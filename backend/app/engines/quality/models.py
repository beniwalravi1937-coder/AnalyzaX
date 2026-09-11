"""
Data Quality Engine Models
Defines domain models, enums, issue taxonomies, and report structures.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Dimension(str, Enum):
    COMPLETENESS = "COMPLETENESS"
    UNIQUENESS = "UNIQUENESS"
    VALIDITY = "VALIDITY"
    CONSISTENCY = "CONSISTENCY"
    INTEGRITY = "INTEGRITY"
    ANOMALY_RISK = "ANOMALY_RISK"


class IssueType(str, Enum):
    MISSING_VALUES = "MISSING_VALUES"
    HIGH_MISSINGNESS = "HIGH_MISSINGNESS"
    CRITICAL_MISSINGNESS = "CRITICAL_MISSINGNESS"
    EMPTY_COLUMN = "EMPTY_COLUMN"
    EMPTY_ROW = "EMPTY_ROW"
    BLANK_STRINGS = "BLANK_STRINGS"
    DUPLICATES = "DUPLICATES"
    DUPLICATE_IDENTIFIER = "DUPLICATE_IDENTIFIER"
    NULL_IDENTIFIER = "NULL_IDENTIFIER"
    CONSTANT_COLUMN = "CONSTANT_COLUMN"
    NEAR_CONSTANT_COLUMN = "NEAR_CONSTANT_COLUMN"
    INVALID_TYPE = "INVALID_TYPE"
    TYPE_INCONSISTENCY = "TYPE_INCONSISTENCY"
    INVALID_DATE = "INVALID_DATE"
    INVALID_NUMERIC = "INVALID_NUMERIC"
    INVALID_RANGE = "INVALID_RANGE"
    NEGATIVE_VALUE = "NEGATIVE_VALUE"
    CATEGORY_INCONSISTENCY = "CATEGORY_INCONSISTENCY"
    WHITESPACE_INCONSISTENCY = "WHITESPACE_INCONSISTENCY"
    INVALID_FORMAT = "INVALID_FORMAT"
    OUTLIER_RISK = "OUTLIER_RISK"
    HIGH_CARDINALITY = "HIGH_CARDINALITY"
    SUSPICIOUS_PATTERN = "SUSPICIOUS_PATTERN"


class QualityIssue(BaseModel):
    """
    Standardized quality issue descriptor.
    Every issue is deterministic, traceable, and includes recommended action for Phase 6.
    """
    issue_id: str = Field(description="Unique deterministic ID of this quality issue")
    dataset_id: str = Field(description="Target dataset identifier")
    dataset_version: str = Field(default="v1", description="Dataset version evaluated")
    issue_type: IssueType = Field(description="Taxonomy classification of the issue")
    dimension: Dimension = Field(description="Quality dimension evaluated")
    severity: Severity = Field(description="Impact severity rating")
    column_name: Optional[str] = Field(default=None, description="Column affected, or null if dataset-wide")
    affected_rows: int = Field(default=0, ge=0, description="Count of rows affected by this issue")
    affected_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Percentage of dataset rows affected")
    description: str = Field(description="Human-readable explanation of why this was flagged")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Deterministic metrics/samples backing the flag")
    rule_id: str = Field(description="ID of the rule that produced this issue")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Detection confidence score")
    recommended_action: str = Field(description="Non-destructive proposed cleaning action for Phase 6")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp when this issue was detected",
    )


class DimensionScore(BaseModel):
    """
    Scorecard for an individual quality dimension (0.0 - 100.0).
    """
    dimension: Dimension
    score: float = Field(ge=0.0, le=100.0, description="Deterministic score 0-100")
    issue_count: int = Field(default=0, ge=0)
    critical_count: int = Field(default=0, ge=0)
    high_count: int = Field(default=0, ge=0)
    medium_count: int = Field(default=0, ge=0)
    low_count: int = Field(default=0, ge=0)
    info_count: int = Field(default=0, ge=0)
    description: str = Field(description="Summary interpretation of this dimension")


class ColumnQualitySummary(BaseModel):
    """
    Column-level quality evaluation summary.
    """
    column_name: str
    physical_type: str
    semantic_type: str
    quality_score: float = Field(ge=0.0, le=100.0, description="Column quality score 0-100")
    null_percentage: float = Field(ge=0.0, le=100.0)
    unique_percentage: float = Field(ge=0.0, le=100.0)
    issues_count: int = Field(default=0, ge=0)
    highest_severity: Optional[Severity] = None
    issue_types: List[str] = Field(default_factory=list)


class DataQualityReport(BaseModel):
    """
    Complete persistent Data Quality Report.
    """
    dataset_id: str
    dataset_version: str = "v1"
    quality_report_version: str = "quality_v1"
    status: str = "READY"
    overall_score: float = Field(ge=0.0, le=100.0, description="Overall dataset health score 0-100")
    overall_grade: str = Field(description="Textual rating: EXCELLENT, GOOD, FAIR, POOR, CRITICAL")
    dimension_scores: Dict[Dimension, DimensionScore]
    total_issues: int = Field(ge=0)
    critical_issues: int = Field(ge=0)
    high_issues: int = Field(ge=0)
    medium_issues: int = Field(ge=0)
    low_issues: int = Field(ge=0)
    info_issues: int = Field(ge=0)
    affected_rows: int = Field(ge=0, description="Distinct count of rows affected across all issues")
    affected_columns: int = Field(ge=0, description="Count of columns with at least one issue")
    issues: List[QualityIssue] = Field(default_factory=list)
    column_summaries: List[ColumnQualitySummary] = Field(default_factory=list)
    execution_time_ms: float = Field(ge=0.0)
    scoring_explanation: str
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC generation timestamp",
    )
