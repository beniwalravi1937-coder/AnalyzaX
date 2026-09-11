"""
Deterministic Sandbox / Test Billing Provider for Phase 21.
Implements the full BillingProvider interface with realistic stateful simulation,
HMAC-SHA256 signature verification, and zero third-party dependencies.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import time
from typing import Any, Dict, List, Optional
import uuid

from backend.app.core.config import settings
from backend.app.engines.billing.models import (
    BillingCustomer,
    BillingPrice,
    Invoice,
    InvoiceStatus,
    Subscription,
    SubscriptionStatus,
)
from backend.app.engines.billing.provider import (
    BillingProvider,
    NormalizedWebhookEvent,
    ProviderCheckoutSession,
    ProviderPortalSession,
)


class SandboxBillingProvider(BillingProvider):
    """
    In-memory / stateful test provider simulating Stripe-like behavior.
    Thread-safe and deterministic for unit, integration, and E2E testing.
    """

    def __init__(self, webhook_secret: Optional[str] = None):
        self._webhook_secret = webhook_secret or settings.BILLING_WEBHOOK_SECRET
        self._customers: Dict[str, BillingCustomer] = {}  # external_id -> customer
        self._subscriptions: Dict[str, Subscription] = {}  # external_id -> subscription
        self._invoices: Dict[str, Invoice] = {}  # external_id -> invoice
        self._sessions: Dict[str, Dict[str, Any]] = {}  # session_id -> session_info

    @property
    def provider_name(self) -> str:
        return "sandbox"

    def create_customer(
        self,
        workspace_id: str,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BillingCustomer:
        ext_id = f"cus_sbx_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        customer = BillingCustomer(
            workspace_id=workspace_id,
            provider=self.provider_name,
            external_customer_id=ext_id,
            email=email,
            name=name,
            status="ACTIVE",
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )
        self._customers[ext_id] = customer
        return customer

    def get_customer(self, external_customer_id: str) -> Optional[BillingCustomer]:
        return self._customers.get(external_customer_id)

    def update_customer(
        self,
        external_customer_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BillingCustomer:
        customer = self._customers.get(external_customer_id)
        if not customer:
            raise ValueError(f"Customer {external_customer_id} not found")
        if email:
            customer.email = email
        if name:
            customer.name = name
        if metadata:
            customer.metadata.update(metadata)
        customer.updated_at = datetime.now(timezone.utc).isoformat()
        self._customers[external_customer_id] = customer
        return customer

    def create_checkout_session(
        self,
        workspace_id: str,
        customer_id: str,
        price: BillingPrice,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProviderCheckoutSession:
        session_id = f"cs_sbx_{uuid.uuid4().hex[:16]}"
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        session_info = {
            "session_id": session_id,
            "workspace_id": workspace_id,
            "external_customer_id": customer_id,
            "price": price.model_dump(),
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": metadata or {},
            "status": "open",
            "expires_at": expires_at,
        }
        self._sessions[session_id] = session_info

        checkout_url = f"http://localhost:3000/checkout/sandbox/{session_id}"
        return ProviderCheckoutSession(
            session_id=session_id,
            checkout_url=checkout_url,
            expires_at=expires_at,
            external_customer_id=customer_id,
            metadata=metadata or {},
        )

    def get_subscription(self, external_subscription_id: str) -> Optional[Subscription]:
        return self._subscriptions.get(external_subscription_id)

    def change_subscription(
        self,
        external_subscription_id: str,
        new_price: BillingPrice,
        proration_behavior: str = "create_prorations",
    ) -> Subscription:
        sub = self._subscriptions.get(external_subscription_id)
        if not sub:
            raise ValueError(f"Subscription {external_subscription_id} not found")
        sub.plan_code = new_price.plan_code
        sub.billing_price_id = new_price.billing_price_id
        sub.currency = new_price.currency
        sub.cancel_at_period_end = False
        sub.status = SubscriptionStatus.ACTIVE
        sub.updated_at = datetime.now(timezone.utc).isoformat()
        self._subscriptions[external_subscription_id] = sub
        return sub

    def cancel_subscription(
        self,
        external_subscription_id: str,
        cancel_at_period_end: bool = True,
        reason: Optional[str] = None,
    ) -> Subscription:
        sub = self._subscriptions.get(external_subscription_id)
        if not sub:
            raise ValueError(f"Subscription {external_subscription_id} not found")
        now = datetime.now(timezone.utc).isoformat()
        if cancel_at_period_end:
            sub.cancel_at_period_end = True
        else:
            sub.status = SubscriptionStatus.CANCELED
            sub.cancel_at_period_end = False
        sub.canceled_at = now
        sub.updated_at = now
        if reason:
            sub.metadata["cancellation_reason"] = reason
        self._subscriptions[external_subscription_id] = sub
        return sub

    def resume_subscription(self, external_subscription_id: str) -> Subscription:
        sub = self._subscriptions.get(external_subscription_id)
        if not sub:
            raise ValueError(f"Subscription {external_subscription_id} not found")
        sub.cancel_at_period_end = False
        sub.status = SubscriptionStatus.ACTIVE
        sub.canceled_at = None
        sub.updated_at = datetime.now(timezone.utc).isoformat()
        self._subscriptions[external_subscription_id] = sub
        return sub

    def get_invoice(self, external_invoice_id: str) -> Optional[Invoice]:
        return self._invoices.get(external_invoice_id)

    def list_invoices(
        self,
        external_customer_id: str,
        limit: int = 20,
        starting_after: Optional[str] = None,
    ) -> List[Invoice]:
        matched = [
            inv for inv in self._invoices.values()
            if inv.billing_customer_id == external_customer_id or inv.provider == self.provider_name
        ]
        matched.sort(key=lambda x: x.created_at, reverse=True)
        return matched[:limit]

    def create_billing_portal_session(
        self,
        external_customer_id: str,
        return_url: str,
    ) -> ProviderPortalSession:
        session_id = f"pts_sbx_{uuid.uuid4().hex[:16]}"
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
        return ProviderPortalSession(
            session_id=session_id,
            portal_url=f"http://localhost:3000/settings/billing?portal_session={session_id}",
            expires_at=expires_at,
        )

    # ─────────────────────────────────────────────────────────────
    # Webhook Utilities & Cryptographic Signatures
    # ─────────────────────────────────────────────────────────────

    def generate_signature(self, payload_bytes: bytes, timestamp: Optional[int] = None) -> str:
        """Generates standard Stripe-style webhook signature header: t=timestamp,v1=hash."""
        ts = timestamp or int(time.time())
        signed_payload = f"{ts}.".encode("utf-8") + payload_bytes
        mac = hmac.new(self._webhook_secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
        return f"t={ts},v1={mac}"

    def verify_webhook(self, payload_bytes: bytes, headers: Dict[str, str]) -> bool:
        """Verifies webhook signature using HMAC-SHA256 and checks timestamp tolerance (5 mins)."""
        sig_header = headers.get("stripe-signature") or headers.get("x-webhook-signature")
        if not sig_header:
            return False

        try:
            parts = dict(pair.split("=", 1) for pair in sig_header.split(",") if "=" in pair)
            if "t" not in parts or "v1" not in parts:
                return False

            timestamp = int(parts["t"])
            # Verify timestamp freshness within 300 seconds
            if abs(time.time() - timestamp) > 300:
                return False

            expected_sig = parts["v1"]
            signed_payload = f"{timestamp}.".encode("utf-8") + payload_bytes
            computed_sig = hmac.new(
                self._webhook_secret.encode("utf-8"), signed_payload, hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(computed_sig, expected_sig)
        except Exception:
            return False

    def parse_webhook_event(
        self, payload_bytes: bytes, headers: Dict[str, str]
    ) -> NormalizedWebhookEvent:
        """Parses webhook JSON and normalizes into NormalizedWebhookEvent."""
        data = json.loads(payload_bytes.decode("utf-8"))

        event_id = data.get("id") or f"evt_sbx_{uuid.uuid4().hex[:12]}"
        event_type = data.get("type", "UNKNOWN")
        obj = data.get("data", {}).get("object", {})

        return NormalizedWebhookEvent(
            provider=self.provider_name,
            external_event_id=event_id,
            event_type=event_type,
            occurred_at=datetime.fromtimestamp(data.get("created", time.time()), timezone.utc).isoformat(),
            workspace_id=obj.get("metadata", {}).get("workspace_id") or data.get("workspace_id"),
            external_customer_id=obj.get("customer"),
            external_subscription_id=obj.get("subscription") or (obj.get("id") if "sub_" in str(obj.get("id", "")) else None),
            external_invoice_id=obj.get("invoice") or (obj.get("id") if "inv_" in str(obj.get("id", "")) else None),
            external_price_id=obj.get("plan", {}).get("id") or obj.get("price", {}).get("id"),
            plan_code=obj.get("metadata", {}).get("plan_code"),
            status=obj.get("status"),
            current_period_start=datetime.fromtimestamp(obj["current_period_start"], timezone.utc).isoformat() if "current_period_start" in obj else None,
            current_period_end=datetime.fromtimestamp(obj["current_period_end"], timezone.utc).isoformat() if "current_period_end" in obj else None,
            cancel_at_period_end=obj.get("cancel_at_period_end"),
            amount_minor_units=obj.get("amount_total") or obj.get("amount_paid") or obj.get("amount"),
            currency=obj.get("currency", "usd").upper(),
            failure_reason=obj.get("failure_message") or obj.get("last_payment_error", {}).get("message"),
            raw_payload=data,
        )

    # ─────────────────────────────────────────────────────────────
    # Test Helpers for Webhook Simulation
    # ─────────────────────────────────────────────────────────────

    def simulate_checkout_completed(
        self,
        session_id: str,
        workspace_id: str,
        customer_id: str,
        plan_code: str,
        price_id: str,
        amount_minor: int,
        interval: str = "month",
    ) -> Dict[str, Any]:
        """Generates realistic checkout.session.completed event payload."""
        sub_id = f"sub_sbx_{uuid.uuid4().hex[:12]}"
        inv_id = f"inv_sbx_{uuid.uuid4().hex[:12]}"
        now_ts = int(time.time())
        period_end_ts = now_ts + (365 * 86400 if interval == "year" else 30 * 86400)

        # Register simulated subscription
        sub = Subscription(
            workspace_id=workspace_id,
            billing_customer_id=customer_id,
            provider=self.provider_name,
            external_subscription_id=sub_id,
            plan_code=plan_code.upper(),
            billing_price_id=price_id,
            status=SubscriptionStatus.ACTIVE,
            currency="USD",
            current_period_start=datetime.fromtimestamp(now_ts, timezone.utc).isoformat(),
            current_period_end=datetime.fromtimestamp(period_end_ts, timezone.utc).isoformat(),
        )
        self._subscriptions[sub_id] = sub

        # Register simulated invoice
        inv = Invoice(
            workspace_id=workspace_id,
            billing_customer_id=customer_id,
            provider=self.provider_name,
            external_invoice_id=inv_id,
            external_subscription_id=sub_id,
            status=InvoiceStatus.PAID,
            currency="USD",
            subtotal_minor=amount_minor,
            total_minor=amount_minor,
            amount_paid_minor=amount_minor,
            amount_due_minor=0,
            period_start=sub.current_period_start,
            period_end=sub.current_period_end,
            hosted_invoice_url=f"http://localhost:3000/invoices/{inv_id}",
        )
        self._invoices[inv_id] = inv

        return {
            "id": f"evt_sbx_{uuid.uuid4().hex[:14]}",
            "type": "checkout.session.completed",
            "created": now_ts,
            "data": {
                "object": {
                    "id": session_id,
                    "customer": customer_id,
                    "subscription": sub_id,
                    "invoice": inv_id,
                    "amount_total": amount_minor,
                    "currency": "usd",
                    "status": "complete",
                    "metadata": {
                        "workspace_id": workspace_id,
                        "plan_code": plan_code.upper(),
                        "price_id": price_id,
                    },
                }
            },
        }
