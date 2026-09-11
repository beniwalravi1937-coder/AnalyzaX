import io
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_get_dataset_profile_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # 1. Upload a dataset
        csv_content = (
            b"cust_id,product_category,revenue,churned,order_date\n"
            b"1,Electronics,1200.50,false,2026-01-01\n"
            b"2,Clothing,85.00,false,2026-01-02\n"
            b"3,Electronics,340.25,true,2026-01-03\n"
            b"4,Home,15.75,false,2026-01-04\n"
        )
        upload_resp = await client.post(
            "/api/v1/datasets/upload",
            files={"file": ("profile_test.csv", io.BytesIO(csv_content), "text/csv")},
        )
        assert upload_resp.status_code == 201
        data = upload_resp.json()
        ds_id = data["dataset_id"]

        # 2. Get profile
        prof_resp = await client.get(f"/api/v1/datasets/{ds_id}/profile")
        assert prof_resp.status_code == 200
        profile = prof_resp.json()

        assert profile["dataset_id"] == ds_id
        assert profile["row_count"] == 4
        assert profile["column_count"] == 5
        assert profile["status"] == "READY"
        assert len(profile["columns"]) == 5

        # Inspect revenue column
        rev_col = next(c for c in profile["columns"] if c["name"] == "revenue")
        assert rev_col["semantic_type"] == "monetary"
        assert rev_col["numeric_metrics"] is not None
        assert rev_col["numeric_metrics"]["min"] == 15.75
        assert rev_col["numeric_metrics"]["max"] == 1200.50

        # Inspect churned column
        churn_col = next(c for c in profile["columns"] if c["name"] == "churned")
        assert churn_col["semantic_type"] == "boolean"

        # 3. Test force refresh
        refresh_resp = await client.post(f"/api/v1/datasets/{ds_id}/profile/refresh")
        assert refresh_resp.status_code == 200
        refreshed = refresh_resp.json()
        assert refreshed["dataset_id"] == ds_id
        assert refreshed["row_count"] == 4


@pytest.mark.anyio
async def test_get_dataset_profile_not_found():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/datasets/ds_non_existent_9999/profile")
        assert resp.status_code == 404
