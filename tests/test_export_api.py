"""
API Integration tests for Phase 15 Export REST Router (/api/v1/exports).
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_list_report_templates():
    resp = client.get("/api/v1/exports/reports/templates")
    assert resp.status_code == 200
    templates = resp.json()
    assert isinstance(templates, list)
    assert len(templates) >= 6
    template_keys = [t["template"] for t in templates]
    assert "EXECUTIVE_SUMMARY" in template_keys
    assert "FULL_ANALYSIS" in template_keys


def test_export_api_full_lifecycle(monkeypatch, tmp_path):
    # Setup dummy parquet and dataset resolution
    dummy_parquet = str(tmp_path / "test.parquet")
    import polars as pl
    pl.DataFrame({"id": [1, 2], "val": ["a", "b"]}).write_parquet(dummy_parquet)

    monkeypatch.setattr(
        "backend.app.services.export_service.dataset_service.get_dataset",
        lambda ds_id: {"dataset_id": ds_id, "name": "API Test", "file_path": dummy_parquet},
    )
    monkeypatch.setattr(
        "backend.app.services.export_service.export_service._resolve_version",
        lambda ds_id, v_id: (v_id or "v1", dummy_parquet),
    )

    # 1. Generate a report via /api/v1/exports/reports
    report_req = {
        "dataset_id": "ds_api_test",
        "template": "EXECUTIVE_SUMMARY",
        "title": "API Test Report",
        "subtitle": "Integration test report generation",
        "format": "HTML_REPORT",
    }
    resp = client.post("/api/v1/exports/reports", json=report_req)
    assert resp.status_code == 200
    job = resp.json()
    job_id = job["job_id"]
    assert job["status"] == "COMPLETED"
    assert job["format"] == "HTML_REPORT"
    assert job["file_name"].endswith(".html")

    # 2. Get export by ID
    resp = client.get(f"/api/v1/exports/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["job_id"] == job_id

    # 3. Download the artifact
    resp = client.get(f"/api/v1/exports/{job_id}/download")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "API Test Report" in resp.text

    # 4. List exports and verify job is present
    resp = client.get("/api/v1/exports?dataset_id=ds_api_test")
    assert resp.status_code == 200
    jobs = resp.json()
    assert any(j["job_id"] == job_id for j in jobs)

    # 5. Delete export
    resp = client.delete(f"/api/v1/exports/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True

    # 6. Verify 404 after deletion
    resp = client.get(f"/api/v1/exports/{job_id}")
    assert resp.status_code == 404


def test_export_cleanup_endpoint():
    resp = client.post("/api/v1/exports/cleanup")
    assert resp.status_code == 200
    data = resp.json()
    assert "removed" in data
    assert isinstance(data["removed"], int)
