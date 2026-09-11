"""
Billing Reconciliation Service for Phase 21: Billing.
Audits internal subscriptions against authoritative provider states to detect discrepancies.
Never silently modifies state; provides explicit administrative diagnostics.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

from backend.app.engines.billing import get_billing_provider
from backend.app.engines.billing.models import (
    BillingReconciliationReport,
    Subscription,
)
from backend.app.engines.billing.provider import BillingProvider
from backend.app.engines.billing.repository import BillingRepository, billing_repository

logger = logging.getLogger("analyzax.billing.reconciliation")


class BillingReconciliationService:
    """Audits consistency between internal ledger and payment gateway."""

    def __init__(
        self,
        repo: Optional[BillingRepository] = None,
        provider: Optional[BillingProvider] = None,
    ):
        self._repo = repo or billing_repository
        self._provider = provider or get_billing_provider()

    def reconcile_workspace(self, workspace_id: str) -> BillingReconciliationReport:
        """Audits subscription state for a single workspace."""
        sub = self._repo.get_subscription_by_workspace(workspace_id)
        subs = [sub] if sub else []
        return self._reconcile_subscriptions(subs, workspace_id=workspace_id)

    def reconcile_all(self) -> BillingReconciliationReport:
        """Audits all internal subscriptions against provider."""
        all_subs = self._repo.get_all_subscriptions()
        return self._reconcile_subscriptions(all_subs)

    def _reconcile_subscriptions(
        self,
        subscriptions: List[Subscription],
        workspace_id: Optional[str] = None,
    ) -> BillingReconciliationReport:
        discrepancies: List[Dict[str, Any]] = []

        for sub in subscriptions:
            try:
                prov_sub = self._provider.get_subscription(sub.external_subscription_id)
                if not prov_sub:
                    discrepancies.append({
                        "workspace_id": sub.workspace_id,
                        "subscription_id": sub.subscription_id,
                        "external_subscription_id": sub.external_subscription_id,
                        "issue": "MISSING_PROVIDER_SUBSCRIPTION",
                        "severity": "HIGH",
                        "details": "Subscription exists in internal database but not found on provider.",
                    })
                    continue

                # Check status match
                if sub.status.value != prov_sub.status.value:
                    discrepancies.append({
                        "workspace_id": sub.workspace_id,
                        "subscription_id": sub.subscription_id,
                        "external_subscription_id": sub.external_subscription_id,
                        "issue": "STATUS_MISMATCH",
                        "severity": "HIGH",
                        "internal_status": sub.status.value,
                        "provider_status": prov_sub.status.value,
                    })

                # Check plan code match
                if sub.plan_code.upper() != prov_sub.plan_code.upper():
                    discrepancies.append({
                        "workspace_id": sub.workspace_id,
                        "subscription_id": sub.subscription_id,
                        "external_subscription_id": sub.external_subscription_id,
                        "issue": "PLAN_MISMATCH",
                        "severity": "MEDIUM",
                        "internal_plan": sub.plan_code,
                        "provider_plan": prov_sub.plan_code,
                    })

            except Exception as e:
                discrepancies.append({
                    "workspace_id": sub.workspace_id,
                    "subscription_id": sub.subscription_id,
                    "issue": "PROVIDER_LOOKUP_ERROR",
                    "severity": "LOW",
                    "error": str(e),
                })

        is_healthy = len(discrepancies) == 0
        now = datetime.now(timezone.utc).isoformat()
        logger.info(
            "Reconciliation audit completed: %d subscriptions audited, %d discrepancies found",
            len(subscriptions),
            len(discrepancies),
        )

        return BillingReconciliationReport(
            workspace_id=workspace_id,
            audited_at=now,
            total_subscriptions_audited=len(subscriptions),
            mismatches_found=len(discrepancies),
            discrepancies=discrepancies,
            is_healthy=is_healthy,
        )


# Global reconciliation service instance
reconciliation_service = BillingReconciliationService()
