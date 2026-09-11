"""
Usage Application Service for Phase 20.
Coordinates append-only event recording, deterministic aggregations,
physical storage audits, and usage reconciliation.
"""

from calendar import monthrange
from datetime import datetime, timezone
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from backend.app.core.config import settings
from backend.app.engines.auth.repository import auth_repo
from backend.app.engines.usage.catalog import Features
from backend.app.engines.usage.metrics import (
    UsageMetrics,
    get_metric_definition,
    list_metric_definitions,
)
from backend.app.engines.usage.models import (
    FeatureEntitlementDetail,
    MetricUsageDetail,
    QuotaHealthStatus,
    QuotaPeriod,
    UsageEvent,
    UsageHistoryItem,
    UsageHistoryResponse,
    UsageReconciliationReport,
    UsageSummaryResponse,
)
from backend.app.engines.usage.repository import UsageRepository, usage_repo
from backend.app.engines.workspace.repository import workspace_repo
from backend.app.services.usage.plan_service import PlanService, plan_service

logger = logging.getLogger("analyzax")


class UsageService:
    """Coordinates usage recording, aggregation, and accounting."""

    def __init__(
        self,
        repository: Optional[UsageRepository] = None,
        plan_svc: Optional[PlanService] = None,
        plan_service: Optional[PlanService] = None,
    ):
        self._repo = repository or usage_repo
        self._plan_svc = plan_svc or plan_service or globals().get("plan_service")

    def record_usage(
        self,
        workspace_id: str,
        metric_key: str,
        quantity: float = 1.0,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        job_id: Optional[str] = None,
        operation_type: str = "OPERATION",
        idempotency_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UsageEvent:
        """
        Appends an immutable usage event with strict idempotency.
        Prevents duplicate charges on retries.
        """
        if quantity <= 0:
            raise ValueError(f"Usage quantity must be positive, got {quantity}")

        metric_def = get_metric_definition(metric_key)
        unit = metric_def.unit.value if metric_def else "COUNT"

        event = UsageEvent(
            workspace_id=workspace_id,
            project_id=project_id,
            user_id=user_id,
            metric_key=metric_key,
            quantity=quantity,
            unit=unit,
            operation_type=operation_type,
            resource_type=resource_type,
            resource_id=resource_id,
            job_id=job_id,
            idempotency_key=idempotency_key,
            metadata=metadata or {},
        )

        persisted, created = self._repo.record_usage_event(event)
        if not created:
            logger.info(
                "Idempotent duplicate detected for workspace %s, key %s. Existing event returned.",
                workspace_id,
                idempotency_key,
            )
        return persisted

    def get_storage_bytes(self, workspace_id: str) -> float:
        """
        Calculates physical disk space occupied by datasets and versions
        associated with the workspace without double-counting.
        """
        total_bytes = 0.0
        try:
            # 1. Look up assets belonging to workspace
            assets = workspace_repo.list_assets(workspace_id=workspace_id, asset_type="DATASET")
            for asset in assets:
                # Check data/uploads/{dataset_id}
                ds_dir = os.path.join(settings.DATA_UPLOADS_DIR, asset.asset_id)
                if os.path.exists(ds_dir):
                    for root, _, files in os.walk(ds_dir):
                        for f in files:
                            fp = os.path.join(root, f)
                            if os.path.isfile(fp):
                                total_bytes += os.path.getsize(fp)
        except Exception as e:
            logger.warning("Failed calculating physical storage for workspace %s: %s", workspace_id, e)
        return total_bytes

    def get_current_resource_count(self, workspace_id: str, metric_key: str) -> float:
        """Returns point-in-time count of active resources."""
        if metric_key == UsageMetrics.DATASET_STORAGE_BYTES:
            return self.get_storage_bytes(workspace_id)
        elif metric_key == UsageMetrics.PROJECT_COUNT:
            from backend.app.engines.workspace.models import ProjectStatus
            projects = workspace_repo.list_projects(workspace_id=workspace_id, status=ProjectStatus.ACTIVE)
            return float(len(projects))
        elif metric_key == UsageMetrics.WORKSPACE_MEMBER_COUNT:
            members = auth_repo.list_workspace_members(workspace_id=workspace_id)
            return float(len(members))
        return 0.0

    def get_usage(
        self,
        workspace_id: str,
        metric_key: str,
        period_key: Optional[str] = None,
    ) -> float:
        """
        Returns authoritative consumed usage for a metric.
        Dispatches to point-in-time counter or period accumulator based on definition.
        """
        metric_def = get_metric_definition(metric_key)
        if metric_def and metric_def.is_point_in_time:
            return self.get_current_resource_count(workspace_id, metric_key)

        effective_period = period_key or datetime.now(timezone.utc).isoformat()[:7]
        return self._repo.get_aggregate_quantity(workspace_id, effective_period, metric_key)

    def get_usage_summary(self, workspace_id: str) -> UsageSummaryResponse:
        """
        Generates comprehensive usage dashboard response including metrics,
        quota health indicators, remaining amounts, and days left in period.
        """
        plan = self._plan_svc.get_workspace_plan(workspace_id)
        entitlements = self._plan_svc.get_plan_entitlements(plan.plan_id)
        ent_by_feature = {e.feature_key: e for e in entitlements}

        now = datetime.now(timezone.utc)
        current_period = now.strftime("%Y-%m")
        year, month = now.year, now.month
        num_days = monthrange(year, month)[1]
        period_start = f"{year:04d}-{month:02d}-01T00:00:00Z"
        period_end = f"{year:04d}-{month:02d}-{num_days:02d}T23:59:59Z"
        days_remaining = max(0, num_days - now.day)

        # Mapping between UsageMetrics and Features
        metric_feature_map = {
            UsageMetrics.DATASET_UPLOADS: (Features.DATASET_UPLOAD, "uploads"),
            UsageMetrics.DATASET_STORAGE_BYTES: (Features.STORAGE_LIMIT_BYTES, "Bytes"),
            UsageMetrics.PROJECT_COUNT: (Features.MAX_PROJECTS, "projects"),
            UsageMetrics.WORKSPACE_MEMBER_COUNT: (Features.MAX_WORKSPACE_MEMBERS, "members"),
            UsageMetrics.AI_ANALYST_MESSAGES: (Features.AI_ANALYST, "messages"),
            UsageMetrics.SQL_QUERY_EXECUTIONS: (Features.SQL_ANALYTICS, "queries"),
            UsageMetrics.ML_EXPERIMENTS: (Features.MACHINE_LEARNING, "experiments"),
            UsageMetrics.FORECAST_RUNS: (Features.FORECASTING, "runs"),
            UsageMetrics.STATISTICAL_ANALYSES: (Features.ADVANCED_STATISTICS, "analyses"),
            UsageMetrics.EXPORTS_GENERATED: (Features.EXPORTS, "exports"),
        }

        metric_details: List[MetricUsageDetail] = []
        for m_def in list_metric_definitions():
            f_tuple = metric_feature_map.get(m_def.metric_key)
            if not f_tuple:
                continue
            f_key, default_unit = f_tuple
            ent = ent_by_feature.get(f_key)

            used = self.get_usage(workspace_id, m_def.metric_key, current_period)
            limit_val: Optional[float] = None
            if ent and ent.enabled and ent.value is not None and isinstance(ent.value, (int, float)):
                limit_val = float(ent.value)

            # Calculate remaining and percentage
            remaining: Optional[float] = None
            percentage: Optional[float] = None
            health_status = QuotaHealthStatus.UNLIMITED

            if limit_val is not None:
                remaining = max(0.0, limit_val - used)
                percentage = round((used / limit_val) * 100.0, 1) if limit_val > 0 else 100.0

                if percentage < 70.0:
                    health_status = QuotaHealthStatus.NORMAL
                elif percentage < 90.0:
                    health_status = QuotaHealthStatus.WARNING
                elif percentage < 100.0:
                    health_status = QuotaHealthStatus.CRITICAL
                else:
                    health_status = QuotaHealthStatus.EXCEEDED

            metric_details.append(
                MetricUsageDetail(
                    metric_key=m_def.metric_key,
                    display_name=m_def.display_name,
                    description=m_def.description,
                    category=m_def.category,
                    used=used,
                    limit=limit_val,
                    remaining=remaining,
                    percentage=percentage,
                    unit=ent.unit if (ent and ent.unit) else default_unit,
                    period=m_def.default_period,
                    status=health_status,
                )
            )

        # Feature entitlement details
        feature_details: List[FeatureEntitlementDetail] = []
        for ent in entitlements:
            feature_details.append(
                FeatureEntitlementDetail(
                    feature_key=ent.feature_key,
                    display_name=ent.feature_key.replace("_", " ").title(),
                    category=ent.limit_type.value,
                    enabled=ent.enabled,
                    limit_value=ent.value,
                    unit=ent.unit,
                )
            )

        return UsageSummaryResponse(
            workspace_id=workspace_id,
            plan=plan,
            plan_code=plan.plan_code,
            period_start=period_start,
            period_end=period_end,
            days_remaining=days_remaining,
            metrics=metric_details,
            features=feature_details,
        )

    def list_history(
        self,
        workspace_id: str,
        metric_key: Optional[str] = None,
        period_key: Optional[str] = None,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> UsageHistoryResponse:
        """Returns paginated history of immutable usage events."""
        events, total, next_cursor, has_more = self._repo.list_usage_events(
            workspace_id=workspace_id,
            metric_key=metric_key,
            period_key=period_key,
            limit=limit,
            cursor=cursor,
        )
        items = [
            UsageHistoryItem(
                usage_event_id=e.usage_event_id,
                metric_key=e.metric_key,
                quantity=e.quantity,
                unit=e.unit,
                operation_type=e.operation_type,
                resource_type=e.resource_type,
                resource_id=e.resource_id,
                user_id=e.user_id,
                occurred_at=e.occurred_at,
            )
            for e in events
        ]
        return UsageHistoryResponse(
            items=items,
            total=total,
            next_cursor=next_cursor,
            has_more=has_more,
        )

    def reconcile_usage(self, workspace_id: str, period_key: Optional[str] = None) -> UsageReconciliationReport:
        """
        Audits rolled-up aggregate balance against raw immutable UsageEvents.
        Detects discrepancies or negative anomalies.
        """
        target_period = period_key or datetime.now(timezone.utc).strftime("%Y-%m")
        events, _, _, _ = self._repo.list_usage_events(
            workspace_id=workspace_id,
            period_key=target_period,
            limit=10000,
        )

        # Sum by metric
        event_sums: Dict[str, float] = {}
        for e in events:
            event_sums[e.metric_key] = event_sums.get(e.metric_key, 0.0) + e.quantity

        discrepancies: List[Dict[str, Any]] = []
        for m_key, sum_val in event_sums.items():
            cached = self._repo.get_aggregate_quantity(workspace_id, target_period, m_key)
            if abs(cached - sum_val) > 1e-4:
                discrepancies.append({
                    "metric_key": m_key,
                    "event_sum": sum_val,
                    "cached_aggregation": cached,
                    "delta": cached - sum_val,
                })

        return UsageReconciliationReport(
            workspace_id=workspace_id,
            period_key=target_period,
            reconciled_at=datetime.now(timezone.utc).isoformat(),
            metrics_audited=len(event_sums),
            discrepancies_found=len(discrepancies),
            discrepancies=discrepancies,
            is_healthy=len(discrepancies) == 0,
        )

    get_current_usage = get_usage
    reconcile_workspace_usage = reconcile_usage


# Global singleton
usage_service = UsageService()
