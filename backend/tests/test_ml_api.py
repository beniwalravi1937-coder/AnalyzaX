"""
AnalyzaX — Phase 11: Machine Learning API Integration Tests.
Tests REST endpoints using FastAPI TestClient:
- Model Registry & Capabilities
- Supported Metrics
- Suitability & Input Validation
- Experiment Execution (Regression, Classification, Clustering)
- Model Run Retrieval
- Predictions & Schema Validation
- Experiment History
"""

import io
import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.services.dataset_service import dataset_service

client = TestClient(app)


@pytest.fixture
def ml_dataset():
    """Ingests a test dataset with continuous, binary, and categorical attributes."""
    rows = ["age,income,education,has_purchased,score"]
    for i in range(60):
        age = 20 + i
        inc = 30000 + i * 1500
        edu = "College" if i % 2 == 0 else "HighSchool"
        purch = 1 if (age > 40 or inc > 60000) else 0
        score = round(2.5 * age + 0.05 * inc + (10 if edu == "College" else 0), 2)
        rows.append(f"{age},{inc},{edu},{purch},{score}")

    csv_content = "\n".join(rows)
    file_obj = io.BytesIO(csv_content.encode("utf-8"))
    import asyncio
    ds = asyncio.run(dataset_service.ingest_file(file_obj, "customer_ml.csv", "text/csv"))
    return ds


def test_api_list_models():
    res = client.get("/api/v1/ml/models")
    assert res.status_code == 200
    models = res.json()
    assert len(models) >= 13
    model_ids = {m["model_id"] for m in models}
    assert "dummy_regressor" in model_ids
    assert "linear_regression" in model_ids
    assert "logistic_regression" in model_ids
    assert "kmeans" in model_ids


def test_api_list_metrics():
    res = client.get("/api/v1/ml/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "regression" in data
    assert "binary_classification" in data
    assert "clustering" in data
    assert "rmse" in data["regression"]
    assert "accuracy" in data["binary_classification"]


def test_api_suitability_check(ml_dataset):
    ds_id = ml_dataset.id
    res = client.post(
        "/api/v1/ml/suitability",
        json={
            "dataset_id": ds_id,
            "dataset_version_id": "v1",
            "target_column": "score",
            "task_type": "regression",
            "candidate_features": ["age", "income", "education"],
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["is_suitable"] is True
    assert "age" in body["recommended_features"]
    assert body["recommended_task"] == "regression"


def test_api_run_regression_experiment(ml_dataset):
    ds_id = ml_dataset.id
    res = client.post(
        "/api/v1/ml/experiments",
        json={
            "dataset_id": ds_id,
            "dataset_version_id": "v1",
            "task_type": "regression",
            "target_column": "score",
            "feature_columns": ["age", "income", "education"],
            "models": ["linear_regression", "ridge"],
            "primary_metric": "rmse",
            "random_seed": 42,
        },
    )
    assert res.status_code == 200
    result = res.json()
    assert result["status"] == "COMPLETED"
    assert len(result["model_runs"]) >= 3
    assert result["best_model_run_id"] is not None
    assert len(result["visualizations"]) >= 1
    assert len(result["findings"]) >= 1

    best_run_id = result["best_model_run_id"]

    # Test prediction endpoint
    pred_res = client.post(
        f"/api/v1/ml/models/{best_run_id}/predict",
        json={
            "rows": [
                {"age": 35, "income": 55000, "education": "College"},
                {"age": 50, "income": 80000, "education": "HighSchool"},
            ]
        },
    )
    assert pred_res.status_code == 200
    pbody = pred_res.json()
    assert pbody["row_count"] == 2
    assert len(pbody["predictions"]) == 2
    assert isinstance(pbody["predictions"][0], float)


def test_api_run_classification_experiment(ml_dataset):
    ds_id = ml_dataset.id
    res = client.post(
        "/api/v1/ml/experiments",
        json={
            "dataset_id": ds_id,
            "dataset_version_id": "v1",
            "task_type": "binary_classification",
            "target_column": "has_purchased",
            "feature_columns": ["age", "income", "education"],
            "models": ["logistic_regression"],
            "primary_metric": "accuracy",
            "random_seed": 42,
        },
    )
    assert res.status_code == 200
    result = res.json()
    assert result["status"] == "COMPLETED"
    assert len(result["model_runs"]) >= 2  # dummy_classifier + logistic_regression


def test_api_run_clustering_experiment(ml_dataset):
    ds_id = ml_dataset.id
    res = client.post(
        "/api/v1/ml/experiments",
        json={
            "dataset_id": ds_id,
            "dataset_version_id": "v1",
            "task_type": "clustering",
            "feature_columns": ["age", "income"],
            "models": ["kmeans"],
            "primary_metric": "inertia",
            "random_seed": 42,
        },
    )
    assert res.status_code == 200
    result = res.json()
    assert result["status"] == "COMPLETED"
    assert len(result["model_runs"]) >= 1


def test_api_history(ml_dataset):
    res = client.get("/api/v1/ml/history")
    assert res.status_code == 200
    history = res.json()
    assert isinstance(history, list)
    assert len(history) >= 1
