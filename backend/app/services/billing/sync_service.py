"""
Subscription Synchronization Service for Phase 21: Billing.
Authoritatively bridges external provider subscription state to internal WorkspacePlan & Entitlements.
"""

from datetime import datetime, timezone
import logging
from typing import Optional

from backend.app.core.config import settings
from backend.app.engines.billing import get_billing_provider
from backend.app.engines.billing.models import (
    BillingPrice,
    Subscription,
    SubscriptionStatus,
)
from backend.app.engines.billing.provider import BillingProvider, NormalizedWebhookEvent
from backend.app.engines.billing.repository import BillingRepository, billing_repository
from backend.app.engines.notifications.models import (
    ApplicationEventType,
    NotificationCategory,
    NotificationPriority,
)
from backend.app.engines.usage.models import PlanTier
from backend.app.services.notifications.event_dispatcher import (
    EventDispatcher,
    event_dispatcher,
)
from backend.app.services.usage.plan_service import PlanService, plan_service

logger = logging.getLogger("analyzax.billing.sync")


class BillingSyncService:
    """
    Synchronizes external payment provider subscription state into internal
    Subscription entities and drives WorkspacePlan entitlement updates.
    """

    def __init__(
        self,
        repo: Optional[BillingRepository] = None,
        provider: Optional[BillingProvider] = None,
        plans: Optional[PlanService] = None,
        dispatcher: Optional[EventDispatcher] = None,
    ):
        self._repo = repo or billing_repository
        self._provider = provider or get_billing_provider()
        self._plans = plans or plan_service
        self._dispatcher = dispatcher or event_dispatcher

    def sync_subscription(
        self,
        workspace_id: str,
        external_subscription_id: str,
        normalized_event: Optional[NormalizedWebhookEvent] = None,
    ) -> Subscription:
        """
        Synchronizes a subscription:
        1. Retrieves authoritative state from provider (or uses normalized webhook state).
        2. Persists normalized Subscription in BillingRepository.
        3. Updates WorkspacePlan in Usage engine (driving immediate entitlement updates).
        4. Emits appropriate notification.
        """
        provider_sub = self._provider.get_subscription(external_subscription_id)

        now = datetime.now(timezone.utc).isoformat()
        if not provider_sub and normalized_event:
            # Reconstruct from verified webhook event payload
            plan_code = normalized_event.plan_code or "PRO"
            sub_status_str = (normalized_event.status or "active").lower()
            try:
                sub_status = SubscriptionStatus(sub_status_str)
            except ValueError:
                sub_status = SubscriptionStatus.ACTIVE

            price_id = normalized_event.external_price_id or "bprice_pro_monthly"
            provider_sub = Subscription(
                workspace_id=workspace_id,
                billing_customer_id=normalized_event.external_customer_id or f"cust_{workspace_id}",
                provider=self._provider.provider_name,
                external_subscription_id=external_subscription_id,
                plan_code=plan_code.upper(),
                billing_price_id=price_id,
                status=sub_status,
                currency=normalized_event.currency or "USD",
                current_period_start=normalized_event.current_period_start or now,
                current_period_end=normalized_event.current_period_end or now,
                cancel_at_period_end=bool(normalized_event.cancel_at_period_end),
            )

        if not provider_sub:
            raise ValueError(f"Unable to resolve subscription '{external_subscription_id}' from provider")

        # Save normalized internal subscription
        saved_sub = self._repo.save_subscription(provider_sub)

        # Synchronize with internal WorkspacePlan
        self._apply_subscription_to_workspace_plan(workspace_id, saved_sub)

        return saved_sub

    def _apply_subscription_to_workspace_plan(self, workspace_id: str, sub: Subscription) -> None:
        """
        Authoritatively drives WorkspacePlan based on Subscription status:
        - ACTIVE / TRIALING / CANCELING (before period end) -> Grants plan tier.
        - CANCELED / UNPAID -> Falls back to FREE plan without deleting any data.
        - PAST_DUE -> Checks grace period.
        """
        target_tier = PlanTier.FREE

        if sub.is_active_entitlement:
            try:
                target_tier = PlanTier(sub.plan_code.upper())
            except ValueError:
                target_tier = PlanTier.PRO
        elif sub.status == SubscriptionStatus.PAST_DUE:
            # Check grace period
            is_in_grace = True
            try:
                end_dt = datetime.fromisoformat(sub.current_period_end.replace("Z", "+00:00"))
                grace_limit = end_dt.timestamp() + (settings.BILLING_GRACE_PERIOD_DAYS * 86400)
                if datetime.now(timezone.utc).timestamp() > grace_limit:
                    is_in_grace = False
            except Exception:
                is_in_grace = False

            if is_in_grace:
                try:
                    target_tier = PlanTier(sub.plan_code.upper())
                except ValueError:
                    target_tier = PlanTier.PRO
            else:
                target_tier = PlanTier.FREE

        # Assign plan in Phase 20 engine
        existing_wp = self._plans.get_workspace_assignment(workspace_id)
        current_code = existing_wp.plan_code if existing_wp else "FREE"

        if current_code.upper() != target_tier.value.upper():
            logger.info(
                "Subscription state '%s' driving workspace '%s' plan transition from '%s' to '%s'",
                sub.status.value,
                workspace_id,
                current_code,
                target_tier.value,
            )
            self._plans.assign_plan(
                workspace_id=workspace_id,
                plan_tier=target_tier,
                assigned_by="system:billing_sync",
                reason=f"Billing sync: subscription {sub.external_subscription_id} status {sub.status.value}",
            )

            # Emit notification
            try:
                evt_type = (
                    ApplicationEventType.SUBSCRIPTION_ACTIVATED
                    if target_tier != PlanTier.FREE
                    else ApplicationEventType.SUBSCRIPTION_CANCELED
                )
                self._dispatcher.create_and_dispatch(
                    event_type=evt_type,
                    workspace_id=workspace_id,
                    metadata={"new_plan": target_tier.value, "plan_name": target_tier.value},
                )
            except Exception as e:
                logger.warning("Failed to dispatch subscription notification: %s", e)


# Global sync service instance
sync_service = BillingSyncService()
