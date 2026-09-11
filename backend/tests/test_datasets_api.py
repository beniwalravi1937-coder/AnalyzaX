import os
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.services.duckdb_service import duckdb_service

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.mark.asyncio
async def test_upload_csv_success():
    transport = ASGITransport(app=app)
    sales_csv = os.path.join(FIXTURES_DIR, "small_sales.csv")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(sales_csv, "rb") as f:
            response = await client.post(
                "/api/v1/datasets/upload",
                files={"file": ("small_sales.csv", f, "text/csv")},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "READY"
        assert data["format"] == "csv"
        assert data["dataset_id"].startswith("ds_")
        assert data["duckdb_table_name"].startswith("dataset_ds_")
        dataset_id = data["dataset_id"]
        table_name = data["duckdb_table_name"]

        # Verify DuckDB queryability directly
        with duckdb_service.get_connection() as conn:
            res = conn.execute(f"SELECT count(*) FROM {table_name};").fetchone()
            assert res[0] == 3

        # Test GET /api/v1/datasets/{id}
        get_res = await client.get(f"/api/v1/datasets/{dataset_id}")
        assert get_res.status_code == 200
        get_data = get_res.json()
        assert get_data["id"] == dataset_id
        assert get_data["original_filename"] == "small_sales.csv"
        assert get_data["status"] == "READY"

        # Test GET /api/v1/datasets list
        list_res = await client.get("/api/v1/datasets")
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert any(d["id"] == dataset_id for d in list_data["datasets"])

        # Clean up via DELETE
        del_res = await client.delete(f"/api/v1/datasets/{dataset_id}")
        assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_upload_parquet_success():
    transport = ASGITransport(app=app)
    sample_parquet = os.path.join(FIXTURES_DIR, "sample.parquet")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(sample_parquet, "rb") as f:
            response = await client.post(
                "/api/v1/datasets/upload",
                files={"file": ("sample.parquet", f, "application/octet-stream")},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "READY"
        assert data["format"] == "parquet"

        # Clean up
        await client.delete(f"/api/v1/datasets/{data['dataset_id']}")


@pytest.mark.asyncio
async def test_upload_json_success():
    transport = ASGITransport(app=app)
    sample_json = os.path.join(FIXTURES_DIR, "sample.json")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(sample_json, "rb") as f:
            response = await client.post(
                "/api/v1/datasets/upload",
                files={"file": ("sample.json", f, "application/json")},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "READY"
        assert data["format"] == "json"

        # Clean up
        await client.delete(f"/api/v1/datasets/{data['dataset_id']}")


@pytest.mark.asyncio
async def test_upload_xlsx_success():
    transport = ASGITransport(app=app)
    sample_xlsx = os.path.join(FIXTURES_DIR, "sample.xlsx")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(sample_xlsx, "rb") as f:
            response = await client.post(
                "/api/v1/datasets/upload",
                files={"file": ("sample.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "READY"
        assert data["format"] == "xlsx"

        # Clean up
        await client.delete(f"/api/v1/datasets/{data['dataset_id']}")


@pytest.mark.asyncio
async def test_upload_unsupported_format():
    transport = ASGITransport(app=app)
    unsupported = os.path.join(FIXTURES_DIR, "unsupported.txt")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(unsupported, "rb") as f:
            response = await client.post(
                "/api/v1/datasets/upload",
                files={"file": ("unsupported.txt", f, "text/plain")},
            )

        assert response.status_code == 400
        data = response.json()
        error_msg = data.get("error", {}).get("message", "") or data.get("detail", "")
        assert "Unsupported file format" in error_msg


@pytest.mark.asyncio
async def test_upload_empty_file():
    transport = ASGITransport(app=app)
    invalid_csv = os.path.join(FIXTURES_DIR, "invalid.csv")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(invalid_csv, "rb") as f:
            response = await client.post(
                "/api/v1/datasets/upload",
                files={"file": ("invalid.csv", f, "text/csv")},
            )

        assert response.status_code == 400
        data = response.json()
        error_msg = data.get("error", {}).get("message", "") or data.get("detail", "")
        assert "empty" in error_msg.lower()


@pytest.mark.asyncio
async def test_path_traversal_sanitized():
    transport = ASGITransport(app=app)
    sales_csv = os.path.join(FIXTURES_DIR, "small_sales.csv")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(sales_csv, "rb") as f:
            response = await client.post(
                "/api/v1/datasets/upload",
                files={"file": ("../../etc/passwd.csv", f, "text/csv")},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "passwd.csv"
        assert ".." not in data["filename"]

        # Clean up
        await client.delete(f"/api/v1/datasets/{data['dataset_id']}")
