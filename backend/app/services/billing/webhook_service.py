"""
Webhook Processing Service for Phase 21: Billing.
Enforces cryptographic signature verification, O(1) deduplication,
transaction safety, out-of-order event convergence, and audit logging.
Never logs raw payment secrets or sensitive credentials.
"""

from datetime import datetime, timezone
import hashlib
import json
import logging
from typing import Any, Dict, Optional, Tuple

from backend.app.engines.billing import get_billing_provider
from backend.app.engines.billing.models import (
    Invoice,
    InvoiceStatus,
    Payment,
    PaymentStatus,
    SubscriptionStatus,
    WebhookEventRecord,
    WebhookEventStatus,
)
from backend.app.engines.billing.provider import BillingProvider, NormalizedWebhookEvent
from backend.app.engines.billing.repository import BillingRepository, billing_repository
from backend.app.engines.notifications.models import (
    ApplicationEventType,
    NotificationCategory,
    NotificationPriority,
)
from backend.app.services.billing.sync_service import BillingSyncService, sync_service
from backend.app.services.notifications.event_dispatcher import (
    EventDispatcher,
    event_dispatcher,
)

logger = logging.getLogger("analyzax.billing.webhook")


class BillingWebhookService:
    """Manages secure, idempotent intake and routing of provider webhooks."""

    def __init__(
        self,
        repo: Optional[BillingRepository] = None,
        provider: Optional[BillingProvider] = None,
        sync_svc: Optional[BillingSyncService] = None,
        dispatcher: Optional[EventDispatcher] = None,
    ):
        self._repo = repo or billing_repository
        self._provider = provider or get_billing_provider()
        self._sync = sync_svc or sync_service
        self._dispatcher = dispatcher or event_dispatcher

    def process_webhook(
        self,
        provider_name: str,
        payload_bytes: bytes,
        headers: Dict[str, str],
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Processes an incoming webhook:
        1. Validates signature.
        2. Checks idempotency cache: ignores duplicate deliveries.
        3. Parses into NormalizedWebhookEvent.
        4. Dispatches state transitions.
        5. Updates event processing status.

        Returns (success: bool, status_message: str, event_id: Optional[str])
        """
        # 1. Signature Verification
        is_valid = self._provider.verify_webhook(payload_bytes, headers)
        if not is_valid:
            logger.warning("Rejected webhook for provider '%s': invalid cryptographic signature", provider_name)
            return False, "invalid_signature", None

        # 2. Extract Event ID & Check Idempotency
        try:
            raw_data = json.loads(payload_bytes.decode("utf-8"))
            ext_event_id = raw_data.get("id") or f"evt_unkn_{hashlib.sha256(payload_bytes).hexdigest()[:12]}"
            event_type = raw_data.get("type", "unknown")
        except Exception as e:
            logger.error("Malformed JSON payload in webhook: %s", e)
            return False, "malformed_json", None

        payload_hash = hashlib.sha256(payload_bytes).hexdigest()

        existing_record = self._repo.get_webhook_event(provider_name, ext_event_id)
        if existing_record and existing_record.status == WebhookEventStatus.PROCESSED:
            self._repo.record_webhook_event(
                provider=provider_name,
                external_event_id=ext_event_id,
                event_type=event_type,
                payload_hash=payload_hash,
                status=WebhookEventStatus.PROCESSED,
            )
            logger.info(
                "Webhook event '%s' from provider '%s' already processed. Idempotently ignoring duplicate delivery.",
                ext_event_id,
                provider_name,
            )
            return True, "duplicate_ignored", ext_event_id

        # Record receipt
        record = self._repo.record_webhook_event(
            provider=provider_name,
            external_event_id=ext_event_id,
            event_type=event_type,
            payload_hash=payload_hash,
            status=WebhookEventStatus.PROCESSING,
        )

        # 3. Parse & Normalize Event
        try:
            normalized = self._provider.parse_webhook_event(payload_bytes, headers)
        except Exception as e:
            logger.error("Failed parsing normalized webhook event '%s': %s", ext_event_id, e)
            self._repo.update_webhook_event_status(
                provider_name, ext_event_id, WebhookEventStatus.FAILED, error=str(e)
            )
            return False, f"parse_error: {str(e)}", ext_event_id

        # 4. Route Normalized Event
        try:
            self._route_event(normalized)
            self._repo.update_webhook_event_status(
                provider_name, ext_event_id, WebhookEventStatus.PROCESSED
            )
            logger.info("Successfully processed webhook event '%s' (%s)", ext_event_id, event_type)
            return True, "processed", ext_event_id
        except Exception as e:
            logger.error("Error processing business logic for webhook '%s': %s", ext_event_id, e, exc_info=True)
            self._repo.update_webhook_event_status(
                provider_name, ext_event_id, WebhookEventStatus.FAILED, error=str(e)
            )
            return False, f"processing_error: {str(e)}", ext_event_id

    def _route_event(self, event: NormalizedWebhookEvent) -> None:
        """Dispatches normalized event to appropriate business handler."""
        event_type = event.event_type.lower()

        if "checkout.session.completed" in event_type or event_type == "checkout_completed":
            self._handle_checkout_completed(event)
        elif "subscription" in event_type and ("created" in event_type or "updated" in event_type):
            self._handle_subscription_updated(event)
        elif "subscription.deleted" in event_type or event_type == "subscription_canceled":
            self._handle_subscription_deleted(event)
        elif "invoice.payment_succeeded" in event_type or event_type == "payment_succeeded":
            self._handle_payment_succeeded(event)
        elif "invoice.payment_failed" in event_type or event_type == "payment_failed":
            self._handle_payment_failed(event)
        elif "invoice.created" in event_type:
            self._handle_invoice_created(event)
        else:
            logger.debug("Unhandled webhook event type: %s", event.event_type)

    def _resolve_workspace_id(self, event: NormalizedWebhookEvent) -> Optional[str]:
        """Resolves workspace ID from event metadata or customer lookup."""
        if event.workspace_id:
            return event.workspace_id
        if event.external_customer_id:
            cust = self._repo.get_customer_by_external_id(event.provider, event.external_customer_id)
            if cust:
                return cust.workspace_id
        if event.external_subscription_id:
            sub = self._repo.get_subscription_by_external_id(event.provider, event.external_subscription_id)
            if sub:
                return sub.workspace_id
        return None

    def _handle_checkout_completed(self, event: NormalizedWebhookEvent) -> None:
        ws_id = self._resolve_workspace_id(event)
        if not ws_id or not event.external_subscription_id:
            logger.warning("Checkout completed event missing workspace_id or subscription_id")
            return

        logger.info("Processing completed checkout for workspace '%s', subscription '%s'", ws_id, event.external_subscription_id)
        self._sync.sync_subscription(
            workspace_id=ws_id,
            external_subscription_id=event.external_subscription_id,
            normalized_event=event,
        )

        # Record invoice & payment if present
        if event.external_invoice_id and event.amount_minor_units:
            now = datetime.now(timezone.utc).isoformat()
            inv = Invoice(
                workspace_id=ws_id,
                billing_customer_id=event.external_customer_id or "",
                provider=event.provider,
                external_invoice_id=event.external_invoice_id,
                external_subscription_id=event.external_subscription_id,
                status=InvoiceStatus.PAID,
                currency=event.currency or "USD",
                subtotal_minor=event.amount_minor_units,
                total_minor=event.amount_minor_units,
                amount_paid_minor=event.amount_minor_units,
                amount_due_minor=0,
                period_start=event.current_period_start or now,
                period_end=event.current_period_end or now,
            )
            self._repo.save_invoice(inv)

            pay = Payment(
                workspace_id=ws_id,
                billing_customer_id=event.external_customer_id or "",
                invoice_id=inv.invoice_id,
                provider=event.provider,
                external_payment_id=f"pay_{event.external_event_id}",
                amount_minor_units=event.amount_minor_units,
                currency=event.currency or "USD",
                status=PaymentStatus.SUCCEEDED,
            )
            self._repo.save_payment(pay)

        self._repo.record_audit(
            workspace_id=ws_id,
            event_type="billing.checkout_completed",
            details={
                "external_subscription_id": event.external_subscription_id,
                "plan_code": event.plan_code,
                "amount_minor_units": event.amount_minor_units,
            },
        )

    def _handle_subscription_updated(self, event: NormalizedWebhookEvent) -> None:
        ws_id = self._resolve_workspace_id(event)
        if not ws_id or not event.external_subscription_id:
            return

        self._sync.sync_subscription(
            workspace_id=ws_id,
            external_subscription_id=event.external_subscription_id,
            normalized_event=event,
        )

    def _handle_subscription_deleted(self, event: NormalizedWebhookEvent) -> None:
        ws_id = self._resolve_workspace_id(event)
        if not ws_id:
            return

        sub = self._repo.get_subscription_by_workspace(ws_id)
        if sub:
            sub.status = SubscriptionStatus.CANCELED
            sub.cancel_at_period_end = False
            sub.canceled_at = datetime.now(timezone.utc).isoformat()
            self._repo.save_subscription(sub)

        # Sync back to FREE tier
        self._sync._apply_subscription_to_workspace_plan(ws_id, sub or Subscription(
            workspace_id=ws_id,
            billing_customer_id="",
            provider=event.provider,
            external_subscription_id=event.external_subscription_id or "",
            plan_code="FREE",
            billing_price_id="",
            status=SubscriptionStatus.CANCELED,
            current_period_start="",
            current_period_end="",
        ))

        self._repo.record_audit(
            workspace_id=ws_id,
            event_type="billing.subscription_canceled",
            details={"external_subscription_id": event.external_subscription_id},
        )

    def _handle_payment_succeeded(self, event: NormalizedWebhookEvent) -> None:
        ws_id = self._resolve_workspace_id(event)
        if not ws_id:
            return

        now = datetime.now(timezone.utc).isoformat()
        inv_id = event.external_invoice_id or f"inv_ext_{event.external_event_id}"
        amount = event.amount_minor_units or 0

        # Save invoice record
        invoice = Invoice(
            workspace_id=ws_id,
            billing_customer_id=event.external_customer_id or "",
            provider=event.provider,
            external_invoice_id=inv_id,
            external_subscription_id=event.external_subscription_id,
            status=InvoiceStatus.PAID,
            currency=event.currency or "USD",
            subtotal_minor=amount,
            total_minor=amount,
            amount_paid_minor=amount,
            amount_due_minor=0,
            period_start=event.current_period_start or now,
            period_end=event.current_period_end or now,
        )
        self._repo.save_invoice(invoice)

        # Save payment record
        payment = Payment(
            workspace_id=ws_id,
            billing_customer_id=event.external_customer_id or "",
            invoice_id=invoice.invoice_id,
            provider=event.provider,
            external_payment_id=f"pay_{event.external_event_id}",
            amount_minor_units=amount,
            currency=event.currency or "USD",
            status=PaymentStatus.SUCCEEDED,
        )
        self._repo.save_payment(payment)

        # Dispatch notification
        major_str = f"{(amount / 100.0):.2f}"
        try:
            self._dispatcher.create_and_dispatch(
                event_type=ApplicationEventType.PAYMENT_SUCCEEDED,
                workspace_id=ws_id,
                metadata={"amount": major_str, "currency": invoice.currency},
            )
        except Exception as e:
            logger.warning("Failed to dispatch payment succeeded notification: %s", e)

    def _handle_payment_failed(self, event: NormalizedWebhookEvent) -> None:
        ws_id = self._resolve_workspace_id(event)
        if not ws_id:
            return

        amount = event.amount_minor_units or 0
        major_str = f"{(amount / 100.0):.2f}"
        reason = event.failure_reason or "Card was declined"

        # Update subscription status to PAST_DUE if active
        sub = self._repo.get_subscription_by_workspace(ws_id)
        if sub:
            sub.status = SubscriptionStatus.PAST_DUE
            self._repo.save_subscription(sub)

        # Record failed payment
        payment = Payment(
            workspace_id=ws_id,
            billing_customer_id=event.external_customer_id or "",
            provider=event.provider,
            external_payment_id=f"pay_fail_{event.external_event_id}",
            amount_minor_units=amount,
            currency=event.currency or "USD",
            status=PaymentStatus.FAILED,
        )
        self._repo.save_payment(payment)

        # Dispatch urgent notification
        try:
            self._dispatcher.create_and_dispatch(
                event_type=ApplicationEventType.PAYMENT_FAILED,
                workspace_id=ws_id,
                metadata={"amount": major_str, "currency": event.currency or "USD", "reason": reason},
            )
        except Exception as e:
            logger.warning("Failed to dispatch payment failed notification: %s", e)

    def _handle_invoice_created(self, event: NormalizedWebhookEvent) -> None:
        ws_id = self._resolve_workspace_id(event)
        if not ws_id or not event.external_invoice_id:
            return

        now = datetime.now(timezone.utc).isoformat()
        amount = event.amount_minor_units or 0
        invoice = Invoice(
            workspace_id=ws_id,
            billing_customer_id=event.external_customer_id or "",
            provider=event.provider,
            external_invoice_id=event.external_invoice_id,
            external_subscription_id=event.external_subscription_id,
            status=InvoiceStatus.OPEN,
            currency=event.currency or "USD",
            subtotal_minor=amount,
            total_minor=amount,
            amount_paid_minor=0,
            amount_due_minor=amount,
            period_start=event.current_period_start or now,
            period_end=event.current_period_end or now,
        )
        self._repo.save_invoice(invoice)


# Global webhook service instance
webhook_service = BillingWebhookService()
