"""
Phase 9: Advanced Visualization & Visualization Intelligence Engine
Domain models, ChartSpec contract, recommendations, filters, and persistence schemas.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ChartType(str, Enum):
    # Distribution
    HISTOGRAM = "histogram"
    BOX = "box"
    VIOLIN = "violin"
    ECDF = "ecdf"
    DENSITY = "density"

    # Categorical
    BAR = "bar"
    HORIZONTAL_BAR = "horizontal_bar"
    GROUPED_BAR = "grouped_bar"
    STACKED_BAR = "stacked_bar"
    PERCENT_STACKED_BAR = "percent_stacked_bar"
    PARETO = "pareto"

    # Relationship
    SCATTER = "scatter"
    BUBBLE = "bubble"
    HEATMAP = "heatmap"
    CORRELATION_MATRIX = "correlation_matrix"

    # Temporal
    LINE = "line"
    MULTI_LINE = "multi_line"
    AREA = "area"
    STACKED_AREA = "stacked_area"
    TIME_BAR = "time_bar"

    # Composition
    DONUT = "donut"
    PIE = "pie"
    TREEMAP = "treemap"

    # Specialized & Tier 2/3
    KPI = "kpi"
    TABLE = "table"
    FUNNEL = "funnel"
    WATERFALL = "waterfall"
    LOLLIPOP = "lollipop"
    DOT_PLOT = "dot_plot"
    RIDGELINE = "ridgeline"
    GEOGRAPHIC_MAP = "geographic_map"
    CHOROPLETH = "choropleth"
    SANKEY = "sankey"
    RADAR = "radar"
    CANDLESTICK = "candlestick"
    GANTT = "gantt"
    PARALLEL_COORDINATES = "parallel_coordinates"


class AggregationType(str, Enum):
    SUM = "sum"
    AVG = "avg"
    MEDIAN = "median"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    COUNT_DISTINCT = "count_distinct"
    NONE = "none"


class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"


class SortBy(str, Enum):
    VALUE = "value"
    CATEGORY = "category"
    CHRONOLOGICAL = "chronological"


class VisualizationIntent(str, Enum):
    DISTRIBUTION = "distribution"
    COMPARISON = "comparison"
    TREND = "trend"
    RELATIONSHIP = "relationship"
    COMPOSITION = "composition"
    RANKING = "ranking"
    CORRELATION = "correlation"
    SUMMARY = "summary"


class StructuredFilter(BaseModel):
    """
    Safe structured filter model.
    Prevents arbitrary JavaScript expression injection.
    """
    field: str
    operator: str = Field(
        ...,
        description=(
            "equals, not_equals, in, not_in, greater_than, greater_than_or_equal, "
            "less_than, less_than_or_equal, between, contains, starts_with, is_null, is_not_null"
        ),
    )
    value: Any = None
    value2: Optional[Any] = None  # For 'between' operator


class ChartEncoding(BaseModel):
    field: str
    semantic_role: Optional[str] = None  # "dimension", "measure", "series", "temporal"
    data_type: Optional[str] = None      # "numeric", "categorical", "datetime"
    aggregation: Optional[AggregationType] = None
    sort: Optional[SortDirection] = None
    formatting: Optional[str] = None     # "currency", "percentage", "compact", "integer"


class ChartTopNConfig(BaseModel):
    n: int = 10
    include_other: bool = True
    other_label: str = "Other"


class ChartAxesConfig(BaseModel):
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    x_rotate: Optional[int] = None
    y_min: Optional[float] = None
    y_max: Optional[float] = None
    log_scale: bool = False
    zero_baseline: bool = True
    show_grid: bool = True


class ChartLegendConfig(BaseModel):
    show: bool = True
    position: str = "top"  # "top", "bottom", "left", "right"


class ChartAnnotation(BaseModel):
    type: str = "reference_line"  # "reference_line", "threshold", "marker"
    value: float
    axis: str = "y"               # "x" or "y"
    label: Optional[str] = None
    color: Optional[str] = None


class ChartInteractions(BaseModel):
    zoom: bool = True
    pan: bool = True
    brush: bool = False
    crossfilter_enabled: bool = True


class ChartSamplingMetadata(BaseModel):
    is_sampled: bool = False
    original_row_count: int
    displayed_points: int
    sampling_method: str = "exact"  # "exact", "uniform", "reservoir", "lttb", "top_n", "aggregation"


class VisualizationProvenance(BaseModel):
    dataset_id: str
    dataset_version_id: str
    source_type: str = "dataset"    # "dataset", "sql", "eda", "manual"
    source_reference: Optional[str] = None
    created_at: str
    created_by: str = "analyst"


class ChartSpec(BaseModel):
    """
    Central, versioned visualization specification for AnalyzaX.
    Strictly typed, deterministic, and safe for client consumption.
    """
    spec_version: str = "v1"
    chart_id: str
    chart_type: Union[ChartType, str]
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None

    # Dataset version binding
    dataset_id: str
    dataset_version_id: str
    source_type: str = "dataset"
    source_reference: Optional[str] = None

    # Visual Encodings
    x: Optional[str] = None
    y: Optional[str] = None
    series: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    tooltip: Optional[List[str]] = None
    encoding_details: Dict[str, ChartEncoding] = Field(default_factory=dict)

    # Operations & Pipeline
    filters: List[StructuredFilter] = Field(default_factory=list)
    sort_direction: Optional[SortDirection] = None
    sort_by: Optional[SortBy] = None
    aggregation: Optional[str] = None
    top_n: Optional[ChartTopNConfig] = None

    # Styling & Axes
    formatting: Dict[str, str] = Field(default_factory=dict)
    axes: ChartAxesConfig = Field(default_factory=ChartAxesConfig)
    legend: ChartLegendConfig = Field(default_factory=ChartLegendConfig)
    annotations: List[ChartAnnotation] = Field(default_factory=list)
    interactions: ChartInteractions = Field(default_factory=ChartInteractions)

    # Hydrated Data Payload
    data: List[Dict[str, Any]] = Field(default_factory=list)
    sampling: Optional[ChartSamplingMetadata] = None
    provenance: Optional[VisualizationProvenance] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Backward compatibility with Phase 7/8 EDA specs
    options: Optional[Any] = None


class VisualizationRecommendation(BaseModel):
    """
    Deterministic chart recommendation generated from dataset profiles,
    cardinality, distributions, quality metrics, and analytical intent.
    """
    recommendation_id: str
    chart_type: ChartType
    title: str
    reason: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    x_field: Optional[str] = None
    y_field: Optional[str] = None
    series_field: Optional[str] = None
    color_field: Optional[str] = None
    aggregation: Optional[str] = None
    sorting: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    required_fields: List[str] = Field(default_factory=list)
    optional_fields: List[str] = Field(default_factory=list)
    priority: int = 1
    tier: int = 1
    intent: Optional[str] = None


class SavedVisualization(BaseModel):
    """
    Persisted visualization bound to dataset version provenance.
    """
    visualization_id: str
    name: str
    description: Optional[str] = None
    dataset_id: str
    dataset_version_id: str
    chart_spec: ChartSpec
    source_reference: Optional[str] = None
    created_at: str
    updated_at: str
    created_by: str = "analyst"


class VisualizationHistoryEntry(BaseModel):
    id: str
    visualization_id: str
    action: str  # "created", "updated", "viewed", "exported"
    dataset_id: str
    dataset_version_id: str
    chart_type: str
    timestamp: str


class ValidationErrorItem(BaseModel):
    code: str
    message: str
    field: Optional[str] = None
    severity: str = "error"
    suggested_fix: Optional[str] = None


class ValidationWarningItem(BaseModel):
    code: str
    message: str
    field: Optional[str] = None
    suggested_fix: Optional[str] = None


class VisualizationValidationResult(BaseModel):
    is_valid: bool
    errors: List[ValidationErrorItem] = Field(default_factory=list)
    warnings: List[ValidationWarningItem] = Field(default_factory=list)
    is_compatible: bool = True
    incompatibility_reason: Optional[str] = None
