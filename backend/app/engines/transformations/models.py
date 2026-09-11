"""
Transformation & Versioning Domain Models
Defines typed transformations, plans, previews, recommendations, versions, and lineage.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TransformationType(str, Enum):
    # Missing value handling
    FILL_MISSING = "FILL_MISSING"
    DROP_MISSING = "DROP_MISSING"

    # Duplicate handling
    DROP_DUPLICATES = "DROP_DUPLICATES"

    # String & Text normalization
    TRIM_WHITESPACE = "TRIM_WHITESPACE"
    TEXT_CASE = "TEXT_CASE"
    REPLACE_TEXT = "REPLACE_TEXT"

    # Categorical normalization
    NORMALIZE_CATEGORIES = "NORMALIZE_CATEGORIES"

    # Type casting
    CAST_TYPE = "CAST_TYPE"

    # Date handling
    PARSE_DATE = "PARSE_DATE"
    EXTRACT_DATE_PARTS = "EXTRACT_DATE_PARTS"

    # Row filtering
    FILTER_ROWS = "FILTER_ROWS"

    # Column operations
    DROP_COLUMNS = "DROP_COLUMNS"
    RENAME_COLUMN = "RENAME_COLUMN"
    REORDER_COLUMNS = "REORDER_COLUMNS"

    # Derived / Arithmetic
    DERIVED_COLUMN = "DERIVED_COLUMN"

    # Encoding
    ONE_HOT_ENCODE = "ONE_HOT_ENCODE"
    LABEL_ENCODE = "LABEL_ENCODE"

    # Scaling & Outlier handling
    SCALE_NUMERIC = "SCALE_NUMERIC"
    HANDLE_OUTLIERS = "HANDLE_OUTLIERS"


class PlanStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    PREVIEW_READY = "PREVIEW_READY"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class VersionStatus(str, Enum):
    READY = "READY"
    CREATING = "CREATING"
    FAILED = "FAILED"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DatasetVersion(BaseModel):
    """
    Immutable representation of a dataset version in the storage hierarchy.
    """
    version_id: str = Field(description="Stable identifier (e.g. 'v1', 'v2')")
    dataset_id: str = Field(description="Parent dataset identifier")
    version_number: int = Field(ge=1, description="Sequential version index")
    version_label: str = Field(description="Human-readable version title")
    parent_version_id: Optional[str] = Field(default=None, description="Immediate lineage ancestor version ID")
    storage_path: str = Field(description="Parquet storage path on local filesystem")
    duckdb_table_name: str = Field(description="SQL identifier registered in DuckDB analytical engine")
    row_count: int = Field(ge=0)
    column_count: int = Field(ge=0)
    file_size_bytes: int = Field(ge=0)
    schema_hash: str = Field(description="SHA-256 hash of column names and physical types")
    data_hash: str = Field(description="SHA-256 digest of columnar data snapshot")
    pipeline_hash: Optional[str] = Field(default=None, description="SHA-256 digest of transformation sequence")
    status: VersionStatus = Field(default=VersionStatus.READY)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: str = Field(default="user")
    operation_count: int = Field(default=0, ge=0)


class TransformationStep(BaseModel):
    """
    Single discrete transformation step in a pipeline.
    """
    step_id: str = Field(description="Unique step identifier")
    type: TransformationType = Field(description="Class of transformation")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operational parameters")
    input_columns: List[str] = Field(default_factory=list, description="Columns read or transformed")
    output_columns: List[str] = Field(default_factory=list, description="Columns created or modified")
    description: str = Field(description="Human-readable explanation of the operation")
    enabled: bool = Field(default=True, description="Whether this step is active in execution")


class TransformationPlan(BaseModel):
    """
    Ordered sequence of transformation steps forming a clean/transform pipeline.
    """
    plan_id: str = Field(description="Unique transformation plan identifier")
    dataset_id: str = Field(description="Target dataset identifier")
    source_version_id: str = Field(description="Version against which the plan is built")
    steps: List[TransformationStep] = Field(default_factory=list)
    status: PlanStatus = Field(default=PlanStatus.DRAFT)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class StepSummary(BaseModel):
    step_id: str
    type: str
    description: str
    rows_affected: int = 0
    columns_affected: int = 0
    schema_change: Optional[str] = None


class TransformationPreview(BaseModel):
    """
    Sample Before/After execution results without persisting a new version.
    """
    plan_id: str
    source_version_id: str
    sample_before: List[Dict[str, Any]]
    sample_after: List[Dict[str, Any]]
    columns_before: List[str]
    columns_after: List[str]
    rows_before: int
    rows_after: int
    rows_affected: int
    step_summaries: List[StepSummary] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)


class DryRunResult(BaseModel):
    """
    Full validation and impact estimation for a plan before applying.
    """
    valid: bool
    validation_errors: List[str] = Field(default_factory=list)
    source_version_id: str
    estimated_rows: int
    estimated_columns: int
    schema_diff: Dict[str, Any] = Field(default_factory=dict)
    quality_impact_prediction: Dict[str, Any] = Field(default_factory=dict)


class CleaningRecommendation(BaseModel):
    """
    Deterministic cleaning recommendation derived from Phase 5 quality issues.
    """
    recommendation_id: str
    issue_id: Optional[str] = None
    title: str
    description: str
    reason: str
    risk: RiskLevel = RiskLevel.LOW
    confidence: float = 1.0
    suggested_step: TransformationStep


class QualityComparison(BaseModel):
    """
    Before/After differential between two dataset versions.
    """
    before_version_id: str
    after_version_id: str
    before_score: float
    after_score: float
    score_delta: float
    before_grade: str
    after_grade: str
    before_total_issues: int
    after_total_issues: int
    issues_delta: int
    metrics_comparison: Dict[str, Any] = Field(default_factory=dict)
    improvements: List[str] = Field(default_factory=list)
    regressions: List[str] = Field(default_factory=list)


class TransformationAudit(BaseModel):
    """
    Audit record logged whenever a transformation plan is applied.
    """
    audit_id: str
    dataset_id: str
    source_version_id: str
    new_version_id: str
    plan_id: str
    steps_applied: int
    rows_before: int
    rows_after: int
    rows_affected: int
    execution_time_ms: float
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
