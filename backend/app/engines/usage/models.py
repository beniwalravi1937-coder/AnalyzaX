"""
Domain models for Phase 20: Advanced Usage Metering, Quotas, Entitlements & Plan Management.
Defines immutable plans, entitlements, usage metrics, events, reservations, and quota responses.
"""

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, computed_field


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class PlanTier(str, Enum):
    FREE = "FREE"
    PRO = "PRO"
    TEAM = "TEAM"
    ENTERPRISE = "ENTERPRISE"


class PlanStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class FeatureType(str, Enum):
    BOOLEAN = "BOOLEAN"
    LIMIT = "LIMIT"
    QUOTA = "QUOTA"
    TIER = "TIER"


class QuotaPeriod(str, Enum):
    MONTHLY = "MONTHLY"
    DAILY = "DAILY"
    LIFETIME = "LIFETIME"
    CURRENT = "CURRENT"  # Point-in-time resource state (e.g. current storage bytes, current project count)


class LimitPolicy(str, Enum):
    HARD_LIMIT = "HARD_LIMIT"
    SOFT_LIMIT = "SOFT_LIMIT"
    BLOCK_NEW_OPERATION = "BLOCK_NEW_OPERATION"
    READ_ONLY_AFTER_LIMIT = "READ_ONLY_AFTER_LIMIT"


class ReservationStatus(str, Enum):
    RESERVED = "RESERVED"
    CONSUMED = "CONSUMED"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


class MetricUnit(str, Enum):
    COUNT = "COUNT"
    BYTES = "BYTES"
    MEGABYTES = "MEGABYTES"
    GIGABYTES = "GIGABYTES"
    MS = "MS"
    TOKENS = "TOKENS"
    ROWS = "ROWS"


class QuotaHealthStatus(str, Enum):
    NORMAL = "NORMAL"        # < 70%
    WARNING = "WARNING"      # 70% - 89%
    CRITICAL = "CRITICAL"    # 90% - 99%
    EXCEEDED = "EXCEEDED"    # >= 100%
    UNLIMITED = "UNLIMITED"


# ─────────────────────────────────────────────────────────────
# Domain Entities
# ─────────────────────────────────────────────────────────────

class Plan(BaseModel):
    """Immutable plan catalog definition."""
    plan_id: str = Field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:12]}")
    plan_code: str  # e.g. "free", "pro", "team", "enterprise"
    name: str
    description: str
    tier: PlanTier = PlanTier.FREE
    version: int = 1
    status: PlanStatus = PlanStatus.ACTIVE
    is_default: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("plan_code", mode="before")
    @classmethod
    def _normalize_code(cls, v: Any) -> str:
        return str(v).upper() if v else "FREE"


class PlanEntitlement(BaseModel):
    """Specific feature or limit entitled to a plan."""
    entitlement_id: str = Field(default_factory=lambda: f"ent_{uuid.uuid4().hex[:12]}")
    plan_id: str
    feature_key: str  # Canonical feature key (e.g. "AI_ANALYST", "MAX_PROJECTS")
    enabled: bool = True
    value: Optional[Union[int, float, str, bool]] = None  # None indicates unlimited if enabled
    unit: Optional[str] = None  # e.g. "messages/month", "MB", "projects"
    limit_type: FeatureType = FeatureType.QUOTA
    period: QuotaPeriod = QuotaPeriod.MONTHLY
    policy: LimitPolicy = LimitPolicy.BLOCK_NEW_OPERATION
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def limit(self) -> Optional[Union[int, float, str, bool]]:
        return self.value


class WorkspacePlan(BaseModel):
    """Current plan assignment for a workspace."""
    workspace_plan_id: str = Field(default_factory=lambda: f"wsplan_{uuid.uuid4().hex[:12]}")
    workspace_id: str
    plan_id: str
    plan_code: str = "FREE"
    plan_version: int = 1
    status: PlanStatus = PlanStatus.ACTIVE
    effective_from: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    effective_until: Optional[str] = None
    assigned_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("plan_code", mode="before")
    @classmethod
    def _normalize_code(cls, v: Any) -> str:
        return str(v).upper() if v else "FREE"


class UsageEvent(BaseModel):
    """
    Immutable, append-only usage event record.
    Represents discrete metric consumption with strict idempotency.
    """
    usage_event_id: str = Field(default_factory=lambda: f"usevt_{uuid.uuid4().hex[:16]}")
    workspace_id: str
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    metric_key: str
    quantity: float = 1.0
    unit: str = "count"
    operation_type: str = "OPERATION"
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    job_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    period_key: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m"))
    occurred_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("quantity")
    @classmethod
    def _validate_quantity(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Usage quantity must be positive")
        return v


class UsageReservation(BaseModel):
    """Concurrency-safe reservation for asynchronous or multi-step operations."""
    reservation_id: str = Field(default_factory=lambda: f"res_{uuid.uuid4().hex[:16]}")
    workspace_id: str
    metric_key: str
    quantity: float = 1.0
    status: ReservationStatus = ReservationStatus.RESERVED
    expires_at: str
    operation_id: Optional[str] = None
    job_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finalized_at: Optional[str] = None


class UsageAggregation(BaseModel):
    """Fast period-based rolled up usage cache for O(1) balance lookups."""
    workspace_id: str
    period_key: str  # e.g. "2026-09" or "current"
    metric_key: str
    total_quantity: float = 0.0
    last_updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ─────────────────────────────────────────────────────────────
# Request & Response DTOs
# ─────────────────────────────────────────────────────────────

class QuotaDecision(BaseModel):
    """Structured result of a quota or entitlement check."""
    allowed: bool
    metric: Optional[str] = None
    feature: Optional[str] = None
    current_usage: float = 0.0
    requested: float = 1.0
    limit: Optional[float] = None
    remaining: Optional[float] = None
    reason: Optional[str] = None
    period: Optional[str] = None
    reset_at: Optional[str] = None
    plan: str = "FREE"


class MetricUsageDetail(BaseModel):
    """User-facing metric consumption progress for dashboards."""
    metric_key: str
    display_name: str
    description: str
    category: str
    used: float
    limit: Optional[float] = None
    remaining: Optional[float] = None
    percentage: Optional[float] = None
    unit: str
    period: QuotaPeriod
    status: QuotaHealthStatus

    @computed_field
    @property
    def is_exceeded(self) -> bool:
        return self.status == QuotaHealthStatus.EXCEEDED or (self.limit is not None and self.used >= self.limit)


class FeatureEntitlementDetail(BaseModel):
    """Feature capability status for a workspace."""
    feature_key: str
    display_name: str
    category: str
    enabled: bool
    limit_value: Optional[Union[int, float, str, bool]] = None
    unit: Optional[str] = None


class UsageSummaryResponse(BaseModel):
    """Complete workspace usage summary."""
    workspace_id: str
    plan: Plan
    plan_code: str = "FREE"
    period_start: str
    period_end: str
    days_remaining: int
    metrics: List[MetricUsageDetail]
    features: List[FeatureEntitlementDetail]

    @computed_field
    @property
    def quotas(self) -> List[MetricUsageDetail]:
        return self.metrics

    @computed_field
    @property
    def resources(self) -> List[MetricUsageDetail]:
        return [m for m in self.metrics if m.period == QuotaPeriod.CURRENT]


UsageSummaryDTO = UsageSummaryResponse


class UsageHistoryItem(BaseModel):
    """Paginated usage history record."""
    usage_event_id: str
    metric_key: str
    quantity: float
    unit: str
    operation_type: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    user_id: Optional[str] = None
    occurred_at: str


class UsageHistoryResponse(BaseModel):
    items: List[UsageHistoryItem]
    total: int
    next_cursor: Optional[str] = None
    has_more: bool = False

    @computed_field
    @property
    def events(self) -> List[UsageHistoryItem]:
        return self.items


class AssignPlanRequest(BaseModel):
    plan_code: str
    reason: Optional[str] = None


class PlanComparisonItem(BaseModel):
    feature_key: str
    display_name: str
    category: str
    free_value: str
    pro_value: str
    team_value: str
    enterprise_value: str


PlanComparisonDTO = PlanComparisonItem


class PlanComparisonResponse(BaseModel):
    plans: List[Plan]
    comparisons: List[PlanComparisonItem]


class UsageReconciliationReport(BaseModel):
    workspace_id: str
    period_key: str
    reconciled_at: str
    metrics_audited: int
    discrepancies_found: int
    discrepancies: List[Dict[str, Any]]
    is_healthy: bool
