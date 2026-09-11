from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class QuantilesSummary(BaseModel):
    """Continuous statistical quantiles for numerical distributions."""

    p0: Optional[float] = Field(None, description="Minimum value (0th percentile)")
    p5: Optional[float] = Field(None, description="5th percentile")
    p25: Optional[float] = Field(None, description="25th percentile (1st quartile)")
    p50: Optional[float] = Field(None, description="50th percentile (median)")
    p75: Optional[float] = Field(None, description="75th percentile (3rd quartile)")
    p95: Optional[float] = Field(None, description="95th percentile")
    p100: Optional[float] = Field(None, description="Maximum value (100th percentile)")
    iqr: Optional[float] = Field(None, description="Interquartile Range (P75 - P25)")


class NumericMetrics(BaseModel):
    """Detailed summary statistics for numerical columns."""

    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    stddev: Optional[float] = None
    variance: Optional[float] = None
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None
    quantiles: Optional[QuantilesSummary] = None


class CategoryFrequency(BaseModel):
    """Category frequency record for categorical inspection."""

    value: Any = Field(..., description="Category label")
    count: int = Field(..., description="Occurrence count")
    percentage: float = Field(..., description="Share percentage of total non-null values (0-100)")


class CategoricalMetrics(BaseModel):
    """Summary metrics for string, categorical, and text columns."""

    top_categories: List[CategoryFrequency] = Field(default_factory=list)
    avg_length: Optional[float] = Field(None, description="Average string character length")
    max_length: Optional[int] = Field(None, description="Maximum string character length")
    is_text: bool = Field(False, description="True if column is detected as unstructured long-form text")


class DatetimeMetrics(BaseModel):
    """Summary metrics for date, datetime, and temporal columns."""

    min_timestamp: Optional[str] = None
    max_timestamp: Optional[str] = None
    span_days: Optional[float] = None
    distinct_dates_count: Optional[int] = None
    detected_frequency: Optional[str] = Field(
        None, description="Inferred time frequency: hourly, daily, weekly, monthly, quarterly, yearly, irregular"
    )


class TargetCandidate(BaseModel):
    """Machine learning target variable recommendation."""

    column_name: str
    task_type: str = Field(..., description="binary_classification, multiclass_classification, or regression")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0")
    reason: str = Field(..., description="Human-readable explanation of why this column is a suitable target")


class ColumnProfile(BaseModel):
    """Comprehensive single-column structural and statistical profile."""

    name: str = Field(..., description="Column identifier")
    physical_type: str = Field(..., description="Physical storage type (e.g. integer, float, string, datetime)")
    semantic_type: str = Field(..., description="Inferred semantic role (e.g. monetary, percentage, identifier, categorical)")
    semantic_confidence: float = Field(1.0, description="Confidence score of semantic inference (0.0 to 1.0)")
    nullable: bool = True
    null_count: int = 0
    null_percentage: float = 0.0
    unique_count: int = 0
    unique_percentage: float = 0.0
    cardinality_ratio: float = 0.0
    sample_values: List[Any] = Field(default_factory=list, description="Small representative sample (max 5)")
    
    # Type-specific metric blocks (None if not applicable)
    numeric_metrics: Optional[NumericMetrics] = None
    categorical_metrics: Optional[CategoricalMetrics] = None
    datetime_metrics: Optional[DatetimeMetrics] = None

    # Semantic flags
    is_identifier_candidate: bool = False
    identifier_confidence: float = 0.0
    target_candidate: Optional[TargetCandidate] = None


class DatasetProfileResponse(BaseModel):
    """Top-level dataset structural intelligence and column profiles."""

    model_config = ConfigDict(from_attributes=True)

    dataset_id: str
    row_count: int
    column_count: int
    columns: List[ColumnProfile]
    
    # Dataset-level summaries
    numeric_columns_count: int
    categorical_columns_count: int
    datetime_columns_count: int
    identifier_columns_count: int
    target_candidates: List[TargetCandidate] = Field(default_factory=list)
    
    profiling_version: str = "profile_v1"
    status: str = Field("READY", description="Profile status: NOT_STARTED, PROFILING, READY, FAILED")
    generated_at: str
    error_message: Optional[str] = None
