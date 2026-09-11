"""
Domain Models for Phase 21: Advanced Billing, Subscriptions, Payments & Revenue Management.
Enforces strict monetary integer minor units, normalized subscription lifecycles,
and provider-independent persistence structures.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field, computed_field, field_validator


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class CurrencyCode(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


class BillingInterval(str, Enum):
    MONTH = "month"
    YEAR = "year"


class SubscriptionStatus(str, Enum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAUSED = "paused"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class WebhookEventStatus(str, Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    IGNORED = "ignored"


# ─────────────────────────────────────────────────────────────
# Domain Entities
# ─────────────────────────────────────────────────────────────

class BillingCustomer(BaseModel):
    """Normalized billing customer representation mapped 1:1 with Workspace."""
    billing_customer_id: str = Field(default_factory=lambda: f"bcust_{uuid.uuid4().hex[:12]}")
    workspace_id: str
    provider: str = "sandbox"
    external_customer_id: str
    email: str
    name: Optional[str] = None
    status: str = "ACTIVE"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BillingPrice(BaseModel):
    """
    Catalog mapping of an internal Product Plan to a commercial billing provider price.
    Uses exact integer minor units (e.g., 2900 minor units = $29.00 USD).
    """
    billing_price_id: str = Field(default_factory=lambda: f"bprice_{uuid.uuid4().hex[:12]}")
    plan_code: str  # e.g., "PRO", "TEAM", "ENTERPRISE"
    provider: str = "sandbox"
    external_price_id: str
    currency: str = "USD"
    amount_minor_units: int  # Must be positive integer
    interval: BillingInterval = BillingInterval.MONTH
    interval_count: int = 1
    active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("amount_minor_units")
    @classmethod
    def validate_amount_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError(f"Price amount cannot be negative, got {v}")
        return v

    @field_validator("plan_code")
    @classmethod
    def normalize_plan_code(cls, v: str) -> str:
        return v.strip().upper()

    @computed_field
    @property
    def amount_display(self) -> str:
        symbol = "$" if self.currency.upper() == "USD" else f"{self.currency} "
        major = self.amount_minor_units / 100.0
        return f"{symbol}{major:.2f}"


class Subscription(BaseModel):
    """
    Normalized internal subscription representation synchronized with the billing provider.
    The external provider is authoritative for payments, AnalyzaX is authoritative for entitlements.
    """
    subscription_id: str = Field(default_factory=lambda: f"sub_{uuid.uuid4().hex[:12]}")
    workspace_id: str
    billing_customer_id: str
    provider: str = "sandbox"
    external_subscription_id: str
    plan_code: str  # e.g. "PRO", "TEAM"
    billing_price_id: str
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    currency: str = "USD"
    current_period_start: str
    current_period_end: str
    cancel_at_period_end: bool = False
    canceled_at: Optional[str] = None
    trial_start: Optional[str] = None
    trial_end: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("plan_code")
    @classmethod
    def normalize_plan_code(cls, v: str) -> str:
        return v.strip().upper()

    @property
    def is_active_entitlement(self) -> bool:
        """Determines if the subscription should grant paid feature access."""
        if self.status == SubscriptionStatus.ACTIVE:
            return True
        if self.status == SubscriptionStatus.TRIALING:
            return True
        # If canceled at period end, remains entitled until period end
        if self.cancel_at_period_end and self.status != SubscriptionStatus.CANCELED:
            try:
                end_dt = datetime.fromisoformat(self.current_period_end.replace("Z", "+00:00"))
                return datetime.now(timezone.utc) <= end_dt
            except Exception:
                return False
        return False


class Invoice(BaseModel):
    """Normalized billing invoice entity with exact minor unit monetary tracking."""
    invoice_id: str = Field(default_factory=lambda: f"inv_{uuid.uuid4().hex[:12]}")
    workspace_id: str
    billing_customer_id: str
    provider: str = "sandbox"
    external_invoice_id: str
    external_subscription_id: Optional[str] = None
    status: InvoiceStatus = InvoiceStatus.PAID
    currency: str = "USD"
    subtotal_minor: int
    tax_minor: Optional[int] = 0
    total_minor: int
    amount_paid_minor: int
    amount_due_minor: int
    period_start: str
    period_end: str
    hosted_invoice_url: Optional[str] = None
    invoice_pdf_url: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @computed_field
    @property
    def total_display(self) -> str:
        symbol = "$" if self.currency.upper() == "USD" else f"{self.currency} "
        major = self.total_minor / 100.0
        return f"{symbol}{major:.2f}"


class Payment(BaseModel):
    """Record of a discrete payment event associated with an invoice."""
    payment_id: str = Field(default_factory=lambda: f"pay_{uuid.uuid4().hex[:12]}")
    workspace_id: str
    billing_customer_id: str
    invoice_id: Optional[str] = None
    provider: str = "sandbox"
    external_payment_id: str
    amount_minor_units: int
    currency: str = "USD"
    status: PaymentStatus = PaymentStatus.SUCCEEDED
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @computed_field
    @property
    def amount_display(self) -> str:
        symbol = "$" if self.currency.upper() == "USD" else f"{self.currency} "
        major = self.amount_minor_units / 100.0
        return f"{symbol}{major:.2f}"


class WebhookEventRecord(BaseModel):
    """Persistent webhook tracking record for idempotency and replay prevention."""
    webhook_event_id: str = Field(default_factory=lambda: f"whevt_{uuid.uuid4().hex[:12]}")
    provider: str = "sandbox"
    external_event_id: str
    event_type: str
    payload_hash: str
    status: WebhookEventStatus = WebhookEventStatus.RECEIVED
    attempt_count: int = 1
    processing_error: Optional[str] = None
    received_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    processed_at: Optional[str] = None


class BillingAuditLog(BaseModel):
    """Audit entry for billing operations."""
    audit_id: str = Field(default_factory=lambda: f"baud_{uuid.uuid4().hex[:12]}")
    workspace_id: str
    event_type: str
    actor_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ─────────────────────────────────────────────────────────────
# Request / Response DTOs
# ─────────────────────────────────────────────────────────────

class CheckoutSessionRequest(BaseModel):
    plan_code: str
    interval: BillingInterval = BillingInterval.MONTH
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutSessionResponse(BaseModel):
    session_id: str
    checkout_url: str
    expires_at: str
    plan_code: str
    interval: str
    amount_minor_units: int
    currency: str
    provider: str


class ChangeSubscriptionRequest(BaseModel):
    new_plan_code: str
    new_interval: Optional[BillingInterval] = None
    proration_behavior: str = "create_prorations"


class CancelSubscriptionRequest(BaseModel):
    cancel_at_period_end: bool = True
    reason: Optional[str] = None


class PortalSessionResponse(BaseModel):
    portal_url: str
    expires_at: str


class BillingOverviewResponse(BaseModel):
    workspace_id: str
    plan_code: str
    customer: Optional[BillingCustomer] = None
    subscription: Optional[Subscription] = None
    prices: List[BillingPrice] = Field(default_factory=list)
    recent_invoices: List[Invoice] = Field(default_factory=list)
    can_manage_billing: bool = True
    is_grace_period: bool = False
    downgrade_warning: Optional[str] = None


class InvoiceListResponse(BaseModel):
    invoices: List[Invoice]
    total: int
    has_more: bool


class BillingReconciliationReport(BaseModel):
    workspace_id: Optional[str] = None
    audited_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_subscriptions_audited: int = 0
    mismatches_found: int = 0
    discrepancies: List[Dict[str, Any]] = Field(default_factory=list)
    is_healthy: bool = True
