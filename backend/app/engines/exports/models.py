"""
Domain Models for Phase 15 Advanced Export, Reporting & Presentation Engine.
Defines ExportJob, ExportRequest, ReportDefinition, and related contracts.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class ExportFormat(str, Enum):
    CSV = "CSV"
    JSON = "JSON"
    XLSX = "XLSX"
    HTML_REPORT = "HTML_REPORT"
    MARKDOWN_REPORT = "MARKDOWN_REPORT"


class ExportSourceType(str, Enum):
    DATASET = "DATASET"
    SQL_RESULT = "SQL_RESULT"
    PROFILE = "PROFILE"
    QUALITY_REPORT = "QUALITY_REPORT"
    EDA_RESULT = "EDA_RESULT"
    VISUALIZATION_DATA = "VISUALIZATION_DATA"
    STATISTICS_RESULT = "STATISTICS_RESULT"
    ML_RESULT = "ML_RESULT"
    FORECAST_RESULT = "FORECAST_RESULT"
    DASHBOARD = "DASHBOARD"
    AI_ANALYST_SESSION = "AI_ANALYST_SESSION"


class ExportStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class ReportTemplate(str, Enum):
    EXECUTIVE_SUMMARY = "EXECUTIVE_SUMMARY"
    DATA_QUALITY = "DATA_QUALITY"
    EDA_DEEP_DIVE = "EDA_DEEP_DIVE"
    ML_EXPERIMENT = "ML_EXPERIMENT"
    FORECAST_BRIEF = "FORECAST_BRIEF"
    FULL_ANALYSIS = "FULL_ANALYSIS"
    CUSTOM = "CUSTOM"


class ReportSectionType(str, Enum):
    MARKDOWN = "MARKDOWN"
    TABLE = "TABLE"
    KPI_GRID = "KPI_GRID"
    STATISTICS_SUMMARY = "STATISTICS_SUMMARY"
    ML_METRICS = "ML_METRICS"
    FORECAST_HORIZON = "FORECAST_HORIZON"
    CHART_REF = "CHART_REF"


# ─────────────────────────────────────────────────────────────
# Export Provenance
# ─────────────────────────────────────────────────────────────

class ExportProvenance(BaseModel):
    """Provenance metadata attached to every export artifact."""
    dataset_id: str
    dataset_version_id: str
    source_engine: Optional[str] = None
    source_result_id: Optional[str] = None
    is_stale: bool = False
    stale_reason: Optional[str] = None
    exported_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    platform_version: str = "analyzax_v1"


# ─────────────────────────────────────────────────────────────
# Export Job
# ─────────────────────────────────────────────────────────────

class ExportJob(BaseModel):
    """Tracks an export job lifecycle from creation to completion."""
    job_id: str = Field(default_factory=lambda: f"exp_{uuid.uuid4().hex[:12]}")
    dataset_id: str
    version_id: str
    source_type: ExportSourceType
    source_id: Optional[str] = None
    format: ExportFormat
    status: ExportStatus = ExportStatus.PENDING
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    row_count: Optional[int] = None
    content_type: Optional[str] = None
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    provenance: Optional[ExportProvenance] = None
    options: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────
# Export Request
# ─────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    """Request to create a new export artifact."""
    dataset_id: str
    workspace_id: Optional[str] = None
    version_id: Optional[str] = None
    source_type: ExportSourceType
    source_id: Optional[str] = None
    format: ExportFormat
    options: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────
# Report Models
# ─────────────────────────────────────────────────────────────

class ReportSection(BaseModel):
    """A single section within a report."""
    section_id: str = Field(default_factory=lambda: f"sec_{uuid.uuid4().hex[:8]}")
    title: str
    content_type: ReportSectionType
    content: Dict[str, Any] = Field(default_factory=dict)
    order: int = 0


class ReportDefinition(BaseModel):
    """Full report definition with metadata and ordered sections."""
    report_id: str = Field(default_factory=lambda: f"rpt_{uuid.uuid4().hex[:12]}")
    dataset_id: str
    version_id: str
    title: str = "Analysis Report"
    subtitle: Optional[str] = None
    template: ReportTemplate = ReportTemplate.EXECUTIVE_SUMMARY
    sections: List[ReportSection] = Field(default_factory=list)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    provenance: Optional[ExportProvenance] = None


class ReportGenerateRequest(BaseModel):
    """Request to generate a report from a template."""
    dataset_id: str
    version_id: Optional[str] = None
    template: ReportTemplate = ReportTemplate.EXECUTIVE_SUMMARY
    title: Optional[str] = None
    subtitle: Optional[str] = None
    sections: Optional[List[ReportSection]] = None
    format: ExportFormat = ExportFormat.HTML_REPORT


# ─────────────────────────────────────────────────────────────
# Source Data Container
# ─────────────────────────────────────────────────────────────

class ExportSourceData(BaseModel):
    """Standardized container for data read from analytical engines."""
    data: Any  # list[dict] for tabular, dict for structured results
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance: ExportProvenance
    row_count: Optional[int] = None
    columns: Optional[List[str]] = None


# ─────────────────────────────────────────────────────────────
# Content Type Mapping
# ─────────────────────────────────────────────────────────────

EXPORT_CONTENT_TYPES: Dict[ExportFormat, str] = {
    ExportFormat.CSV: "text/csv",
    ExportFormat.JSON: "application/json",
    ExportFormat.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ExportFormat.HTML_REPORT: "text/html",
    ExportFormat.MARKDOWN_REPORT: "text/markdown",
}

EXPORT_FILE_EXTENSIONS: Dict[ExportFormat, str] = {
    ExportFormat.CSV: ".csv",
    ExportFormat.JSON: ".json",
    ExportFormat.XLSX: ".xlsx",
    ExportFormat.HTML_REPORT: ".html",
    ExportFormat.MARKDOWN_REPORT: ".md",
}
