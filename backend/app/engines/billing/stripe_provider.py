"""
Production Stripe Billing Provider Adapter for Phase 21.
Implements the exact same BillingProvider interface using Stripe API primitives.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional

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

logger = logging.getLogger("analyzax.billing.stripe")


class StripeBillingProvider(BillingProvider):
    """
    Production Stripe implementation of BillingProvider.
    Requires stripe python SDK and valid BILLING_SECRET_KEY.
    """

    def __init__(self, api_key: Optional[str] = None, webhook_secret: Optional[str] = None):
        self._api_key = api_key or settings.BILLING_SECRET_KEY
        self._webhook_secret = webhook_secret or settings.BILLING_WEBHOOK_SECRET

    @property
    def provider_name(self) -> str:
        return "stripe"

    def _ensure_configured(self):
        if not self._api_key:
            raise RuntimeError(
                "Stripe API key not configured. Set BILLING_SECRET_KEY or use BILLING_PROVIDER='sandbox'"
            )

    def create_customer(
        self,
        workspace_id: str,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BillingCustomer:
        self._ensure_configured()
        import stripe
        stripe.api_key = self._api_key

        meta = metadata or {}
        meta["workspace_id"] = workspace_id

        cus = stripe.Customer.create(
            email=email,
            name=name,
            metadata=meta,
        )
        now = datetime.now(timezone.utc).isoformat()
        return BillingCustomer(
            workspace_id=workspace_id,
            provider="stripe",
            external_customer_id=cus["id"],
            email=cus.get("email", email),
            name=cus.get("name", name),
            metadata=dict(cus.get("metadata", {})),
            created_at=now,
            updated_at=now,
        )

    def get_customer(self, external_customer_id: str) -> Optional[BillingCustomer]:
        self._ensure_configured()
        import stripe
        stripe.api_key = self._api_key
        try:
            cus = stripe.Customer.retrieve(external_customer_id)
            if getattr(cus, "deleted", False):
                return None
            return BillingCustomer(
                workspace_id=cus.get("metadata", {}).get("workspace_id", ""),
                provider="stripe",
                external_customer_id=cus["id"],
                email=cus.get("email", ""),
                name=cus.get("name"),
                metadata=dict(cus.get("metadata", {})),
            )
        except Exception as e:
            logger.warning("Error fetching Stripe customer %s: %s", external_customer_id, e)
            return None

    def update_customer(
        self,
        external_customer_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BillingCustomer:
        self._ensure_configured()
        import stripe
        stripe.api_key = self._api_key
        params: Dict[str, Any] = {}
        if email:
            params["email"] = email
        if name:
            params["name"] = name
        if metadata:
            params["metadata"] = metadata

        cus = stripe.Customer.modify(external_customer_id, **params)
        return BillingCustomer(
            workspace_id=cus.get("metadata", {}).get("workspace_id", ""),
            provider="stripe",
            external_customer_id=cus["id"],
            email=cus.get("email", ""),
            name=cus.get("name"),
            metadata=dict(cus.get("metadata", {})),
        )

    def create_checkout_session(
        self,
        workspace_id: str,
        customer_id: str,
        price: BillingPrice,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProviderCheckoutSession:
        self._ensure_configured()
        import stripe
        stripe.api_key = self._api_key

        meta = metadata or {}
        meta["workspace_id"] = workspace_id
        meta["plan_code"] = price.plan_code

        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": price.external_price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=meta,
            subscription_data={"metadata": meta},
        )
        return ProviderCheckoutSession(
            session_id=session["id"],
            checkout_url=session["url"],
            expires_at=datetime.fromtimestamp(session["expires_at"], timezone.utc).isoformat(),
            external_customer_id=customer_id,
            metadata=meta,
        )

    def get_subscription(self, external_subscription_id: str) -> Optional[Subscription]:
        self._ensure_configured()
        import stripe
        stripe.api_key = self._api_key
        try:
            sub = stripe.Subscription.retrieve(external_subscription_id)
            return self._normalize_stripe_subscription(sub)
        except Exception as e:
            logger.warning("Error fetching Stripe subscription %s: %s", external_subscription_id, e)
            return None

    def change_subscription(
        self,
        external_subscription_id: str,
        new_price: BillingPrice,
        proration_behavior: str = "create_prorations",
    ) -> Subscription:
        self._ensure_configured()
        import stripe
        stripe.api_key = self._api_key

        sub = stripe.Subscription.retrieve(external_subscription_id)
        item_id = sub["items"]["data"][0]["id"]

        updated = stripe.Subscription.modify(
            external_subscription_id,
            items=[{"id": item_id, "price": new_price.external_price_id}],
            proration_behavior=proration_behavior,
            metadata={"plan_code": new_price.plan_code},
        )
        return self._normalize_stripe_subscription(updated)

    def cancel_subscription(
        self,
        external_subscription_id: str,
        cancel_at_period_end: bool = True,
        reason: Optional[str] = None,
    ) -> Subscription:
        self._ensure_configured()
        import stripe
        stripe.api_key = self._api_key

        if cancel_at_period_end:
            sub = stripe.Subscription.modify(
                external_subscription_id,
                cancel_at_period_end=True,
                metadata={"cancellation_reason": reason or ""},
            )
        else:
            sub = stripe.Subscription.cancel(
                external_subscription_id,
                cancellation_details={"comment": reason or "Immediate cancellation"},
            )
        return self._normalize_stripe_subscription(sub)

    def resume_subscription(self, external_subscription_id: str) -> Subscription:
        self._ensure_configured()
        import stripe
        stripe.api_key = self._api_key
        sub = stripe.Subscription.modify(external_subscription_id, cancel_at_period_end=False)
        return self._normalize_stripe_subscription(sub)

    def get_invoice(self, external_invoice_id: str) -> Optional[Invoice]:
        self._ensure_configured()
        import stripe
        stripe.api_key = self._api_key
        try:
            inv = stripe.Invoice.retrieve(external_invoice_id)
            return self._normalize_stripe_invoice(inv)
        except Exception as e:
            logger.warning("Error fetching Stripe invoice %s: %s", external_invoice_id, e)
            return None

    def list_invoices(
        self,
        external_customer_id: str,
        limit: int = 20,
        starting_after: Optional[str] = None,
    ) -> List[Invoice]:
        self._ensure_configured()
        import stripe
        stripe.api_key = self._api_key
        params: Dict[str, Any] = {"customer": external_customer_id, "limit": limit}
        if starting_after:
            params["starting_after"] = starting_after

        res = stripe.Invoice.list(**params)
        return [self._normalize_stripe_invoice(i) for i in res.get("data", [])]

    def create_billing_portal_session(
        self,
        external_customer_id: str,
        return_url: str,
    ) -> ProviderPortalSession:
        self._ensure_configured()
        import stripe
        stripe.api_key = self._api_key
        session = stripe.billing_portal.Session.create(
            customer=external_customer_id,
            return_url=return_url,
        )
        return ProviderPortalSession(
            session_id=session["id"],
            portal_url=session["url"],
            expires_at=datetime.fromtimestamp(session["created"] + 1800, timezone.utc).isoformat(),
        )

    def verify_webhook(self, payload_bytes: bytes, headers: Dict[str, str]) -> bool:
        if not self._webhook_secret:
            return False
        import stripe
        sig_header = headers.get("stripe-signature")
        if not sig_header:
            return False
        try:
            stripe.Webhook.construct_event(payload_bytes, sig_header, self._webhook_secret)
            return True
        except Exception:
            return False

    def parse_webhook_event(
        self, payload_bytes: bytes, headers: Dict[str, str]
    ) -> NormalizedWebhookEvent:
        data = json.loads(payload_bytes.decode("utf-8"))
        obj = data.get("data", {}).get("object", {})

        return NormalizedWebhookEvent(
            provider="stripe",
            external_event_id=data["id"],
            event_type=data["type"],
            occurred_at=datetime.fromtimestamp(data.get("created", 0), timezone.utc).isoformat(),
            workspace_id=obj.get("metadata", {}).get("workspace_id"),
            external_customer_id=obj.get("customer"),
            external_subscription_id=obj.get("subscription") or (obj["id"] if obj.get("object") == "subscription" else None),
            external_invoice_id=obj.get("invoice") or (obj["id"] if obj.get("object") == "invoice" else None),
            external_price_id=obj.get("plan", {}).get("id") or (obj.get("items", {}).get("data", [{}])[0].get("price", {}).get("id") if "items" in obj else None),
            plan_code=obj.get("metadata", {}).get("plan_code"),
            status=obj.get("status"),
            current_period_start=datetime.fromtimestamp(obj["current_period_start"], timezone.utc).isoformat() if "current_period_start" in obj else None,
            current_period_end=datetime.fromtimestamp(obj["current_period_end"], timezone.utc).isoformat() if "current_period_end" in obj else None,
            cancel_at_period_end=obj.get("cancel_at_period_end"),
            amount_minor_units=obj.get("amount_total") or obj.get("amount_paid"),
            currency=obj.get("currency", "usd").upper(),
            raw_payload=data,
        )

    def _normalize_stripe_subscription(self, sub: Any) -> Subscription:
        status_map = {
            "trialing": SubscriptionStatus.TRIALING,
            "active": SubscriptionStatus.ACTIVE,
            "past_due": SubscriptionStatus.PAST_DUE,
            "unpaid": SubscriptionStatus.UNPAID,
            "canceled": SubscriptionStatus.CANCELED,
            "incomplete": SubscriptionStatus.INCOMPLETE,
            "incomplete_expired": SubscriptionStatus.INCOMPLETE_EXPIRED,
            "paused": SubscriptionStatus.PAUSED,
        }
        status = status_map.get(sub.get("status", ""), SubscriptionStatus.ACTIVE)
        plan_code = sub.get("metadata", {}).get("plan_code") or "PRO"

        return Subscription(
            workspace_id=sub.get("metadata", {}).get("workspace_id", ""),
            billing_customer_id=sub.get("customer", ""),
            provider="stripe",
            external_subscription_id=sub["id"],
            plan_code=plan_code,
            billing_price_id=sub["items"]["data"][0]["price"]["id"] if sub.get("items", {}).get("data") else "",
            status=status,
            currency=sub.get("currency", "usd").upper(),
            current_period_start=datetime.fromtimestamp(sub["current_period_start"], timezone.utc).isoformat(),
            current_period_end=datetime.fromtimestamp(sub["current_period_end"], timezone.utc).isoformat(),
            cancel_at_period_end=sub.get("cancel_at_period_end", False),
            metadata=dict(sub.get("metadata", {})),
        )

    def _normalize_stripe_invoice(self, inv: Any) -> Invoice:
        status_map = {
            "draft": InvoiceStatus.DRAFT,
            "open": InvoiceStatus.OPEN,
            "paid": InvoiceStatus.PAID,
            "void": InvoiceStatus.VOID,
            "uncollectible": InvoiceStatus.UNCOLLECTIBLE,
        }
        return Invoice(
            workspace_id=inv.get("metadata", {}).get("workspace_id", ""),
            billing_customer_id=inv.get("customer", ""),
            provider="stripe",
            external_invoice_id=inv["id"],
            external_subscription_id=inv.get("subscription"),
            status=status_map.get(inv.get("status", ""), InvoiceStatus.PAID),
            currency=inv.get("currency", "usd").upper(),
            subtotal_minor=inv.get("subtotal", 0),
            tax_minor=inv.get("tax", 0),
            total_minor=inv.get("total", 0),
            amount_paid_minor=inv.get("amount_paid", 0),
            amount_due_minor=inv.get("amount_due", 0),
            period_start=datetime.fromtimestamp(inv.get("period_start", 0), timezone.utc).isoformat(),
            period_end=datetime.fromtimestamp(inv.get("period_end", 0), timezone.utc).isoformat(),
            hosted_invoice_url=inv.get("hosted_invoice_url"),
            invoice_pdf_url=inv.get("invoice_pdf"),
        )
