"""
Security tests for Phase 15 Export Engine.
Validates path traversal prevention, input validation, and boundary enforcement.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.engines.exports.models import (
    ExportProvenance,
    ExportSourceData,
)
from backend.app.engines.exports.renderers import CsvRenderer
from backend.app.main import app

client = TestClient(app)


def test_path_traversal_on_download():
    """Attempting path traversal in job_id must fail safely (400, 404, or 422)."""
    malicious_ids = [
        "../../etc/passwd",
        "..\\..\\windows\\system32\\calc.exe",
        "....//....//boot.ini",
        "exp_123/../../../secret.env",
    ]
    for bad_id in malicious_ids:
        resp = client.get(f"/api/v1/exports/{bad_id}/download")
        assert resp.status_code in [400, 404, 422]


def test_invalid_export_format():
    """Requesting an unsupported export format must be rejected with 422 Unprocessable Entity."""
    payload = {
        "dataset_id": "ds_sec_test",
        "source_type": "DATASET",
        "format": "MALICIOUS_EXEC_FORMAT",
    }
    resp = client.post("/api/v1/exports", json=payload)
    assert resp.status_code == 422


def test_invalid_source_type():
    """Requesting an unsupported source type must be rejected with 422 Unprocessable Entity."""
    payload = {
        "dataset_id": "ds_sec_test",
        "source_type": "ARBITRARY_FILE_SYSTEM",
        "format": "CSV",
    }
    resp = client.post("/api/v1/exports", json=payload)
    assert resp.status_code == 422


def test_row_limit_enforcement(tmp_path):
    """Ensure renderers enforce EXPORT_MAX_ROWS and do not write unbounded rows."""
    original_limit = settings.EXPORT_MAX_ROWS
    settings.EXPORT_MAX_ROWS = 50  # Lower limit for testing

    try:
        # Generate 150 rows
        large_rows = [{"id": i, "val": f"item_{i}"} for i in range(150)]
        source_data = ExportSourceData(
            data=large_rows,
            provenance=ExportProvenance(
                dataset_id="ds_sec",
                dataset_version_id="v1",
            ),
        )

        out_csv = str(tmp_path / "bounded.csv")
        renderer = CsvRenderer()
        path, size, rows = renderer.render(source_data, out_csv)

        assert rows == 50  # Capped at EXPORT_MAX_ROWS

        with open(out_csv, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        # 1 header line + 50 data lines = 51 lines
        assert len(lines) == 51
    finally:
        settings.EXPORT_MAX_ROWS = original_limit
