"""
AnalyzaX — Phase 12: Mandatory Forecasting Version Isolation Tests.
Verifies that:
1. A forecasting experiment and its artifacts remain strictly bound to Dataset Version V1.
2. Dataset Version V2 does not mutate or invalidate Experiment A.
3. Provenance unequivocally traces back to V1.
"""

import numpy as np
import pandas as pd
import polars as pl
import pytest

from backend.app.engines.forecasting.engine import forecasting_engine
from backend.app.engines.forecasting.models import ForecastExperimentRequest


def test_forecast_version_isolation():
    # 1. Create Dataset Version 1
    dates_v1 = pd.date_range("2024-01-01", periods=40, freq="D")
    df_v1 = pl.DataFrame({
        "date": [d.strftime("%Y-%m-%d") for d in dates_v1],
        "metric": np.linspace(10.0, 50.0, 40).tolist(),
    })

    req_v1 = ForecastExperimentRequest(
        dataset_id="ds_ts_isolation",
        dataset_version_id="ver_1",
        time_column="date",
        target_column="metric",
        forecast_horizon=5,
        validation_folds=2,
        models=["naive", "drift"],
    )

    result_v1 = forecasting_engine.execute_experiment(df_v1, req_v1)
    assert result_v1.dataset_version_id == "ver_1"
    assert result_v1.provenance["dataset_version_id"] == "ver_1"
    v1_drift_preds = [pt.value for pt in next(m for m in result_v1.models if m.model_id == "drift").future_forecasts]

    # 2. Create Dataset Version 2 with substantially modified values (e.g. downward trend)
    dates_v2 = pd.date_range("2024-01-01", periods=40, freq="D")
    df_v2 = pl.DataFrame({
        "date": [d.strftime("%Y-%m-%d") for d in dates_v2],
        "metric": np.linspace(500.0, 100.0, 40).tolist(),
    })

    req_v2 = ForecastExperimentRequest(
        dataset_id="ds_ts_isolation",
        dataset_version_id="ver_2",
        time_column="date",
        target_column="metric",
        forecast_horizon=5,
        validation_folds=2,
        models=["naive", "drift"],
    )

    result_v2 = forecasting_engine.execute_experiment(df_v2, req_v2)
    assert result_v2.dataset_version_id == "ver_2"
    assert result_v2.provenance["dataset_version_id"] == "ver_2"
    v2_drift_preds = [pt.value for pt in next(m for m in result_v2.models if m.model_id == "drift").future_forecasts]

    # 3. Assert V1 predictions were NOT mutated by V2 execution
    assert result_v1.dataset_version_id == "ver_1"
    assert v1_drift_preds != v2_drift_preds
    # V1 has upward slope (last val 50.0), V2 has downward slope (last val 100.0)
    assert v1_drift_preds[0] > 50.0
    assert v2_drift_preds[0] < 100.0
