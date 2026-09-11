"""
Catalog Service for Phase 21: Billing & Pricing.
Resolves commercial pricing from internal plan codes and intervals.
Strictly prevents arbitrary client-side price ID or amount injection.
"""

from typing import List, Optional

from backend.app.engines.billing.models import BillingInterval, BillingPrice
from backend.app.engines.billing.repository import BillingRepository, billing_repository
from backend.app.engines.usage.models import PlanTier


class BillingCatalogService:
    """Manages commercial price catalog and price validation."""

    def __init__(self, repo: Optional[BillingRepository] = None):
        self._repo = repo or billing_repository

    def list_prices(self, active_only: bool = True) -> List[BillingPrice]:
        """Returns all configured prices."""
        return self._repo.get_all_prices(active_only=active_only)

    def get_price_by_id(self, price_id: str) -> Optional[BillingPrice]:
        """Retrieves price by internal ID."""
        return self._repo.get_price_by_id(price_id)

    def get_price_by_external_id(self, external_price_id: str) -> Optional[BillingPrice]:
        """Retrieves price by external provider price ID."""
        return self._repo.get_price_by_external_id(external_price_id)

    def resolve_price(
        self,
        plan_code: str,
        interval: BillingInterval = BillingInterval.MONTH,
    ) -> BillingPrice:
        """
        Authoritatively resolves the active price for a plan code and billing interval.
        Raises ValueError if no matching active price exists.
        """
        code = plan_code.upper().strip()
        price = self._repo.get_price_by_plan_and_interval(code, interval)
        if not price or not price.active:
            raise ValueError(f"No active billing price found for plan '{code}' with interval '{interval.value}'")
        return price

    def validate_plan_tier(self, plan_code: str) -> str:
        """Validates that plan code maps to a supported commercial paid tier."""
        code = plan_code.upper().strip()
        valid_paid_tiers = {PlanTier.PRO.value, PlanTier.TEAM.value, PlanTier.ENTERPRISE.value}
        if code not in valid_paid_tiers:
            raise ValueError(f"Plan '{code}' is not an upgradeable commercial tier")
        return code


# Global catalog service instance
catalog_service = BillingCatalogService()
