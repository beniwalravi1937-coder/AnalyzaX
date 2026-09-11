"""
Unit tests for Phase 15 Export Renderers.
Tests CSV, JSON, XLSX, HTML Report, and Markdown Report renderers.
"""

import os
import tempfile
import pytest

from backend.app.engines.exports.models import (
    ExportProvenance,
    ExportSourceData,
)
from backend.app.engines.exports.renderers import (
    CsvRenderer,
    JsonRenderer,
    XlsxRenderer,
    HtmlReportRenderer,
    MarkdownReportRenderer,
    get_renderer,
)


@pytest.fixture
def sample_source_data():
    return ExportSourceData(
        data=[
            {"id": 1, "name": "Alice", "score": 95.5},
            {"id": 2, "name": "Bob", "score": 82.0},
            {"id": 3, "name": "Charlie", "score": 91.2},
        ],
        metadata={"source": "test_dataset"},
        provenance=ExportProvenance(
            dataset_id="ds_123",
            dataset_version_id="v1",
            source_engine="duckdb",
            is_stale=False,
        ),
        row_count=3,
        columns=["id", "name", "score"],
    )


def test_csv_renderer(sample_source_data):
    renderer = CsvRenderer()
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, "test.csv")
        path, size, rows = renderer.render(sample_source_data, out_file)

        assert os.path.exists(path)
        assert size > 0
        assert rows == 3

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Alice" in content
            assert "score" in content


def test_json_renderer(sample_source_data):
    renderer = JsonRenderer()
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, "test.json")
        path, size, rows = renderer.render(sample_source_data, out_file)

        assert os.path.exists(path)
        assert size > 0
        assert rows == 3

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            assert '"Alice"' in content

    # Also test full orient with provenance
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, "test_full.json")
        path, size, rows = renderer.render(
            sample_source_data, out_file, options={"orient": "full"}
        )
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            assert '"data"' in content
            assert '"provenance"' in content


def test_xlsx_renderer(sample_source_data):
    renderer = XlsxRenderer()
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, "test.xlsx")
        path, size, rows = renderer.render(sample_source_data, out_file)

        assert os.path.exists(path)
        assert size > 0
        assert rows == 3


def test_html_report_renderer():
    renderer = HtmlReportRenderer()
    report_dict = {
        "title": "Executive Performance Summary",
        "subtitle": "Q3 Analytical Findings",
        "dataset_id": "ds_sales_2026",
        "sections": [
            {
                "title": "Key Metrics",
                "content_type": "KPI_GRID",
                "content": {
                    "cards": [
                        {"label": "Revenue", "value": "$1,200,000"},
                        {"label": "Retention", "value": "94.2%"},
                    ]
                },
            },
            {
                "title": "Findings",
                "content_type": "MARKDOWN",
                "content": {"markdown": "Sales increased by **15%** quarter-over-quarter."},
            },
        ],
        "provenance": {
            "dataset_id": "ds_sales_2026",
            "dataset_version_id": "v1",
            "is_stale": False,
        },
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, "report.html")
        path, size, section_count = renderer.render(report_dict, out_file)

        assert os.path.exists(path)
        assert size > 0
        assert section_count == 2

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "<!DOCTYPE html>" in content
            assert "Executive Performance Summary" in content
            assert "Revenue" in content


def test_markdown_report_renderer():
    renderer = MarkdownReportRenderer()
    report_dict = {
        "title": "Data Quality Report",
        "subtitle": "Integrity Check",
        "dataset_id": "ds_quality_1",
        "sections": [
            {
                "title": "Overview",
                "content_type": "MARKDOWN",
                "content": {"markdown": "All 12 columns passed null-check validation."},
            }
        ],
        "provenance": {
            "dataset_id": "ds_quality_1",
            "dataset_version_id": "v1",
            "is_stale": False,
        },
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, "report.md")
        path, size, section_count = renderer.render(report_dict, out_file)

        assert os.path.exists(path)
        assert size > 0
        assert section_count == 1

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "# Data Quality Report" in content
            assert "All 12 columns passed null-check" in content


def test_get_renderer_factory():
    assert isinstance(get_renderer("CSV"), CsvRenderer)
    assert isinstance(get_renderer("JSON"), JsonRenderer)
    assert isinstance(get_renderer("XLSX"), XlsxRenderer)
    assert isinstance(get_renderer("HTML_REPORT"), HtmlReportRenderer)
    assert isinstance(get_renderer("MARKDOWN_REPORT"), MarkdownReportRenderer)

    with pytest.raises(ValueError, match="Unsupported export format"):
        get_renderer("UNSUPPORTED_XYZ")
