"""
AnalyzaX — Phase 7: Exploratory Data Analysis (EDA) Domain Models
Defines all strongly-typed schemas for statistics, distributions, correlations,
relationships, temporal trends, automated findings, and ChartSpecs.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class FindingCategory(str, Enum):
    DISTRIBUTION = "DISTRIBUTION"
    RELATIONSHIP = "RELATIONSHIP"
    MISSINGNESS = "MISSINGNESS"
    ANOMALY = "ANOMALY"
    CATEGORY = "CATEGORY"
    TIME = "TIME"
    CARDINALITY = "CARDINALITY"
    DATA_HEALTH = "DATA_HEALTH"


class FindingSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class FindingConfidence(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CardinalityClass(str, Enum):
    CONSTANT = "CONSTANT"
    VERY_LOW = "VERY_LOW"       # 2-5 unique
    LOW = "LOW"                 # 6-20 unique
    MEDIUM = "MEDIUM"           # 21-100 unique
    HIGH = "HIGH"               # >100 unique, <90% ratio
    UNIQUE = "UNIQUE"           # >=90% ratio, identifier candidate


class CorrelationMethod(str, Enum):
    PEARSON = "pearson"
    SPEARMAN = "spearman"


class ChartType(str, Enum):
    HISTOGRAM = "histogram"
    BOX = "box"
    SCATTER = "scatter"
    LINE = "line"
    AREA = "area"
    BAR = "bar"
    GROUPED_BAR = "grouped_bar"
    STACKED_BAR = "stacked_bar"
    HEATMAP = "heatmap"


# ─────────────────────────────────────────────────────────────
# Chart Specification Models
# ─────────────────────────────────────────────────────────────

class ChartSamplingMetadata(BaseModel):
    is_sampled: bool = False
    original_row_count: int
    displayed_points: int
    sampling_method: str = "deterministic"


class ChartOptions(BaseModel):
    show_legend: bool = True
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    color_palette: Optional[str] = None
    bin_count: Optional[int] = None
    bin_method: Optional[str] = None


class ChartSpec(BaseModel):
    """
    Standard visualization specification produced deterministically by the EDA engine.
    Consumed directly by frontend presentation components.
    """
    chart_id: str
    chart_type: ChartType
    title: str
    description: Optional[str] = None
    dataset_id: str
    version_id: str
    x: str
    y: Optional[str] = None
    series: Optional[str] = None
    aggregation: Optional[str] = None
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Aggregated or sampled chart records")
    options: ChartOptions = Field(default_factory=ChartOptions)
    sampling: Optional[ChartSamplingMetadata] = None


# ─────────────────────────────────────────────────────────────
# Univariate Statistics Models
# ─────────────────────────────────────────────────────────────

class HistogramBin(BaseModel):
    bin_start: float
    bin_end: float
    count: int
    percentage: float


class HistogramData(BaseModel):
    bins: List[HistogramBin]
    bin_count: int
    bin_method: str
    min_value: float
    max_value: float


class BoxPlotData(BaseModel):
    min: float
    q1: float
    median: float
    q3: float
    max: float
    iqr: float
    outlier_points: List[float] = Field(default_factory=list)


class UnivariateNumeric(BaseModel):
    column: str
    count: int
    null_count: int
    null_percentage: float
    unique_count: int
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    stddev: Optional[float] = None
    variance: Optional[float] = None
    range: Optional[float] = None
    q1: Optional[float] = None
    q3: Optional[float] = None
    iqr: Optional[float] = None
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None
    coefficient_of_variation: Optional[float] = None
    zero_count: int = 0
    negative_count: int = 0
    positive_count: int = 0
    distribution_shape: str = "normal"  # "normal", "right_skewed", "left_skewed", "bimodal", "constant"
    histogram: Optional[HistogramData] = None
    box_plot: Optional[BoxPlotData] = None


class CategoryFrequencyItem(BaseModel):
    category: str
    count: int
    percentage: float


class UnivariateCategorical(BaseModel):
    column: str
    count: int
    null_count: int
    null_percentage: float
    unique_count: int
    cardinality_class: CardinalityClass
    top_categories: List[CategoryFrequencyItem] = Field(default_factory=list)
    other_count: int = 0
    other_percentage: float = 0.0
    rare_categories_count: int = 0
    dominant_category_percentage: float = 0.0


class TimeSeriesPoint(BaseModel):
    period: str
    timestamp: str
    count: int
    sum: Optional[float] = None
    mean: Optional[float] = None


class DatetimeAnalysis(BaseModel):
    column: str
    count: int
    null_count: int
    null_percentage: float
    unique_count: int
    min_timestamp: Optional[str] = None
    max_timestamp: Optional[str] = None
    span_days: Optional[float] = None
    inferred_frequency: str = "irregular"  # "daily", "weekly", "monthly", "yearly", "irregular"
    temporal_trends: List[TimeSeriesPoint] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# Correlation & Bivariate Models
# ─────────────────────────────────────────────────────────────

class RankedCorrelationPair(BaseModel):
    column_x: str
    column_y: str
    correlation: float
    abs_correlation: float
    strength: str  # "very_strong", "strong", "moderate", "weak", "negligible"
    method: CorrelationMethod = CorrelationMethod.PEARSON


class CorrelationMatrix(BaseModel):
    method: CorrelationMethod
    columns: List[str]
    matrix: List[List[Optional[float]]]
    ranked_pairs: List[RankedCorrelationPair] = Field(default_factory=list)


class ScatterPoint(BaseModel):
    x: float
    y: float


class RegressionLine(BaseModel):
    slope: float
    intercept: float
    r_squared: float


class NumericNumericRelationship(BaseModel):
    column_x: str
    column_y: str
    correlation: float
    regression: Optional[RegressionLine] = None
    sample_points: List[ScatterPoint] = Field(default_factory=list)
    sampling: Optional[ChartSamplingMetadata] = None


class CategoryGroupStats(BaseModel):
    category: str
    count: int
    mean: float
    median: float
    stddev: Optional[float] = None
    min: float
    max: float
    q1: float
    q3: float


class NumericCategoricalRelationship(BaseModel):
    numeric_column: str
    categorical_column: str
    group_stats: List[CategoryGroupStats] = Field(default_factory=list)
    variance_across_groups: Optional[float] = None


class CategoricalCategoricalRelationship(BaseModel):
    column_x: str
    column_y: str
    categories_x: List[str]
    categories_y: List[str]
    contingency_matrix: List[List[int]]
    cramers_v: Optional[float] = None


# ─────────────────────────────────────────────────────────────
# Missingness & Outliers Models
# ─────────────────────────────────────────────────────────────

class ColumnMissingnessItem(BaseModel):
    column: str
    missing_count: int
    missing_percentage: float


class MissingnessCooccurrence(BaseModel):
    column_a: str
    column_b: str
    both_missing_count: int
    cooccurrence_ratio: float


class MissingnessAnalysis(BaseModel):
    total_cells: int
    total_missing_cells: int
    overall_missing_percentage: float
    complete_rows_count: int
    incomplete_rows_count: int
    column_missingness: List[ColumnMissingnessItem] = Field(default_factory=list)
    cooccurrences: List[MissingnessCooccurrence] = Field(default_factory=list)


class OutlierColumnSummary(BaseModel):
    column: str
    outlier_count: int
    outlier_percentage: float
    lower_bound: float
    upper_bound: float
    method: str = "IQR"
    sample_extreme_values: List[float] = Field(default_factory=list)


class OutlierAnalysis(BaseModel):
    total_outlier_count: int
    columns_with_outliers: List[OutlierColumnSummary] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# Cardinality & Overview Models
# ─────────────────────────────────────────────────────────────

class CardinalityColumnSummary(BaseModel):
    column: str
    unique_count: int
    total_count: int
    cardinality_ratio: float
    cardinality_class: CardinalityClass
    is_identifier_candidate: bool = False


class CardinalityAnalysis(BaseModel):
    columns: List[CardinalityColumnSummary] = Field(default_factory=list)
    constant_columns: List[str] = Field(default_factory=list)
    identifier_candidates: List[str] = Field(default_factory=list)


class EDAOverview(BaseModel):
    dataset_id: str
    version_id: str
    row_count: int
    column_count: int
    numeric_columns_count: int
    categorical_columns_count: int
    datetime_columns_count: int
    boolean_columns_count: int
    text_columns_count: int
    identifier_columns_count: int
    total_cells: int
    missing_cells: int
    missing_percentage: float
    duplicate_rows: int
    duplicate_percentage: float
    quality_score: Optional[float] = None
    anomalies_count: int = 0
    storage_size_bytes: Optional[int] = None
    profile_timestamp: Optional[str] = None
    quality_timestamp: Optional[str] = None
    eda_timestamp: str


# ─────────────────────────────────────────────────────────────
# Findings & Plan Models
# ─────────────────────────────────────────────────────────────

class EDAFinding(BaseModel):
    finding_id: str
    category: FindingCategory
    severity: FindingSeverity
    title: str
    description: str
    evidence: str
    columns: List[str] = Field(default_factory=list)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    chart_reference: Optional[str] = None
    confidence: FindingConfidence = FindingConfidence.HIGH
    methodology: str


class EDAPlan(BaseModel):
    dataset_id: str
    version_id: str
    selected_numeric_columns: List[str] = Field(default_factory=list)
    selected_categorical_columns: List[str] = Field(default_factory=list)
    selected_datetime_columns: List[str] = Field(default_factory=list)
    selected_numeric_pairs: List[List[str]] = Field(default_factory=list)
    selected_num_cat_pairs: List[List[str]] = Field(default_factory=list)
    run_correlation: bool = True
    run_missingness: bool = True
    run_outliers: bool = True
    max_scatter_points: int = 1000


# ─────────────────────────────────────────────────────────────
# Root EDA Report
# ─────────────────────────────────────────────────────────────

class EDAReport(BaseModel):
    report_id: str
    dataset_id: str
    version_id: str
    eda_version: str = "eda_v1"
    generated_at: str
    computation_time_ms: float
    overview: EDAOverview
    numeric_analyses: List[UnivariateNumeric] = Field(default_factory=list)
    categorical_analyses: List[UnivariateCategorical] = Field(default_factory=list)
    datetime_analyses: List[DatetimeAnalysis] = Field(default_factory=list)
    correlation: Optional[CorrelationMatrix] = None
    numeric_relationships: List[NumericNumericRelationship] = Field(default_factory=list)
    num_cat_relationships: List[NumericCategoricalRelationship] = Field(default_factory=list)
    cat_cat_relationships: List[CategoricalCategoricalRelationship] = Field(default_factory=list)
    missingness: Optional[MissingnessAnalysis] = None
    outliers: Optional[OutlierAnalysis] = None
    cardinality: Optional[CardinalityAnalysis] = None
    findings: List[EDAFinding] = Field(default_factory=list)
    charts: List[ChartSpec] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# Interactive Query Request / Response Schemas
# ─────────────────────────────────────────────────────────────

class RelationshipQueryRequest(BaseModel):
    column_x: str
    column_y: str
    analysis_type: Optional[str] = None  # auto, numeric_numeric, numeric_categorical, categorical_categorical, datetime_numeric


class RelationshipQueryResponse(BaseModel):
    column_x: str
    column_y: str
    relationship_type: str
    summary: Dict[str, Any]
    chart: Optional[ChartSpec] = None
    findings: List[EDAFinding] = Field(default_factory=list)
