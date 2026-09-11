"""
Integration tests for Data Quality API endpoints
Tests GET /api/v1/datasets/{id}/quality, query filters, and POST /refresh.
"""

import io
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_get_dataset_quality_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # 1. Upload a dataset with deliberate quality issues (missing, duplicates, whitespaces, negative age)
        csv_content = (
            b"user_id,name,age,email,gender\n"
            b"1,Alice,25,alice@example.com,Female\n"
            b"2,Bob,30,bob@example.com,Male\n"
            b"2,Bob,30,bob@example.com,Male\n"  # Duplicate row & duplicate key
            b"3, Charlie ,-10,invalid-email,male\n"  # Whitespace, negative age, malformed email, casing
            b",Dave,145,dave@example.com,MALE\n"  # Null ID, impossible age, casing
        )
        upload_resp = await client.post(
            "/api/v1/datasets/upload",
            files={"file": ("quality_api_test.csv", io.BytesIO(csv_content), "text/csv")},
        )
        assert upload_resp.status_code == 201
        data = upload_resp.json()
        ds_id = data["dataset_id"]

        # 2. Call GET /datasets/{id}/quality
        quality_resp = await client.get(f"/api/v1/datasets/{ds_id}/quality")
        assert quality_resp.status_code == 200
        report = quality_resp.json()

        assert report["dataset_id"] == ds_id
        assert report["status"] == "READY"
        assert report["quality_report_version"] == "quality_v1"
        assert report["overall_score"] < 100.0  # Quality issues detected
        assert report["total_issues"] > 0
        assert "COMPLETENESS" in report["dimension_scores"]
        assert "UNIQUENESS" in report["dimension_scores"]
        assert "VALIDITY" in report["dimension_scores"]
        assert "CONSISTENCY" in report["dimension_scores"]
        assert "INTEGRITY" in report["dimension_scores"]
        assert len(report["column_summaries"]) == 5

        # 3. Test filtering by severity
        filtered_resp = await client.get(f"/api/v1/datasets/{ds_id}/quality?severity=CRITICAL")
        assert filtered_resp.status_code == 200
        filtered = filtered_resp.json()
        for issue in filtered["issues"]:
            assert issue["severity"] == "CRITICAL"

        # 4. Test filtering by dimension
        dim_resp = await client.get(f"/api/v1/datasets/{ds_id}/quality?dimension=CONSISTENCY")
        assert dim_resp.status_code == 200
        dim_filtered = dim_resp.json()
        for issue in dim_filtered["issues"]:
            assert issue["dimension"] == "CONSISTENCY"

        # 5. Test POST /datasets/{id}/quality/refresh
        refresh_resp = await client.post(f"/api/v1/datasets/{ds_id}/quality/refresh")
        assert refresh_resp.status_code == 200
        refreshed = refresh_resp.json()
        assert refreshed["dataset_id"] == ds_id
        assert refreshed["total_issues"] == report["total_issues"]

        # 6. Test 404 for unknown dataset
        unknown_resp = await client.get("/api/v1/datasets/non_existent_dataset_id_123/quality")
        assert unknown_resp.status_code == 404
