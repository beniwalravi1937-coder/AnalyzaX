"""
Billing Domain Engine for AnalyzaX Phase 21.
"""
from typing import Optional

from backend.app.engines.billing.models import (
    BillingAuditLog,
    BillingCustomer,
    BillingInterval,
    BillingOverviewResponse,
    BillingPrice,
    BillingReconciliationReport,
    CancelSubscriptionRequest,
    ChangeSubscriptionRequest,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    CurrencyCode,
    Invoice,
    InvoiceListResponse,
    InvoiceStatus,
    Payment,
    PaymentStatus,
    PortalSessionResponse,
    Subscription,
    SubscriptionStatus,
    WebhookEventRecord,
    WebhookEventStatus,
)
from backend.app.engines.billing.provider import (
    BillingProvider,
    NormalizedWebhookEvent,
    ProviderCheckoutSession,
    ProviderPortalSession,
)
from backend.app.engines.billing.repository import (
    BillingRepository,
    billing_repository,
)
from backend.app.engines.billing.sandbox_provider import SandboxBillingProvider
from backend.app.engines.billing.stripe_provider import StripeBillingProvider


_sandbox_instance: Optional[SandboxBillingProvider] = None


def get_billing_provider() -> BillingProvider:
    """Factory resolver returning active configured billing provider."""
    global _sandbox_instance
    from backend.app.core.config import settings

    provider_name = (getattr(settings, "BILLING_PROVIDER", "") or "sandbox").lower()
    if provider_name == "stripe":
        return StripeBillingProvider()
    if _sandbox_instance is None:
        _sandbox_instance = SandboxBillingProvider()
    return _sandbox_instance


__all__ = [
    "BillingAuditLog",
    "BillingCustomer",
    "BillingInterval",
    "BillingOverviewResponse",
    "BillingPrice",
    "BillingReconciliationReport",
    "CancelSubscriptionRequest",
    "ChangeSubscriptionRequest",
    "CheckoutSessionRequest",
    "CheckoutSessionResponse",
    "CurrencyCode",
    "Invoice",
    "InvoiceListResponse",
    "InvoiceStatus",
    "Payment",
    "PaymentStatus",
    "PortalSessionResponse",
    "Subscription",
    "SubscriptionStatus",
    "WebhookEventRecord",
    "WebhookEventStatus",
    "BillingProvider",
    "NormalizedWebhookEvent",
    "ProviderCheckoutSession",
    "ProviderPortalSession",
    "BillingRepository",
    "billing_repository",
    "SandboxBillingProvider",
    "StripeBillingProvider",
    "get_billing_provider",
]
