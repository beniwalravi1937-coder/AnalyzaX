"""
AnalyzaX — Phase 10: Statistical Intelligence API Integration Tests
Tests REST endpoints using FastAPI TestClient:
- Method Catalog
- Recommender
- Validation
- Analysis Execution
- History and Persistence
- Deletion
- Visualization retrieval
"""

import io
import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.services.dataset_service import dataset_service

client = TestClient(app)


@pytest.fixture
def sample_dataset():
    """Ingests a test dataset with numeric and categorical columns for statistical analysis."""
    csv_content = (
        "department,salary,experience_years,performance_score,gender\n"
        "Engineering,95000,5,85,Male\n"
        "Engineering,105000,7,90,Female\n"
        "Engineering,88000,4,82,Male\n"
        "Engineering,120000,9,95,Female\n"
        "Marketing,75000,3,78,Female\n"
        "Marketing,82000,5,80,Male\n"
        "Marketing,71000,2,75,Female\n"
        "Marketing,90000,6,88,Male\n"
        "Sales,65000,2,70,Male\n"
        "Sales,72000,4,74,Female\n"
        "Sales,85000,6,85,Male\n"
        "Sales,92000,7,89,Female\n"
    )
    file_obj = io.BytesIO(csv_content.encode("utf-8"))
    import asyncio
    ds = asyncio.run(dataset_service.ingest_file(file_obj, "employee_stats.csv", "text/csv"))
    return ds


def test_api_list_methods():
    res = client.get("/api/v1/statistics/methods")
    assert res.status_code == 200
    methods = res.json()
    assert len(methods) >= 12
    method_keys = [m["method"] for m in methods]
    assert "t_test_welch" in method_keys
    assert "anova_oneway" in method_keys
    assert "pearson" in method_keys
    assert "chi_square" in method_keys
    assert "ols_regression" in method_keys


def test_api_recommend_method(sample_dataset):
    ds_id = sample_dataset.id
    payload = {
        "dataset_id": ds_id,
        "dataset_version_id": "v1",
        "target_columns": ["salary"],
        "group_columns": ["department"],
    }
    res = client.post("/api/v1/statistics/recommend", json=payload)
    assert res.status_code == 200
    rec = res.json()
    assert rec["recommended_method"] == "anova_oneway"
    assert "rationale" in rec
    assert len(rec["rationale"]) > 0


def test_api_validate_request(sample_dataset):
    ds_id = sample_dataset.id
    # Valid request
    valid_payload = {
        "dataset_id": ds_id,
        "dataset_version_id": "v1",
        "analysis_type": "group_comparison",
        "method": "anova_oneway",
        "target_columns": ["salary"],
        "group_columns": ["department"],
    }
    res = client.post("/api/v1/statistics/validate", json=valid_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["missing_data_report"] is not None

    # Invalid request (non-existent column)
    invalid_payload = {
        "dataset_id": ds_id,
        "dataset_version_id": "v1",
        "analysis_type": "group_comparison",
        "method": "anova_oneway",
        "target_columns": ["non_existent_col"],
    }
    res_inv = client.post("/api/v1/statistics/validate", json=invalid_payload)
    assert res_inv.status_code == 200
    assert res_inv.json()["is_valid"] is False


def test_api_execute_and_history(sample_dataset):
    ds_id = sample_dataset.id

    # 1. Execute ANOVA
    req_payload = {
        "dataset_id": ds_id,
        "dataset_version_id": "v1",
        "analysis_type": "group_comparison",
        "method": "anova_oneway",
        "target_columns": ["salary"],
        "group_columns": ["department"],
        "parameters": {"alpha": 0.05},
    }
    res_run = client.post("/api/v1/statistics/analyze", json=req_payload)
    assert res_run.status_code == 200
    result_data = res_run.json()
    assert result_data["status"] == "COMPLETED"
    assert result_data["method"] == "anova_oneway"
    assert "statistics" in result_data
    assert "findings" in result_data
    assert "interpretation" in result_data
    assert len(result_data["chart_specs"]) > 0

    analysis_id = result_data["result_id"]

    # 2. Get specific analysis
    res_get = client.get(f"/api/v1/statistics/{analysis_id}")
    assert res_get.status_code == 200
    assert res_get.json()["result_id"] == analysis_id

    # 3. Retrieve visualizations
    res_viz = client.get(f"/api/v1/statistics/{analysis_id}/visualizations")
    assert res_viz.status_code == 200
    assert len(res_viz.json()) > 0

    # 4. List history
    res_hist = client.get(f"/api/v1/statistics/history?dataset_id={ds_id}")
    assert res_hist.status_code == 200
    assert any(h["result_id"] == analysis_id for h in res_hist.json())

    # 5. Delete analysis
    res_del = client.delete(f"/api/v1/statistics/{analysis_id}")
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "deleted"
