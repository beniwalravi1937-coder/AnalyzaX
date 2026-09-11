"""
Unit tests for Phase 15 Export Engine Domain Models.
Validates model creation, default values, enums, serialization, and provenance.
"""

import pytest
from backend.app.engines.exports.models import (
    ExportFormat,
    ExportSourceType,
    ExportStatus,
    ReportTemplate,
    ReportSectionType,
    ExportProvenance,
    ExportJob,
    ExportRequest,
    ReportSection,
    ReportDefinition,
    ReportGenerateRequest,
)


def test_export_enums():
    """Verify all expected enum members exist."""
    assert ExportFormat.CSV == "CSV"
    assert ExportFormat.JSON == "JSON"
    assert ExportFormat.XLSX == "XLSX"
    assert ExportFormat.HTML_REPORT == "HTML_REPORT"
    assert ExportFormat.MARKDOWN_REPORT == "MARKDOWN_REPORT"

    assert ExportSourceType.DATASET == "DATASET"
    assert ExportSourceType.SQL_RESULT == "SQL_RESULT"
    assert ExportSourceType.PROFILE == "PROFILE"
    assert ExportSourceType.QUALITY_REPORT == "QUALITY_REPORT"
    assert ExportSourceType.EDA_RESULT == "EDA_RESULT"
    assert ExportSourceType.DASHBOARD == "DASHBOARD"

    assert ExportStatus.PENDING == "PENDING"
    assert ExportStatus.COMPLETED == "COMPLETED"
    assert ExportStatus.FAILED == "FAILED"

    assert ReportTemplate.EXECUTIVE_SUMMARY == "EXECUTIVE_SUMMARY"
    assert ReportTemplate.FULL_ANALYSIS == "FULL_ANALYSIS"


def test_export_provenance_defaults():
    """Verify ExportProvenance defaults and fields."""
    prov = ExportProvenance(
        dataset_id="ds_123",
        dataset_version_id="v1",
        source_engine="duckdb",
        is_stale=False,
    )
    assert prov.dataset_id == "ds_123"
    assert prov.dataset_version_id == "v1"
    assert prov.source_engine == "duckdb"
    assert not prov.is_stale
    assert prov.platform_version == "analyzax_v1"
    assert prov.exported_at is not None


def test_export_job_defaults():
    """Verify ExportJob initializes with UUID, timestamp, and default status."""
    job = ExportJob(
        dataset_id="ds_test",
        version_id="v1",
        source_type=ExportSourceType.DATASET,
        format=ExportFormat.CSV,
    )
    assert job.job_id.startswith("exp_")
    assert job.dataset_id == "ds_test"
    assert job.version_id == "v1"
    assert job.source_type == ExportSourceType.DATASET
    assert job.format == ExportFormat.CSV
    assert job.status == ExportStatus.PENDING
    assert job.created_at is not None
    assert job.options == {}


def test_report_definition_and_sections():
    """Verify ReportDefinition and ReportSection hierarchy."""
    sec1 = ReportSection(
        title="Dataset Overview",
        content_type=ReportSectionType.KPI_GRID,
        content={"cards": [{"label": "Total Rows", "value": 1000}]},
        order=0,
    )
    sec2 = ReportSection(
        title="Executive Summary",
        content_type=ReportSectionType.MARKDOWN,
        content={"markdown": "# Overview\nData looks great."},
        order=1,
    )

    report = ReportDefinition(
        dataset_id="ds_test",
        version_id="v1",
        title="Quarterly Review",
        template=ReportTemplate.EXECUTIVE_SUMMARY,
        sections=[sec1, sec2],
    )

    assert report.report_id.startswith("rpt_")
    assert len(report.sections) == 2
    assert report.sections[0].title == "Dataset Overview"
    assert report.sections[1].title == "Executive Summary"
    assert report.template == ReportTemplate.EXECUTIVE_SUMMARY
