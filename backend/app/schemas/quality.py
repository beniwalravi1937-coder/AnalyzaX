"""
Data Quality API Schemas
Pydantic schemas for quality evaluation requests and responses.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from backend.app.engines.quality.models import (
    ColumnQualitySummary,
    Dimension,
    DimensionScore,
    QualityIssue,
    Severity,
)


class DataQualityReportResponse(BaseModel):
    """
    Standard response payload for Data Quality reports.
    """
    dataset_id: str
    dataset_version: str
    quality_report_version: str
    status: str
    overall_score: float
    overall_grade: str
    dimension_scores: Dict[Dimension, DimensionScore]
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    info_issues: int
    affected_rows: int
    affected_columns: int
    issues: List[QualityIssue]
    column_summaries: List[ColumnQualitySummary]
    execution_time_ms: float
    scoring_explanation: str
    generated_at: str
