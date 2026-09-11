"""
Subscription Management Service for Phase 21: Billing.
Coordinates plan upgrades, downgrades, period-end cancellations, and resumptions.
Ensures downgrade safety: historical datasets, models, and lineage are never deleted.
"""

from datetime import datetime, timezone
import logging
from typing import Optional

from backend.app.engines.billing import get_billing_provider
from backend.app.engines.billing.models import (
    BillingInterval,
    BillingOverviewResponse,
    Subscription,
    SubscriptionStatus,
)
from backend.app.engines.billing.provider import BillingProvider
from backend.app.engines.billing.repository import BillingRepository, billing_repository
from backend.app.engines.notifications.models import (
    ApplicationEventType,
    NotificationCategory,
    NotificationPriority,
)
from backend.app.services.billing.catalog_service import (
    BillingCatalogService,
    catalog_service,
)
from backend.app.services.billing.sync_service import (
    BillingSyncService,
    sync_service,
)
from backend.app.services.notifications.event_dispatcher import (
    EventDispatcher,
    event_dispatcher,
)
from backend.app.services.usage.plan_service import PlanService, plan_service

logger = logging.getLogger("analyzax.billing.subscription")


class BillingSubscriptionService:
    """Handles self-serve lifecycle operations for workspace subscriptions."""

    def __init__(
        self,
        repo: Optional[BillingRepository] = None,
        provider: Optional[BillingProvider] = None,
        catalog_svc: Optional[BillingCatalogService] = None,
        sync_svc: Optional[BillingSyncService] = None,
        plans: Optional[PlanService] = None,
        dispatcher: Optional[EventDispatcher] = None,
    ):
        self._repo = repo or billing_repository
        self._provider = provider or get_billing_provider()
        self._catalog = catalog_svc or catalog_service
        self._sync = sync_svc or sync_service
        self._plans = plans or plan_service
        self._dispatcher = dispatcher or event_dispatcher

    def get_subscription(self, workspace_id: str) -> Optional[Subscription]:
        """Retrieves internal active subscription for a workspace."""
        return self._repo.get_subscription_by_workspace(workspace_id)

    def change_subscription(
        self,
        workspace_id: str,
        new_plan_code: str,
        new_interval: Optional[BillingInterval] = None,
        proration_behavior: str = "create_prorations",
        actor_id: Optional[str] = None,
    ) -> Subscription:
        """
        Upgrades or downgrades subscription tier on provider and synchronizes internally.
        Downgrade safety: existing assets are strictly preserved in read-only state if over limit.
        """
        current_sub = self._repo.get_subscription_by_workspace(workspace_id)
        if not current_sub:
            raise ValueError(f"Workspace '{workspace_id}' does not have an active subscription to change")

        # Resolve new price
        interval = new_interval or BillingInterval.MONTH
        new_price = self._catalog.resolve_price(new_plan_code, interval)

        logger.info(
            "Changing subscription for workspace '%s' to '%s' (%s)",
            workspace_id,
            new_price.plan_code,
            new_price.interval.value,
        )

        updated_provider_sub = self._provider.change_subscription(
            external_subscription_id=current_sub.external_subscription_id,
            new_price=new_price,
            proration_behavior=proration_behavior,
        )

        # Synchronize internally
        synced = self._sync.sync_subscription(
            workspace_id=workspace_id,
            external_subscription_id=current_sub.external_subscription_id,
        )

        self._repo.record_audit(
            workspace_id=workspace_id,
            event_type="billing.subscription_changed",
            actor_id=actor_id,
            details={
                "old_plan": current_sub.plan_code,
                "new_plan": new_price.plan_code,
                "interval": new_price.interval.value,
            },
        )

        try:
            self._dispatcher.create_and_dispatch(
                event_type=ApplicationEventType.SUBSCRIPTION_CHANGED,
                workspace_id=workspace_id,
                metadata={
                    "new_plan": new_price.plan_code,
                    "old_plan": current_sub.plan_code,
                    "interval": new_price.interval.value,
                },
            )
        except Exception as e:
            logger.warning("Failed to dispatch subscription changed notification: %s", e)
        return synced

    def cancel_subscription(
        self,
        workspace_id: str,
        cancel_at_period_end: bool = True,
        reason: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> Subscription:
        """
        Cancels subscription:
        - If cancel_at_period_end=True: maintains access until current_period_end.
        - If immediate: downgrades to FREE immediately.
        In both cases: NO datasets or models are ever deleted.
        """
        current_sub = self._repo.get_subscription_by_workspace(workspace_id)
        if not current_sub:
            raise ValueError(f"Workspace '{workspace_id}' does not have an active subscription to cancel")

        logger.info(
            "Canceling subscription '%s' for workspace '%s' (Period end: %s)",
            current_sub.external_subscription_id,
            workspace_id,
            cancel_at_period_end,
        )

        updated_provider_sub = self._provider.cancel_subscription(
            external_subscription_id=current_sub.external_subscription_id,
            cancel_at_period_end=cancel_at_period_end,
            reason=reason,
        )

        synced = self._sync.sync_subscription(
            workspace_id=workspace_id,
            external_subscription_id=current_sub.external_subscription_id,
        )

        self._repo.record_audit(
            workspace_id=workspace_id,
            event_type="billing.subscription_canceled",
            actor_id=actor_id,
            details={
                "cancel_at_period_end": cancel_at_period_end,
                "effective_until": synced.current_period_end if cancel_at_period_end else "immediate",
                "reason": reason,
            },
        )

        try:
            self._dispatcher.create_and_dispatch(
                event_type=ApplicationEventType.SUBSCRIPTION_CANCELED,
                workspace_id=workspace_id,
                metadata={"effective_date": synced.current_period_end},
            )
        except Exception as e:
            logger.warning("Failed to dispatch subscription canceled notification: %s", e)
        return synced

    def resume_subscription(
        self,
        workspace_id: str,
        actor_id: Optional[str] = None,
    ) -> Subscription:
        """Resumes a subscription that was scheduled to cancel at period end."""
        current_sub = self._repo.get_subscription_by_workspace(workspace_id)
        if not current_sub:
            raise ValueError(f"No subscription found for workspace '{workspace_id}'")
        if not current_sub.cancel_at_period_end:
            return current_sub

        logger.info("Resuming subscription '%s' for workspace '%s'", current_sub.external_subscription_id, workspace_id)
        self._provider.resume_subscription(current_sub.external_subscription_id)

        synced = self._sync.sync_subscription(
            workspace_id=workspace_id,
            external_subscription_id=current_sub.external_subscription_id,
        )

        self._repo.record_audit(
            workspace_id=workspace_id,
            event_type="billing.subscription_resumed",
            actor_id=actor_id,
            details={"subscription_id": synced.subscription_id},
        )
        return synced

    def get_billing_overview(
        self,
        workspace_id: str,
        can_manage: bool = True,
    ) -> BillingOverviewResponse:
        """Assembles unified billing overview for workspace settings UI."""
        wp = self._plans.get_workspace_assignment(workspace_id)
        current_plan_code = wp.plan_code if wp else "FREE"

        customer = self._repo.get_customer_by_workspace(workspace_id)
        subscription = self._repo.get_subscription_by_workspace(workspace_id)
        prices = self._catalog.list_prices(active_only=True)
        invoices, _ = self._repo.list_invoices_by_workspace(workspace_id, limit=5)

        is_grace = False
        if subscription and subscription.status == SubscriptionStatus.PAST_DUE:
            is_grace = True

        return BillingOverviewResponse(
            workspace_id=workspace_id,
            plan_code=current_plan_code,
            customer=customer,
            subscription=subscription,
            prices=prices,
            recent_invoices=invoices,
            can_manage_billing=can_manage,
            is_grace_period=is_grace,
        )


# Global subscription service instance
subscription_service = BillingSubscriptionService()
