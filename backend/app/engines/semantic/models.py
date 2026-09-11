"""
AnalyzaX — Phase 25: Semantic Intelligence & Metric Governance Models.
Defines versioned, governed metrics, dimensions, entities, semantic relationships,
and calculation contracts.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MetricStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


class AggregationType(str, Enum):
    SUM = "SUM"
    AVG = "AVG"
    COUNT = "COUNT"
    MIN = "MIN"
    MAX = "MAX"
    CUSTOM = "CUSTOM"


class TimeGrain(str, Enum):
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    QUARTER = "QUARTER"
    YEAR = "YEAR"


from datetime import datetime, timezone

class MetricDefinition(BaseModel):
    """Governed analytical metric definition with strict versioning and dependencies."""
    metric_id: str = Field(..., description="Unique identifier (e.g. met_12345)")
    workspace_id: str = Field(..., description="Owning workspace ID")
    project_id: Optional[str] = Field(None, description="Owning project ID if project-scoped")
    dataset_id: Optional[str] = Field(None, description="Default source dataset ID if applicable")
    name: str = Field(..., description="Human-readable business name (e.g. Net Revenue)")
    description: Optional[str] = Field(None, description="Clear business explanation")
    expression: str = Field(..., description="Constrained formula or SQL expression (e.g. SUM(revenue) - SUM(discounts))")
    aggregation: AggregationType = Field(AggregationType.SUM, description="Primary aggregation type")
    unit: Optional[str] = Field(None, description="Unit symbol or label (e.g. USD, %, count)")
    format: Optional[str] = Field("number", description="Formatting style (e.g. currency, percentage, decimal)")
    dimensions: List[str] = Field(default_factory=list, description="Compatible dimension columns (e.g. ['region', 'category'])")
    time_grain: Optional[TimeGrain] = Field(None, description="Default time roll-up grain")
    filters: Optional[str] = Field(None, description="Default pre-filter clause")
    dependencies: List[str] = Field(default_factory=list, description="Referenced columns or nested metric names")
    synonyms: List[str] = Field(default_factory=list, description="Natural language synonyms for AI resolution (e.g. ['sales', 'topline'])")
    owner_id: str = Field("system", description="Author or owner user ID")
    status: MetricStatus = Field(MetricStatus.ACTIVE, description="Lifecycle status")
    version: int = Field(1, description="Sequential version integer")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="ISO 8601 creation timestamp")
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="ISO 8601 modification timestamp")


class MetricVersionRecord(BaseModel):
    """Immutable historical snapshot of a metric definition."""
    version_id: str
    metric_id: str
    version: int
    definition: MetricDefinition
    changed_by: str
    change_reason: Optional[str] = None
    created_at: str

    @property
    def change_summary(self) -> str:
        return self.change_reason or ""

    @property
    def expression(self) -> str:
        return self.definition.expression if self.definition else ""


class DimensionDefinition(BaseModel):
    """Semantic dimension mapping business attributes to dataset columns."""
    dimension_id: str
    workspace_id: str
    name: str
    column_name: str
    data_type: str = "VARCHAR"
    description: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list)


class EntityDefinition(BaseModel):
    """Semantic entity representing a core business object (e.g. Customer, Order, Product)."""
    entity_id: str
    workspace_id: str
    name: str
    primary_key: str
    description: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list)


class SemanticRelationship(BaseModel):
    """Defines relationships between semantic entities."""
    relationship_id: str
    source_entity: str
    target_entity: str
    relationship_type: str = "MANY_TO_ONE"  # ONE_TO_ONE, ONE_TO_MANY, MANY_TO_ONE
    join_condition: str


class SemanticModel(BaseModel):
    """Aggregate semantic model containing all metrics, dimensions, and entities."""
    model_id: str
    workspace_id: str
    project_id: Optional[str] = None
    dataset_id: Optional[str] = None
    version: int = 1
    metrics: List[MetricDefinition] = Field(default_factory=list)
    dimensions: List[DimensionDefinition] = Field(default_factory=list)
    entities: List[EntityDefinition] = Field(default_factory=list)
    relationships: List[SemanticRelationship] = Field(default_factory=list)
    updated_at: str


class MetricCalculationResult(BaseModel):
    """Deterministic output from calculating a governed metric."""
    metric_id: str
    metric_name: str
    value: Optional[float] = None
    formatted_value: Optional[str] = None
    unit: Optional[str] = None
    breakdown: Optional[List[Dict[str, Any]]] = None
    rows_scanned: Optional[int] = None
    sql_executed: Optional[str] = None
    execution_time_ms: float = 0.0

    @property
    def row_count(self) -> int:
        return self.rows_scanned or 0


class MetricValidationResult(BaseModel):
    """Validation response for metric expressions."""
    is_valid: bool
    error_message: Optional[str] = None
    parsed_columns: List[str] = Field(default_factory=list)
    parsed_functions: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    has_cycle: bool = False
