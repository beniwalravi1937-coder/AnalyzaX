"""
Checkout Service for Phase 21: Billing.
Creates secure provider-hosted checkout sessions.
Enforces that client CANNOT inject arbitrary price IDs or manipulate pricing.
Paid entitlements are NEVER granted upon checkout creation alone.
"""

import logging
from typing import Optional

from backend.app.engines.billing import get_billing_provider
from backend.app.engines.billing.models import (
    BillingInterval,
    CheckoutSessionResponse,
)
from backend.app.engines.billing.provider import BillingProvider
from backend.app.engines.billing.repository import BillingRepository, billing_repository
from backend.app.services.billing.catalog_service import (
    BillingCatalogService,
    catalog_service,
)
from backend.app.services.billing.customer_service import (
    BillingCustomerService,
    customer_service,
)

logger = logging.getLogger("analyzax.billing.checkout")


class BillingCheckoutService:
    """Manages checkout session initiation and parameter security."""

    def __init__(
        self,
        catalog_svc: Optional[BillingCatalogService] = None,
        cust_svc: Optional[BillingCustomerService] = None,
        repo: Optional[BillingRepository] = None,
        provider: Optional[BillingProvider] = None,
    ):
        self._catalog = catalog_svc or catalog_service
        self._customers = cust_svc or customer_service
        self._repo = repo or billing_repository
        self._provider = provider or get_billing_provider()

    def create_checkout_session(
        self,
        workspace_id: str,
        plan_code: str,
        interval: BillingInterval = BillingInterval.MONTH,
        user_email: str = "user@example.com",
        user_name: Optional[str] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> CheckoutSessionResponse:
        """
        Secure checkout session creation:
        1. Authoritatively resolves Price from Plan + Interval (preventing arbitrary price injection).
        2. Resolves or creates BillingCustomer on payment provider.
        3. Generates hosted checkout URL.
        4. Does NOT activate entitlements (waiting for authoritative webhook / provider confirmation).
        """
        # Validate plan tier & resolve exact authorized price
        self._catalog.validate_plan_tier(plan_code)
        price = self._catalog.resolve_price(plan_code, interval)

        # Resolve billing customer
        customer = self._customers.get_or_create_customer(workspace_id, email=user_email, name=user_name)

        # Default fallback URLs if not provided by client
        s_url = success_url or "http://localhost:3000/settings/billing?session_id={CHECKOUT_SESSION_ID}&status=success"
        c_url = cancel_url or "http://localhost:3000/settings/billing?status=canceled"

        logger.info(
            "Creating checkout session for workspace '%s', customer '%s', plan '%s' ($%.2f)",
            workspace_id,
            customer.external_customer_id,
            price.plan_code,
            price.amount_minor_units / 100.0,
        )

        session = self._provider.create_checkout_session(
            workspace_id=workspace_id,
            customer_id=customer.external_customer_id,
            price=price,
            success_url=s_url,
            cancel_url=c_url,
            metadata={
                "workspace_id": workspace_id,
                "plan_code": price.plan_code,
                "price_id": price.billing_price_id,
                "interval": price.interval.value,
                "actor_id": actor_id or "",
            },
        )

        self._repo.record_audit(
            workspace_id=workspace_id,
            event_type="billing.checkout_session_created",
            actor_id=actor_id,
            details={
                "session_id": session.session_id,
                "plan_code": price.plan_code,
                "interval": price.interval.value,
                "amount_minor_units": price.amount_minor_units,
            },
        )

        return CheckoutSessionResponse(
            session_id=session.session_id,
            checkout_url=session.checkout_url,
            expires_at=session.expires_at,
            plan_code=price.plan_code,
            interval=price.interval.value,
            amount_minor_units=price.amount_minor_units,
            currency=price.currency,
            provider=self._provider.provider_name,
        )


# Global checkout service instance
checkout_service = BillingCheckoutService()
