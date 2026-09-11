"""
Billing Provider Boundary Abstraction for Phase 20.
Defines clean future interfaces for customer & subscription synchronization
without coupling AnalyzaX to any third-party payment gateways.
External billing processors (Stripe, etc.) are strictly out of scope for Phase 20.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel


class CustomerRecord(BaseModel):
    customer_id: str
    workspace_id: str
    email: str
    name: Optional[str] = None
    provider: str = "internal"
    created_at: str


class SubscriptionRecord(BaseModel):
    subscription_id: str
    workspace_id: str
    plan_code: str
    status: str
    current_period_start: str
    current_period_end: str
    provider: str = "internal"


class BillingProvider(ABC):
    """Abstract contract for future payment & subscription providers."""

    @abstractmethod
    def get_customer(self, workspace_id: str) -> Optional[CustomerRecord]:
        """Retrieves customer record for a workspace."""
        pass

    @abstractmethod
    def create_customer(self, workspace_id: str, email: str, name: Optional[str] = None) -> CustomerRecord:
        """Provisions a billing customer identity."""
        pass

    @abstractmethod
    def get_subscription(self, workspace_id: str) -> Optional[SubscriptionRecord]:
        """Retrieves active subscription."""
        pass

    @abstractmethod
    def change_subscription(self, workspace_id: str, new_plan_code: str) -> SubscriptionRecord:
        """Changes subscription tier."""
        pass


class InternalBillingProvider(BillingProvider):
    """
    Default Phase 20 internal provider.
    Maintains workspace plan assignments without external payment processing.
    """

    def get_customer(self, workspace_id: str) -> Optional[CustomerRecord]:
        return None

    def create_customer(self, workspace_id: str, email: str, name: Optional[str] = None) -> CustomerRecord:
        from datetime import datetime, timezone
        return CustomerRecord(
            customer_id=f"cust_{workspace_id}",
            workspace_id=workspace_id,
            email=email,
            name=name,
            provider="internal",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def get_subscription(self, workspace_id: str) -> Optional[SubscriptionRecord]:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        return SubscriptionRecord(
            subscription_id=f"sub_{workspace_id}",
            workspace_id=workspace_id,
            plan_code="free",
            status="active",
            current_period_start=now,
            current_period_end=now,
            provider="internal",
        )

    def change_subscription(self, workspace_id: str, new_plan_code: str) -> SubscriptionRecord:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        return SubscriptionRecord(
            subscription_id=f"sub_{workspace_id}",
            workspace_id=workspace_id,
            plan_code=new_plan_code,
            status="active",
            current_period_start=now,
            current_period_end=now,
            provider="internal",
        )


# Global provider instance
billing_provider: BillingProvider = InternalBillingProvider()
