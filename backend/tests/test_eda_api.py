"""
AnalyzaX — Phase 7: EDA REST API Integration Tests
Tests /api/v1/datasets/{id}/eda, /refresh, column drilldown, relationship queries, and findings endpoints.
"""

import io
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_eda_api_full_flow():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # 1. Upload a rich test dataset
        csv_content = (
            b"id,age,income,category,signup_date\n"
            b"1,25,50000,Retail,2023-01-15\n"
            b"2,30,62000,Tech,2023-02-20\n"
            b"3,35,75000,Tech,2023-03-10\n"
            b"4,40,90000,Finance,2023-04-05\n"
            b"5,45,110000,Finance,2023-05-18\n"
            b"6,50,125000,Tech,2023-06-22\n"
            b"7,28,55000,Retail,2023-07-30\n"
            b"8,32,68000,Retail,2023-08-14\n"
            b"9,60,180000,Executive,2023-09-01\n"
            b"10,22,42000,Retail,2023-10-12\n"
        )
        upload_resp = await client.post(
            "/api/v1/datasets/upload",
            files={"file": ("eda_api_test.csv", io.BytesIO(csv_content), "text/csv")},
        )
        assert upload_resp.status_code == 201
        data = upload_resp.json()
        ds_id = data["dataset_id"]
        v_id = data.get("active_version_id", "v1")

        # 2. Call GET /datasets/{id}/eda
        eda_resp = await client.get(f"/api/v1/datasets/{ds_id}/eda")
        assert eda_resp.status_code == 200
        report = eda_resp.json()

        assert report["dataset_id"] == ds_id
        assert report["version_id"] == v_id
        assert report["report_id"].startswith("eda_")
        assert report["eda_version"] == "eda_v1"

        # Overview validations
        overview = report["overview"]
        assert overview["row_count"] == 10
        assert overview["column_count"] == 5
        assert overview["numeric_columns_count"] >= 2
        assert overview["categorical_columns_count"] >= 1

        # Check charts exist
        assert "charts" in report
        assert len(report["charts"]) > 0

        # Check findings exist
        assert "findings" in report
        assert isinstance(report["findings"], list)

        # 3. Call GET /datasets/{id}/versions/{version_id}/eda
        v_eda_resp = await client.get(f"/api/v1/datasets/{ds_id}/versions/{v_id}/eda")
        assert v_eda_resp.status_code == 200
        assert v_eda_resp.json()["dataset_id"] == ds_id

        # 4. Call POST /datasets/{id}/eda/refresh
        refresh_resp = await client.post(f"/api/v1/datasets/{ds_id}/eda/refresh")
        assert refresh_resp.status_code == 200
        refreshed = refresh_resp.json()
        assert refreshed["report_id"].startswith("eda_")

        # 5. Call GET /datasets/{id}/eda/columns/{column} for numeric column
        col_resp = await client.get(f"/api/v1/datasets/{ds_id}/eda/columns/income")
        assert col_resp.status_code == 200
        col_data = col_resp.json()
        assert col_data["column"] == "income"
        assert col_data["is_numeric"] is True
        assert "statistics" in col_data
        assert "charts" in col_data

        # 6. Call GET /datasets/{id}/eda/columns/{column} for categorical column
        cat_resp = await client.get(f"/api/v1/datasets/{ds_id}/eda/columns/category")
        assert cat_resp.status_code == 200
        cat_data = cat_resp.json()
        assert cat_data["column"] == "category"
        assert cat_data["is_numeric"] is False

        # 7. Call POST /datasets/{id}/eda/relationship
        rel_resp = await client.post(
            f"/api/v1/datasets/{ds_id}/eda/relationship",
            json={"column_x": "age", "column_y": "income"},
        )
        assert rel_resp.status_code == 200
        rel_data = rel_resp.json()
        assert rel_data["column_x"] == "age"
        assert rel_data["column_y"] == "income"
        assert rel_data["relationship_type"] == "numeric_numeric"
        assert rel_data["summary"] is not None
        assert rel_data["summary"]["correlation"] > 0.8
        assert rel_data["chart"] is not None

        # 8. Call GET /datasets/{id}/eda/findings
        findings_resp = await client.get(f"/api/v1/datasets/{ds_id}/eda/findings")
        assert findings_resp.status_code == 200
        findings = findings_resp.json()
        assert isinstance(findings, list)

        # 9. Test 404 for invalid dataset
        invalid_resp = await client.get("/api/v1/datasets/non_existent_ds_123/eda")
        assert invalid_resp.status_code == 404
