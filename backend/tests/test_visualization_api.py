"""
Tests for Phase 9 Visualization REST API endpoints.
"""

import os
import tempfile
import polars as pl
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.engines.visualization.models import ChartType
from backend.app.main import app
from backend.app.services.visualization_service import visualization_service


@pytest.fixture
def mock_dataset_environment(monkeypatch):
    temp_dir = tempfile.mkdtemp()
    parquet_path = os.path.join(temp_dir, "test.parquet")
    df = pl.DataFrame({
        "region": ["North", "South", "East", "West"],
        "revenue": [100.0, 200.0, 300.0, 400.0],
        "date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
    })
    df.write_parquet(parquet_path)

    # Monkeypatch resolver
    def mock_resolve(dataset_id: str, version_id: str = None):
        return "v1", parquet_path

    monkeypatch.setattr(visualization_service, "_resolve_version_and_path", mock_resolve)
    yield parquet_path

    try:
        os.remove(parquet_path)
        os.rmdir(temp_dir)
    except Exception:
        pass


@pytest.mark.asyncio
async def test_visualization_api_endpoints(mock_dataset_environment):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. POST /recommend-from-sql
        sql_rec_resp = await client.post(
            "/api/v1/visualizations/recommend-from-sql",
            json={
                "columns": [
                    {"name": "region", "physical_type": "string", "semantic_type": "categorical"},
                    {"name": "revenue", "physical_type": "float64", "semantic_type": "numeric"},
                ],
                "rows": [
                    {"region": "North", "revenue": 100.0},
                    {"region": "South", "revenue": 200.0},
                ],
            },
        )
        assert sql_rec_resp.status_code == 200
        recs = sql_rec_resp.json()
        assert len(recs) > 0
        assert any(r["chart_type"] == "bar" for r in recs)

        # 2. POST /validate
        val_resp = await client.post(
            "/api/v1/visualizations/validate",
            json={
                "chart_id": "test_v",
                "chart_type": "bar",
                "title": "Test",
                "dataset_id": "mock_ds",
                "dataset_version_id": "v1",
                "x": "region",
                "y": "revenue",
                "aggregation": "sum",
            },
        )
        assert val_resp.status_code == 200
        val_data = val_resp.json()
        assert val_data["is_valid"] is True

        # 3. POST /preview
        prev_resp = await client.post(
            "/api/v1/visualizations/preview",
            json={
                "chart_id": "test_prev",
                "chart_type": "bar",
                "title": "Revenue by Region",
                "dataset_id": "mock_ds",
                "dataset_version_id": "v1",
                "x": "region",
                "y": "revenue",
                "aggregation": "sum",
            },
        )
        assert prev_resp.status_code == 200
        prev_data = prev_resp.json()
        assert len(prev_data["data"]) == 4

        # 4. POST / (save visualization)
        save_resp = await client.post(
            "/api/v1/visualizations",
            json={
                "name": "Regional Revenue Bar",
                "description": "Created from test suite",
                "spec": prev_data,
            },
        )
        assert save_resp.status_code == 201
        saved = save_resp.json()
        viz_id = saved["visualization_id"]
        assert viz_id.startswith("viz_")

        # 5. GET /
        list_resp = await client.get("/api/v1/visualizations")
        assert list_resp.status_code == 200
        all_viz = list_resp.json()
        assert any(v["visualization_id"] == viz_id for v in all_viz)

        # 6. GET /{id}
        get_resp = await client.get(f"/api/v1/visualizations/{viz_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "Regional Revenue Bar"

        # 7. GET /{id}/data
        data_resp = await client.get(f"/api/v1/visualizations/{viz_id}/data")
        assert data_resp.status_code == 200
        assert data_resp.json()["row_count"] == 4

        # 8. DELETE /{id}
        del_resp = await client.delete(f"/api/v1/visualizations/{viz_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["deleted"] is True
