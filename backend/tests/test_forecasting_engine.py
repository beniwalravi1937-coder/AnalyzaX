"""
AnalyzaX — Phase 12: Forecasting Engine Unit Tests.
Tests frequency detection, temporal validation, decomposition, baselines,
exponential smoothing, ARIMA, SARIMA, backtesting, and metrics.
"""

import numpy as np
import pandas as pd
import polars as pl
import pytest

from backend.app.engines.forecasting.engine import forecasting_engine
from backend.app.engines.forecasting.evaluation import calculate_forecast_metrics, compute_residual_diagnostics
from backend.app.engines.forecasting.exceptions import ForecastException
from backend.app.engines.forecasting.models import (
    ForecastExperimentRequest,
    ForecastFrequency,
    RegularityStatus,
)
from backend.app.engines.forecasting.registry import forecast_model_registry
from backend.app.engines.forecasting.splitting import (
    chronological_train_test_split,
    generate_rolling_origin_folds,
)
from backend.app.engines.forecasting.temporal_analysis import (
    analyze_trend,
    compute_acf_pacf,
    decompose_series,
    detect_seasonality,
)
from backend.app.engines.forecasting.training import build_estimator
from backend.app.engines.forecasting.validation import (
    detect_time_column_candidates,
    infer_frequency,
    validate_time_series,
)


@pytest.fixture
def daily_seasonal_df():
    """Generates 90 days of synthetic daily data with linear trend and weekly seasonality."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=90, freq="D")
    t = np.arange(90)
    # Trend + Weekly Sine + Noise
    trend = 0.5 * t + 50.0
    seasonal = 10.0 * np.sin(2 * np.pi * t / 7.0)
    noise = np.random.normal(0, 1.0, size=90)
    y = trend + seasonal + noise
    return pl.DataFrame({
        "date": [d.strftime("%Y-%m-%d") for d in dates],
        "sales": y.tolist(),
        "store": ["Store_A"] * 90,
    })


def test_time_column_candidate_detection(daily_seasonal_df):
    candidates = detect_time_column_candidates(daily_seasonal_df)
    assert len(candidates) > 0
    assert candidates[0]["column_name"] == "date"
    assert candidates[0]["confidence"] >= 0.7


def test_frequency_inference():
    # Daily
    daily_ts = pd.date_range("2024-01-01", periods=30, freq="D")
    freq, p_freq, reg, conf = infer_frequency(pd.Series(daily_ts))
    assert freq == ForecastFrequency.DAILY
    assert reg == RegularityStatus.REGULAR
    assert conf > 0.8

    # Hourly
    hourly_ts = pd.date_range("2024-01-01", periods=48, freq="h")
    h_freq, _, _, _ = infer_frequency(pd.Series(hourly_ts))
    assert h_freq == ForecastFrequency.HOURLY

    # Monthly
    monthly_ts = pd.date_range("2020-01-01", periods=24, freq="MS")
    m_freq, _, _, _ = infer_frequency(pd.Series(monthly_ts))
    assert m_freq == ForecastFrequency.MONTHLY


def test_validate_time_series_success(daily_seasonal_df):
    report = validate_time_series(
        df=daily_seasonal_df,
        time_column="date",
        target_column="sales",
    )
    assert report.is_valid is True
    assert report.observation_count == 90
    assert report.inferred_frequency == ForecastFrequency.DAILY
    assert report.missing_timestamp_count == 0
    assert report.duplicate_timestamp_count == 0


def test_validate_time_series_constant_target_fails():
    df = pl.DataFrame({
        "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
        "constant_y": [10.0, 10.0, 10.0, 10.0, 10.0],
    })
    report = validate_time_series(df, "date", "constant_y")
    assert report.is_valid is False
    assert any(i.issue_id == "QI_CONSTANT_TARGET" for i in report.issues)


def test_trend_and_seasonality_analysis(daily_seasonal_df):
    y = daily_seasonal_df["sales"].to_numpy()
    dates = daily_seasonal_df["date"].to_list()

    trend = analyze_trend(y)
    assert trend.detected is True
    assert trend.slope > 0
    assert trend.direction.value == "UPWARD"

    seas = detect_seasonality(y, ForecastFrequency.DAILY)
    assert seas.detected is True
    assert seas.candidate_period == 7  # weekly cycle

    acf_res = compute_acf_pacf(y, max_lags=15)
    assert len(acf_res.acf_values) == 16
    assert acf_res.acf_values[0] == 1.0

    decomp = decompose_series(dates, y, period=7)
    assert decomp is not None
    assert len(decomp.trend) == 90
    assert len(decomp.seasonal) == 90


def test_chronological_splitting(daily_seasonal_df):
    dates = daily_seasonal_df["date"].to_list()
    y = daily_seasonal_df["sales"].to_numpy()

    tr_idx, te_idx, tr_ts, te_ts, tr_y, te_y = chronological_train_test_split(dates, y, test_size=14)
    assert len(tr_y) == 76
    assert len(te_y) == 14
    # Ensure chronology: last train date < first test date
    assert pd.to_datetime(tr_ts[-1]) < pd.to_datetime(te_ts[0])


def test_rolling_origin_folds(daily_seasonal_df):
    dates = daily_seasonal_df["date"].to_list()
    y = daily_seasonal_df["sales"].to_numpy()

    folds = generate_rolling_origin_folds(dates, y, horizon=7, n_folds=3)
    assert len(folds) == 3

    for fold in folds:
        assert len(fold.test_y) == 7
        assert pd.to_datetime(fold.train_timestamps[-1]) < pd.to_datetime(fold.test_timestamps[0])

    # Assert fold 0 is strictly earlier than fold 1
    assert pd.to_datetime(folds[0].test_timestamps[0]) < pd.to_datetime(folds[1].test_timestamps[0])
    assert pd.to_datetime(folds[1].test_timestamps[0]) < pd.to_datetime(folds[2].test_timestamps[0])


def test_forecast_metrics_correctness():
    y_true = np.array([100.0, 105.0, 110.0, 95.0])
    y_pred = np.array([102.0, 104.0, 108.0, 97.0])
    y_train = np.array([90.0, 95.0, 98.0, 100.0])

    metrics = calculate_forecast_metrics(y_true, y_pred, y_train=y_train)
    # Expected MAE = (2 + 1 + 2 + 2) / 4 = 1.75
    assert metrics.mae == 1.75
    assert metrics.rmse > 0
    assert metrics.mase is not None
    assert metrics.smape > 0
    assert metrics.wape > 0
    assert metrics.mape is not None


def test_all_registered_models_train_and_predict(daily_seasonal_df):
    y = daily_seasonal_df["sales"].to_numpy()[:60]
    horizon = 7

    for model_id in ["naive", "seasonal_naive", "drift", "simple_exp_smoothing", "holt", "holt_winters", "arima", "sarima"]:
        model_def = forecast_model_registry.get(model_id)
        assert model_def is not None

        est = build_estimator(model_id, model_def.default_parameters)
        est.fit(y)
        preds, lowers, uppers = est.predict(steps=horizon, confidence_level=0.95)

        assert len(preds) == horizon
        assert not np.any(np.isnan(preds))
        if lowers is not None and uppers is not None:
            assert len(lowers) == horizon
            assert len(uppers) == horizon
            # Point forecast should generally sit within prediction intervals
            assert np.all(lowers <= uppers)


def test_end_to_end_forecasting_experiment(daily_seasonal_df):
    req = ForecastExperimentRequest(
        dataset_id="ds_test_time_series",
        dataset_version_id="ver_1",
        time_column="date",
        target_column="sales",
        forecast_horizon=7,
        validation_folds=2,
        models=["naive", "drift", "holt", "arima"],
        primary_metric="rmse",
        confidence_level=0.95,
    )

    result = forecasting_engine.execute_experiment(daily_seasonal_df, req)
    assert result.forecast_horizon == 7
    assert len(result.models) == 4
    assert result.best_model_id in ["naive", "drift", "holt", "arima"]
    assert len(result.findings) >= 2
    assert len(result.visualizations) >= 3  # forecast, comparison, decomposition, etc.

    # Check that best model generated 7 future points with prediction intervals
    best_run = next(m for m in result.models if m.model_id == result.best_model_id)
    assert len(best_run.future_forecasts) == 7
    for pt in best_run.future_forecasts:
        assert pt.value is not None
        assert pt.lower_bound is not None
        assert pt.upper_bound is not None
        assert pt.lower_bound <= pt.upper_bound
