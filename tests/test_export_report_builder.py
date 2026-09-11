"""
Unit tests for Phase 15 Report Builder.
Tests assembling ReportDefinitions from templates and gracefully handling missing analytical results.
"""

import json
import os
import tempfile
import pytest

from backend.app.core.config import settings
from backend.app.engines.exports.models import (
    ReportTemplate,
    ReportSection,
    ReportSectionType,
)
from backend.app.engines.exports.report_builder import ReportBuilder


def test_template_metadata_completeness():
    builder = ReportBuilder()
    for tmpl in [
        ReportTemplate.EXECUTIVE_SUMMARY,
        ReportTemplate.DATA_QUALITY,
        ReportTemplate.EDA_DEEP_DIVE,
        ReportTemplate.ML_EXPERIMENT,
        ReportTemplate.FORECAST_BRIEF,
        ReportTemplate.FULL_ANALYSIS,
        ReportTemplate.CUSTOM,
    ]:
        assert tmpl in builder.TEMPLATE_METADATA
        meta = builder.TEMPLATE_METADATA[tmpl]
        assert "name" in meta
        assert "description" in meta


def test_build_fallback_when_no_data():
    builder = ReportBuilder()
    report = builder.build(
        dataset_id="non_existent_ds",
        version_id="v1",
        template=ReportTemplate.EXECUTIVE_SUMMARY,
    )

    assert report.dataset_id == "non_existent_ds"
    assert report.template == ReportTemplate.EXECUTIVE_SUMMARY
    assert len(report.sections) >= 1
    assert report.sections[0].title == "No Data Available"


def test_build_custom_template():
    builder = ReportBuilder()
    custom_sec = ReportSection(
        title="Custom Findings",
        content_type=ReportSectionType.MARKDOWN,
        content={"markdown": "Custom narrative content."},
        order=0,
    )
    report = builder.build(
        dataset_id="ds_custom",
        version_id="v1",
        template=ReportTemplate.CUSTOM,
        title="Custom Audit",
        custom_sections=[custom_sec],
    )

    assert report.title == "Custom Audit"
    assert len(report.sections) == 1
    assert report.sections[0].title == "Custom Findings"


def test_build_with_profile_data(monkeypatch):
    builder = ReportBuilder()
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(settings, "DATA_PROFILES_DIR", tmpdir)

        dataset_id = "ds_sales"
        ds_prof_dir = os.path.join(tmpdir, dataset_id)
        os.makedirs(ds_prof_dir, exist_ok=True)

        prof = {
            "dataset_id": dataset_id,
            "row_count": 1000,
            "column_count": 5,
            "columns": [{"name": "col_1", "dtype": "Int64", "null_count": 0}],
        }
        with open(os.path.join(ds_prof_dir, "v1.json"), "w", encoding="utf-8") as f:
            json.dump(prof, f)

        report = builder.build(
            dataset_id=dataset_id,
            version_id="v1",
            template=ReportTemplate.EXECUTIVE_SUMMARY,
            title="Sales Overview",
        )

        assert report.title == "Sales Overview"
        # Profile overview section should be populated
        assert any("Profile" in s.title or "Overview" in s.title for s in report.sections)
