"""
Customer Service for Phase 21: Billing.
Manages workspace-to-billing-customer mapping (1:1 relationship) and provider customer synchronization.
"""

import logging
from typing import Optional

from backend.app.engines.billing import get_billing_provider
from backend.app.engines.billing.models import BillingCustomer
from backend.app.engines.billing.provider import BillingProvider
from backend.app.engines.billing.repository import BillingRepository, billing_repository

logger = logging.getLogger("analyzax.billing.customer")


class BillingCustomerService:
    """Manages internal and external billing customer identities."""

    def __init__(
        self,
        repo: Optional[BillingRepository] = None,
        provider: Optional[BillingProvider] = None,
    ):
        self._repo = repo or billing_repository
        self._provider = provider or get_billing_provider()

    def get_customer(self, workspace_id: str) -> Optional[BillingCustomer]:
        """Retrieves internal customer record for a workspace."""
        return self._repo.get_customer_by_workspace(workspace_id)

    def get_or_create_customer(
        self,
        workspace_id: str,
        email: str,
        name: Optional[str] = None,
    ) -> BillingCustomer:
        """
        Retrieves existing customer or provisions new customer on payment provider.
        Maintains strict 1:1 workspace to billing customer constraint.
        """
        existing = self._repo.get_customer_by_workspace(workspace_id)
        if existing:
            return existing

        logger.info("Creating external billing customer for workspace '%s' (%s)", workspace_id, email)
        provider_customer = self._provider.create_customer(
            workspace_id=workspace_id,
            email=email,
            name=name,
            metadata={"workspace_id": workspace_id},
        )
        saved = self._repo.save_customer(provider_customer)

        self._repo.record_audit(
            workspace_id=workspace_id,
            event_type="billing.customer_created",
            details={
                "billing_customer_id": saved.billing_customer_id,
                "external_customer_id": saved.external_customer_id,
                "provider": saved.provider,
                "email": saved.email,
            },
        )
        return saved


# Global customer service instance
customer_service = BillingCustomerService()
