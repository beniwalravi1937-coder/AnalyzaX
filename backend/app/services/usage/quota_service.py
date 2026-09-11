"""
Quota Enforcement & Concurrency-Safe Reservation Service for Phase 20.
Evaluates workspace plans, feature entitlements, and metric consumption.
Provides atomic reservations for multi-step jobs and structured QUOTA_EXCEEDED errors.
"""

from calendar import monthrange
from datetime import datetime, timedelta, timezone
import logging
import threading
from typing import Any, Dict, Optional

from backend.app.core.errors import QuotaExceededException
from backend.app.engines.notifications.models import (
    ApplicationEvent,
    ApplicationEventType,
)
from backend.app.engines.usage.catalog import Features
from backend.app.engines.usage.metrics import (
    UsageMetrics,
    get_metric_definition,
)
from backend.app.engines.usage.models import (
    FeatureType,
    LimitPolicy,
    QuotaDecision,
    QuotaPeriod,
    ReservationStatus,
    UsageEvent,
    UsageReservation,
)
from backend.app.engines.usage.repository import UsageRepository, usage_repo
from backend.app.services.notifications.event_dispatcher import event_dispatcher
from backend.app.services.usage.plan_service import PlanService, plan_service
from backend.app.services.usage.usage_service import UsageService, usage_service

logger = logging.getLogger("analyzax")


# Metric to Feature Key mapping
METRIC_FEATURE_MAP: Dict[str, str] = {
    UsageMetrics.DATASET_UPLOADS: Features.DATASET_UPLOAD,
    UsageMetrics.DATASET_STORAGE_BYTES: Features.STORAGE_LIMIT_BYTES,
    UsageMetrics.PROJECT_COUNT: Features.MAX_PROJECTS,
    UsageMetrics.WORKSPACE_MEMBER_COUNT: Features.MAX_WORKSPACE_MEMBERS,
    UsageMetrics.AI_ANALYST_MESSAGES: Features.AI_ANALYST,
    UsageMetrics.SQL_QUERY_EXECUTIONS: Features.SQL_ANALYTICS,
    UsageMetrics.ML_EXPERIMENTS: Features.MACHINE_LEARNING,
    UsageMetrics.FORECAST_RUNS: Features.FORECASTING,
    UsageMetrics.STATISTICAL_ANALYSES: Features.ADVANCED_STATISTICS,
    UsageMetrics.EXPORTS_GENERATED: Features.EXPORTS,
}


class QuotaService:
    """
    Centralized Quota & Entitlement Enforcement Service.
    Guarantees server-side authorization and concurrency safety.
    """

    def __init__(
        self,
        repository: Optional[UsageRepository] = None,
        plan_svc: Optional[PlanService] = None,
        usage_svc: Optional[UsageService] = None,
        plan_service: Optional[PlanService] = None,
        usage_service: Optional[UsageService] = None,
    ):
        self._lock = threading.RLock()
        self._repo = repository or usage_repo
        self._plan_svc = plan_svc or plan_service or globals().get("plan_service")
        self._usage_svc = usage_svc or usage_service or globals().get("usage_service")
        # Cooldown cache: f"{workspace_id}:{metric_key}:{threshold}" -> YYYY-MM
        self._warning_cooldowns: Dict[str, str] = {}

    def check_feature(self, workspace_id: str, feature_key: str) -> bool:
        """
        Checks whether a boolean or quota feature is enabled for a workspace.
        """
        # Map uppercase feature name if passed
        f_key = feature_key.lower()
        ent = self._plan_svc.get_feature_entitlement(workspace_id, f_key)
        if not ent:
            ent = self._plan_svc.get_feature_entitlement(workspace_id, feature_key)
        if not ent:
            return False
        return ent.enabled

    def enforce_feature(self, workspace_id: str, feature_key: str) -> None:
        """Enforces that a feature is entitled for the workspace. Raises QuotaExceededException if disabled."""
        if not self.check_feature(workspace_id, feature_key):
            from backend.app.core.errors import QuotaExceededException
            plan = self._plan_svc.get_workspace_plan(workspace_id)
            raise QuotaExceededException(
                message=f"Feature '{feature_key}' is not available on your current plan ({plan.plan_code}). Please upgrade.",
                metric=feature_key,
                feature=feature_key,
                current_usage=0.0,
                requested=1.0,
                limit=0.0,
                remaining=0.0,
                period="CURRENT",
                plan=plan.plan_code,
            )

    def check_quota(
        self,
        workspace_id: str,
        metric_key: str,
        requested_quantity: float = 1.0,
        quantity: Optional[float] = None,
    ) -> QuotaDecision:
        """
        Evaluates current consumption + active reservations against plan entitlements.
        Returns structured QuotaDecision without modifying state.
        """
        req_qty = quantity if quantity is not None else requested_quantity
        with self._lock:
            # Expire stale reservations
            self._repo.cleanup_expired_reservations()

            plan = self._plan_svc.get_workspace_plan(workspace_id)
            f_key = METRIC_FEATURE_MAP.get(metric_key, metric_key)
            ent = self._plan_svc.get_feature_entitlement(workspace_id, f_key)

            # Calculate period metadata
            now = datetime.now(timezone.utc)
            year, month = now.year, now.month
            num_days = monthrange(year, month)[1]
            reset_at = f"{year:04d}-{month:02d}-{num_days:02d}T23:59:59Z"

            if not ent or not ent.enabled:
                return QuotaDecision(
                    allowed=False,
                    metric=metric_key,
                    feature=f_key,
                    current_usage=0.0,
                    requested=req_qty,
                    limit=0.0,
                    remaining=0.0,
                    reason=f"Feature '{f_key}' is not included in the {plan.name} plan.",
                    period=QuotaPeriod.MONTHLY.value,
                    reset_at=reset_at,
                    plan=plan.plan_code.upper(),
                )

            # Unlimited entitlement
            if ent.value is None or ent.value is True:
                return QuotaDecision(
                    allowed=True,
                    metric=metric_key,
                    feature=f_key,
                    current_usage=0.0,
                    requested=req_qty,
                    limit=None,
                    remaining=None,
                    reason=None,
                    period=ent.period.value,
                    reset_at=reset_at,
                    plan=plan.plan_code.upper(),
                )

            limit_val = float(ent.value)
            consumed = self._usage_svc.get_usage(workspace_id, metric_key)
            active_reserved = self._repo.get_active_reserved_quantity(workspace_id, metric_key)
            effective_usage = consumed + active_reserved

            remaining = max(0.0, limit_val - effective_usage)
            new_total = effective_usage + req_qty

            # Quota exceeded check
            if new_total > limit_val:
                if ent.policy == LimitPolicy.SOFT_LIMIT:
                    # Soft limit logs warning but allows operation
                    logger.warning(
                        "Workspace %s exceeded soft limit for %s: %f / %f",
                        workspace_id,
                        metric_key,
                        new_total,
                        limit_val,
                    )
                    return QuotaDecision(
                        allowed=True,
                        metric=metric_key,
                        feature=f_key,
                        current_usage=effective_usage,
                        requested=req_qty,
                        limit=limit_val,
                        remaining=0.0,
                        reason="Soft limit exceeded (allowed)",
                        period=ent.period.value,
                        reset_at=reset_at,
                        plan=plan.plan_code.upper(),
                    )

                # Hard limit / Block new operation
                return QuotaDecision(
                    allowed=False,
                    metric=metric_key,
                    feature=f_key,
                    current_usage=effective_usage,
                    requested=req_qty,
                    limit=limit_val,
                    remaining=remaining,
                    reason=(
                        f"Quota exceeded for {metric_key.replace('_', ' ')}. "
                        f"Current: {effective_usage:g}/{limit_val:g} {ent.unit or ''}. "
                        f"Resets on {reset_at[:10]}. Upgrade your plan to increase limits."
                    ),
                    period=ent.period.value,
                    reset_at=reset_at,
                    plan=plan.plan_code.upper(),
                )

            # Check threshold notification triggers
            self._check_and_emit_warnings(workspace_id, metric_key, new_total, limit_val)

            return QuotaDecision(
                allowed=True,
                metric=metric_key,
                feature=f_key,
                current_usage=effective_usage,
                requested=req_qty,
                limit=limit_val,
                remaining=remaining,
                reason=None,
                period=ent.period.value,
                reset_at=reset_at,
                plan=plan.plan_code.upper(),
            )

    def enforce_quota(
        self,
        workspace_id: str,
        metric_key: str,
        requested_quantity: float = 1.0,
        quantity: Optional[float] = None,
    ) -> QuotaDecision:
        """
        Enforces quota strictly. Raises QuotaExceededException if not allowed.
        """
        req_qty = quantity if quantity is not None else requested_quantity
        decision = self.check_quota(workspace_id, metric_key, req_qty)
        if not decision.allowed:
            raise QuotaExceededException(
                message=decision.reason or f"Quota limit reached for {metric_key}",
                metric=decision.metric,
                feature=decision.feature,
                current_usage=decision.current_usage,
                requested=decision.requested,
                limit=decision.limit,
                remaining=decision.remaining,
                period=decision.period,
                reset_at=decision.reset_at,
                plan=decision.plan,
            )
        return decision

    def reserve_quota(
        self,
        workspace_id: str,
        metric_key: str,
        quantity: float = 1.0,
        ttl_seconds: int = 300,
        operation_id: Optional[str] = None,
        job_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UsageReservation:
        """
        Atomic Check + Reserve pattern for concurrency safety.
        Prevents race conditions on simultaneous requests.
        """
        with self._lock:
            decision = self.enforce_quota(workspace_id, metric_key, quantity=quantity)

            expires_at = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()
            reservation = UsageReservation(
                workspace_id=workspace_id,
                metric_key=metric_key,
                quantity=quantity,
                status=ReservationStatus.RESERVED,
                expires_at=expires_at,
                operation_id=operation_id,
                job_id=job_id,
                user_id=user_id,
                metadata=metadata or {},
            )
            created = self._repo.create_reservation(reservation)
            logger.debug(
                "Created reservation %s for %s (%f units) in workspace %s",
                created.reservation_id,
                metric_key,
                quantity,
                workspace_id,
            )
            return created

    def finalize_quota(
        self,
        reservation_id: str,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        operation_type: str = "OPERATION",
        idempotency_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UsageEvent:
        """
        Finalizes a reservation into permanent consumed usage upon successful job completion.
        """
        with self._lock:
            res = self._repo.get_reservation(reservation_id)
            if not res or res.status != ReservationStatus.RESERVED:
                raise ValueError(f"Invalid or already finalized reservation: {reservation_id}")

            self._repo.finalize_reservation(reservation_id)
            event = self._usage_svc.record_usage(
                workspace_id=res.workspace_id,
                metric_key=res.metric_key,
                quantity=res.quantity,
                user_id=user_id or res.user_id,
                project_id=project_id,
                job_id=reservation_id,
                operation_type=operation_type,
                idempotency_key=idempotency_key or f"res_fin_{reservation_id}",
                metadata=metadata or res.metadata or {},
            )
            return event

    def release_quota(self, reservation_id: str) -> Optional[UsageReservation]:
        """
        Releases an active reservation if an asynchronous job failed or was cancelled.
        """
        with self._lock:
            res = self._repo.release_reservation(reservation_id)
            if res:
                logger.debug("Released reservation %s for workspace %s", reservation_id, res.workspace_id)
            return res

    def _check_and_emit_warnings(
        self,
        workspace_id: str,
        metric_key: str,
        new_usage: float,
        limit_val: float,
    ) -> None:
        """Emits threshold warning events (at 80%, 90%, 100%) with monthly deduplication."""
        if limit_val <= 0:
            return

        pct = new_usage / limit_val
        now_period = datetime.now(timezone.utc).strftime("%Y-%m")

        thresholds = [(1.0, "100"), (0.9, "90"), (0.8, "80")]
        for t_val, t_name in thresholds:
            if pct >= t_val:
                cooldown_key = f"{workspace_id}:{metric_key}:{t_name}"
                if self._warning_cooldowns.get(cooldown_key) != now_period:
                    self._warning_cooldowns[cooldown_key] = now_period
                    try:
                        event_type = (
                            ApplicationEventType.QUOTA_EXCEEDED
                            if t_val >= 1.0
                            else ApplicationEventType.QUOTA_WARNING
                        )
                        event_dispatcher.dispatch(
                            ApplicationEvent(
                                event_type=event_type,
                                workspace_id=workspace_id,
                                metadata={
                                    "metric_key": metric_key,
                                    "current_usage": new_usage,
                                    "limit": limit_val,
                                    "threshold_percentage": int(t_val * 100),
                                    "recipient_id": "ws_members",
                                },
                            )
                        )
                    except Exception as e:
                        logger.warning("Failed dispatching quota warning event: %s", e)
                break


# Global singleton
quota_service = QuotaService()
