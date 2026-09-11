"""
AnalyzaX — Phase 12: Forecasting REST API Integration Tests.
Tests all FastAPI endpoints for models, metrics, temporal analysis,
experiments, results, diagnostics, and future inference.
"""

import os
from fastapi.testclient import TestClient
import numpy as np
import pandas as pd
import polars as pl
import pytest

from backend.app.core.config import settings
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_dataset():
    """Create a sample parquet dataset file in data/processed for API testing."""
    os.makedirs(settings.DATA_PROCESSED_DIR, exist_ok=True)
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    df = pl.DataFrame({
        "date": [d.strftime("%Y-%m-%d") for d in dates],
        "sales": np.linspace(100.0, 300.0, 60).tolist(),
        "store_id": ["ST1"] * 60,
    })
    target_path = os.path.join(settings.DATA_PROCESSED_DIR, "ds_api_ts.parquet")
    df.write_parquet(target_path)
    yield
    # Cleanup if needed
    if os.path.exists(target_path):
        try:
            os.remove(target_path)
        except Exception:
            pass


def test_api_models_and_metrics(client):
    res_models = client.get("/api/v1/forecasting/models")
    assert res_models.status_code == 200
    models_data = res_models.json()
    assert len(models_data) >= 8
    model_ids = [m["model_id"] for m in models_data]
    assert "naive" in model_ids
    assert "drift" in model_ids
    assert "holt" in model_ids
    assert "arima" in model_ids

    res_metrics = client.get("/api/v1/forecasting/metrics")
    assert res_metrics.status_code == 200
    metrics_data = res_metrics.json()
    metric_ids = [m["id"] for m in metrics_data]
    assert "rmse" in metric_ids
    assert "mae" in metric_ids
    assert "mase" in metric_ids


def test_api_suitability_and_temporal_analysis(client):
    payload = {
        "dataset_id": "ds_api_ts",
        "dataset_version_id": "v1",
        "time_column": "date",
        "target_column": "sales",
    }
    res_suit = client.post("/api/v1/forecasting/suitability", json=payload)
    assert res_suit.status_code == 200
    suit_data = res_suit.json()
    assert suit_data["is_valid"] is True
    assert suit_data["observation_count"] == 60
    assert suit_data["inferred_frequency"] == "DAILY"

    res_ana = client.post("/api/v1/forecasting/analyze", json={**payload, "frequency": "DAILY"})
    assert res_ana.status_code == 200
    ana_data = res_ana.json()
    assert "trend" in ana_data
    assert "seasonality" in ana_data
    assert ana_data["trend"]["direction"] == "UPWARD"


def test_api_run_forecasting_experiment(client):
    exp_req = {
        "dataset_id": "ds_api_ts",
        "dataset_version_id": "v1",
        "time_column": "date",
        "target_column": "sales",
        "forecast_horizon": 5,
        "validation_folds": 2,
        "models": ["naive", "drift"],
        "primary_metric": "rmse",
        "confidence_level": 0.95,
    }
    # Run sync for instant result
    res_exp = client.post("/api/v1/forecasting/experiments?sync=true", json=exp_req)
    assert res_exp.status_code == 200
    exp_data = res_exp.json()
    exp_id = exp_data["experiment_id"]
    assert exp_data["status"] == "COMPLETED"

    # Get results
    res_res = client.get(f"/api/v1/forecasting/experiments/{exp_id}/results")
    assert res_res.status_code == 200
    res_data = res_res.json()
    assert len(res_data["models"]) == 2
    assert res_data["forecast_horizon"] == 5
    assert len(res_data["visualizations"]) >= 2

    # Get forecasts
    res_fc = client.get(f"/api/v1/forecasting/experiments/{exp_id}/forecasts")
    assert res_fc.status_code == 200
    fc_data = res_fc.json()
    assert len(fc_data) == 5

    # Run future prediction on best model run
    best_run_id = res_data["models"][0]["run_id"]
    res_pred = client.post(
        f"/api/v1/forecasting/models/{best_run_id}/predict",
        json={"periods": 10, "confidence_level": 0.95},
    )
    assert res_pred.status_code == 200
    pred_data = res_pred.json()
    assert len(pred_data["forecast_points"]) == 10

    # Check history
    res_hist = client.get("/api/v1/forecasting/history")
    assert res_hist.status_code == 200
    hist_data = res_hist.json()
    assert hist_data["total_count"] >= 1
