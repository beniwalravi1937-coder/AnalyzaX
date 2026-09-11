"""
Billing Provider Abstraction Interface for Phase 21.
Isolates external payment processor mechanics (Stripe, Sandbox, etc.) from AnalyzaX core domain.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.engines.billing.models import (
    BillingCustomer,
    BillingPrice,
    Invoice,
    Subscription,
)


class NormalizedWebhookEvent(BaseModel):
    """
    Provider-agnostic event model representing external billing state transitions.
    Normalized from provider-specific webhook payloads.
    """
    provider: str
    external_event_id: str
    event_type: str  # e.g. "CHECKOUT_COMPLETED", "SUBSCRIPTION_UPDATED", "PAYMENT_SUCCEEDED", "PAYMENT_FAILED"
    occurred_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    workspace_id: Optional[str] = None
    external_customer_id: Optional[str] = None
    external_subscription_id: Optional[str] = None
    external_invoice_id: Optional[str] = None
    external_price_id: Optional[str] = None
    plan_code: Optional[str] = None
    status: Optional[str] = None
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: Optional[bool] = None
    amount_minor_units: Optional[int] = None
    currency: Optional[str] = None
    failure_reason: Optional[str] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict)


class ProviderCheckoutSession(BaseModel):
    session_id: str
    checkout_url: str
    expires_at: str
    external_customer_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProviderPortalSession(BaseModel):
    session_id: str
    portal_url: str
    expires_at: str


class BillingProvider(ABC):
    """
    Abstract contract for payment & subscription providers.
    All external processors must implement these normalized primitives.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the billing provider (e.g. 'sandbox', 'stripe')."""
        pass

    @abstractmethod
    def create_customer(
        self,
        workspace_id: str,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BillingCustomer:
        """Provisions a customer identity on the payment provider."""
        pass

    @abstractmethod
    def get_customer(self, external_customer_id: str) -> Optional[BillingCustomer]:
        """Retrieves a customer by provider external ID."""
        pass

    @abstractmethod
    def update_customer(
        self,
        external_customer_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BillingCustomer:
        """Updates customer details on the payment provider."""
        pass

    @abstractmethod
    def create_checkout_session(
        self,
        workspace_id: str,
        customer_id: str,
        price: BillingPrice,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProviderCheckoutSession:
        """Creates a hosted checkout session."""
        pass

    @abstractmethod
    def get_subscription(self, external_subscription_id: str) -> Optional[Subscription]:
        """Fetches authoritative subscription state from provider."""
        pass

    @abstractmethod
    def change_subscription(
        self,
        external_subscription_id: str,
        new_price: BillingPrice,
        proration_behavior: str = "create_prorations",
    ) -> Subscription:
        """Upgrades or downgrades subscription tier on provider."""
        pass

    @abstractmethod
    def cancel_subscription(
        self,
        external_subscription_id: str,
        cancel_at_period_end: bool = True,
        reason: Optional[str] = None,
    ) -> Subscription:
        """Cancels subscription (either at period end or immediately)."""
        pass

    @abstractmethod
    def resume_subscription(self, external_subscription_id: str) -> Subscription:
        """Resumes a subscription that was set to cancel at period end."""
        pass

    @abstractmethod
    def get_invoice(self, external_invoice_id: str) -> Optional[Invoice]:
        """Retrieves invoice by external provider ID."""
        pass

    @abstractmethod
    def list_invoices(
        self,
        external_customer_id: str,
        limit: int = 20,
        starting_after: Optional[str] = None,
    ) -> List[Invoice]:
        """Lists historical invoices for a customer."""
        pass

    @abstractmethod
    def create_billing_portal_session(
        self,
        external_customer_id: str,
        return_url: str,
    ) -> ProviderPortalSession:
        """Creates a short-lived hosted billing portal session."""
        pass

    @abstractmethod
    def verify_webhook(self, payload_bytes: bytes, headers: Dict[str, str]) -> bool:
        """Cryptographically verifies webhook signature."""
        pass

    @abstractmethod
    def parse_webhook_event(
        self, payload_bytes: bytes, headers: Dict[str, str]
    ) -> NormalizedWebhookEvent:
        """Parses and normalizes provider webhook payload."""
        pass
