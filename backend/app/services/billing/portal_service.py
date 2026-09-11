"""
Billing Portal Service for Phase 21: Billing.
Provisions short-lived hosted self-serve customer billing portal sessions.
Never exposes permanent credentials or generates URLs on the frontend.
"""

from typing import Optional

from backend.app.core.config import settings
from backend.app.engines.billing import get_billing_provider
from backend.app.engines.billing.models import PortalSessionResponse
from backend.app.engines.billing.provider import BillingProvider
from backend.app.engines.billing.repository import BillingRepository, billing_repository
from backend.app.services.billing.customer_service import (
    BillingCustomerService,
    customer_service,
)


class BillingPortalService:
    """Manages short-lived customer portal session generation."""

    def __init__(
        self,
        repo: Optional[BillingRepository] = None,
        cust_svc: Optional[BillingCustomerService] = None,
        provider: Optional[BillingProvider] = None,
    ):
        self._repo = repo or billing_repository
        self._customers = cust_svc or customer_service
        self._provider = provider or get_billing_provider()

    def create_portal_session(
        self,
        workspace_id: str,
        return_url: Optional[str] = None,
    ) -> PortalSessionResponse:
        """
        Creates hosted customer billing portal session:
        1. Verifies workspace has an external billing customer.
        2. Calls provider to generate short-lived signed URL.
        """
        customer = self._customers.get_customer(workspace_id)
        if not customer:
            raise ValueError("No billing customer profile found for this workspace. Subscribe to a plan first.")

        r_url = return_url or settings.BILLING_PORTAL_RETURN_URL
        session = self._provider.create_billing_portal_session(
            external_customer_id=customer.external_customer_id,
            return_url=r_url,
        )

        return PortalSessionResponse(
            portal_url=session.portal_url,
            expires_at=session.expires_at,
        )


# Global portal service instance
portal_service = BillingPortalService()
