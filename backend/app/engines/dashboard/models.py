"""
Domain Models for Phase 14 Dashboard, Insight Workspace, and Analytical Storytelling.
Defines Dashboard, Component, Filter, Source, Provenance, Action, and Request/Response contracts.
"""

from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class ComponentType(str, Enum):
    CHART = "CHART"
    TABLE = "TABLE"
    KPI = "KPI"
    TEXT = "TEXT"
    STATISTICS = "STATISTICS"
    ML_RESULT = "ML_RESULT"
    FORECAST = "FORECAST"
    EDA_FINDING = "EDA_FINDING"
    AI_INSIGHT = "AI_INSIGHT"
    DIVIDER = "DIVIDER"
    SECTION = "SECTION"


class SourceType(str, Enum):
    SQL_RESULT = "SQL_RESULT"
    EDA_RESULT = "EDA_RESULT"
    STATISTICAL_RESULT = "STATISTICAL_RESULT"
    ML_RESULT = "ML_RESULT"
    FORECAST_RESULT = "FORECAST_RESULT"
    VISUALIZATION = "VISUALIZATION"
    AI_ANALYST_RESULT = "AI_ANALYST_RESULT"
    MANUAL = "MANUAL"


class RefreshPolicy(str, Enum):
    RELOAD = "RELOAD"
    RECOMPUTE = "RECOMPUTE"
    STATIC = "STATIC"


class ComponentStatus(str, Enum):
    IDLE = "IDLE"
    LOADING = "LOADING"
    READY = "READY"
    STALE_VERSION = "STALE_VERSION"
    ERROR = "ERROR"
    UNAVAILABLE = "UNAVAILABLE"


class FilterScope(str, Enum):
    GLOBAL = "GLOBAL"
    COMPONENT = "COMPONENT"


class FilterOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    NOT_IN = "not_in"
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    BETWEEN = "between"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class ActionType(str, Enum):
    ADD_COMPONENT = "ADD_COMPONENT"
    REMOVE_COMPONENT = "REMOVE_COMPONENT"
    UPDATE_COMPONENT = "UPDATE_COMPONENT"
    MOVE_COMPONENT = "MOVE_COMPONENT"
    RESIZE_COMPONENT = "RESIZE_COMPONENT"
    ADD_FILTER = "ADD_FILTER"
    UPDATE_FILTER = "UPDATE_FILTER"


# ─────────────────────────────────────────────────────────────
# Layout, Source, & Provenance Models
# ─────────────────────────────────────────────────────────────

class ComponentPosition(BaseModel):
    x: int = Field(default=0, ge=0, description="Column offset on 12-col grid")
    y: int = Field(default=0, ge=0, description="Row offset")


class ComponentSize(BaseModel):
    width: int = Field(default=6, ge=1, le=12, description="Width spanning 1-12 columns")
    height: int = Field(default=4, ge=1, le=24, description="Height in grid row units")


class ComponentSource(BaseModel):
    source_type: SourceType
    source_id: Optional[str] = None
    dataset_id: str
    dataset_version_id: str
    result_id: Optional[str] = None
    chart_id: Optional[str] = None
    engine: str = "core"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ComponentProvenance(BaseModel):
    dataset_id: str
    dataset_version_id: str
    source_engine: str
    result_id: Optional[str] = None
    chart_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_refreshed_at: Optional[datetime] = None
    is_stale: bool = False
    stale_reason: Optional[str] = None


# ─────────────────────────────────────────────────────────────
# Filter Model
# ─────────────────────────────────────────────────────────────

class DashboardFilter(BaseModel):
    filter_id: str = Field(default_factory=lambda: f"flt_{uuid.uuid4().hex[:10]}")
    field: str
    operator: FilterOperator
    value: Any = None
    value2: Optional[Any] = None  # For 'between' operator
    data_type: str = "categorical"  # "numeric", "categorical", "datetime", "boolean"
    scope: FilterScope = FilterScope.GLOBAL
    component_ids: List[str] = Field(default_factory=list, description="Target components if COMPONENT scope")
    default_value: Optional[Any] = None
    label: Optional[str] = None


# ─────────────────────────────────────────────────────────────
# Component Model
# ─────────────────────────────────────────────────────────────

class DashboardComponent(BaseModel):
    component_id: str = Field(default_factory=lambda: f"cmp_{uuid.uuid4().hex[:10]}")
    dashboard_id: str
    type: ComponentType
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    position: ComponentPosition = Field(default_factory=ComponentPosition)
    size: ComponentSize = Field(default_factory=ComponentSize)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    source: ComponentSource
    dataset_id: str
    dataset_version_id: str
    result_reference: Optional[Dict[str, Any]] = None
    visualization_reference: Optional[Dict[str, Any]] = None
    filter_bindings: List[str] = Field(default_factory=list)
    refresh_policy: RefreshPolicy = RefreshPolicy.RELOAD
    status: ComponentStatus = ComponentStatus.READY
    provenance: Optional[ComponentProvenance] = None
    visibility: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────────────────────
# Dashboard Aggregate & Theme
# ─────────────────────────────────────────────────────────────

class DashboardLayout(BaseModel):
    columns: int = 12
    breakpoints: Dict[str, int] = Field(
        default_factory=lambda: {"desktop": 12, "tablet": 8, "mobile": 4}
    )


class DashboardTheme(BaseModel):
    mode: str = "dark"
    density: str = "comfortable"  # "compact", "comfortable", "spacious"
    font_size: str = "medium"
    accent_color: str = "indigo"


class Dashboard(BaseModel):
    dashboard_id: str = Field(default_factory=lambda: f"dsh_{uuid.uuid4().hex[:12]}")
    name: str
    description: Optional[str] = None
    dataset_id: str
    dataset_version_id: str
    status: str = "active"
    layout: DashboardLayout = Field(default_factory=DashboardLayout)
    components: List[DashboardComponent] = Field(default_factory=list)
    filters: List[DashboardFilter] = Field(default_factory=list)
    variables: Dict[str, Any] = Field(default_factory=dict)
    theme: DashboardTheme = Field(default_factory=DashboardTheme)
    version: int = 1
    configuration_hash: str = ""
    created_by: str = "user"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def compute_hash(self) -> str:
        """Computes SHA-256 hash of the dashboard state for optimistic concurrency."""
        payload = {
            "name": self.name,
            "description": self.description,
            "dataset_id": self.dataset_id,
            "dataset_version_id": self.dataset_version_id,
            "layout": self.layout.model_dump(),
            "components": [c.model_dump(exclude={"created_at", "updated_at"}) for c in self.components],
            "filters": [f.model_dump() for f in self.filters],
            "variables": self.variables,
            "theme": self.theme.model_dump(),
            "version": self.version,
        }
        raw = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class DashboardVersion(BaseModel):
    version_id: str = Field(default_factory=lambda: f"ver_{uuid.uuid4().hex[:10]}")
    dashboard_id: str
    version_number: int
    snapshot: Dashboard
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "user"
    comment: Optional[str] = None


# ─────────────────────────────────────────────────────────────
# AI / UI Action Model
# ─────────────────────────────────────────────────────────────

class DashboardAction(BaseModel):
    action_id: str = Field(default_factory=lambda: f"act_{uuid.uuid4().hex[:10]}")
    action_type: ActionType
    dashboard_id: str
    target_component_id: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    source_references: List[str] = Field(default_factory=list)
    requires_confirmation: bool = True
    status: str = "pending"  # "pending", "approved", "applied", "rejected"


# ─────────────────────────────────────────────────────────────
# API Request & Response Contracts
# ─────────────────────────────────────────────────────────────

class DashboardCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    dataset_id: str
    dataset_version_id: str = "v1"
    template_id: Optional[str] = None


class DashboardUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    layout: Optional[DashboardLayout] = None
    components: Optional[List[DashboardComponent]] = None
    filters: Optional[List[DashboardFilter]] = None
    variables: Optional[Dict[str, Any]] = None
    theme: Optional[DashboardTheme] = None
    expected_version: Optional[int] = None
    expected_hash: Optional[str] = None


class DashboardDuplicateRequest(BaseModel):
    new_name: Optional[str] = None
    dataset_id: Optional[str] = None
    dataset_version_id: Optional[str] = None


class ComponentCreateRequest(BaseModel):
    type: ComponentType
    title: str = Field(..., min_length=1, max_length=120)
    subtitle: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    position: Optional[ComponentPosition] = None
    size: Optional[ComponentSize] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)
    source: ComponentSource
    result_reference: Optional[Dict[str, Any]] = None
    visualization_reference: Optional[Dict[str, Any]] = None
    filter_bindings: List[str] = Field(default_factory=list)
    refresh_policy: RefreshPolicy = RefreshPolicy.RELOAD


class ComponentUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    subtitle: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    position: Optional[ComponentPosition] = None
    size: Optional[ComponentSize] = None
    configuration: Optional[Dict[str, Any]] = None
    source: Optional[ComponentSource] = None
    filter_bindings: Optional[List[str]] = None
    refresh_policy: Optional[RefreshPolicy] = None
    visibility: Optional[bool] = None


class DashboardFilterValidateRequest(BaseModel):
    filter: DashboardFilter
    dataset_id: str
    dataset_version_id: str


class DashboardFilterValidateResponse(BaseModel):
    valid: bool
    field_exists: bool
    operator_compatible: bool
    message: str
    compatible_component_ids: List[str] = Field(default_factory=list)


class DashboardActionValidateRequest(BaseModel):
    action: DashboardAction


class DashboardActionValidateResponse(BaseModel):
    valid: bool
    action_type: ActionType
    requires_confirmation: bool
    impact_summary: str
    diff_preview: Optional[Dict[str, Any]] = None


class ComponentDataResponse(BaseModel):
    component_id: str
    type: ComponentType
    status: ComponentStatus
    data: Any = None
    is_stale: bool = False
    stale_reason: Optional[str] = None
    requires_recomputation: bool = False
    recomputation_reason: Optional[str] = None
    error_message: Optional[str] = None
    provenance: Optional[ComponentProvenance] = None
    refreshed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DashboardDataResponse(BaseModel):
    dashboard_id: str
    version: int
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    components: Dict[str, ComponentDataResponse] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    stale_components_count: int = 0
