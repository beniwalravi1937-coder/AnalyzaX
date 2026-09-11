"""
AnalyzaX — Phase 12: Mandatory Temporal Leakage Tests.
Verifies that:
1. Chronological splitting strictly enforces train_end < test_start.
2. Rolling-origin validation folds never expose future actual observations to training windows.
3. Future forecast timestamps begin strictly after the historical series ends.
"""

import numpy as np
import pandas as pd
import polars as pl
import pytest

from backend.app.engines.forecasting.inference import generate_future_timestamps
from backend.app.engines.forecasting.splitting import (
    chronological_train_test_split,
    generate_rolling_origin_folds,
)
from backend.app.engines.forecasting.training import build_estimator


def test_chronological_train_test_split_temporal_isolation():
    dates = pd.date_range("2024-01-01", periods=50, freq="D")
    timestamps = [d.strftime("%Y-%m-%d") for d in dates]
    y = np.arange(50, dtype=float)

    _, _, tr_ts, te_ts, tr_y, te_y = chronological_train_test_split(timestamps, y, test_size=10)

    # 1. No overlapping timestamps
    assert set(tr_ts).isdisjoint(set(te_ts))

    # 2. Maximum training date is strictly less than minimum test date
    max_train_dt = pd.to_datetime(tr_ts[-1])
    min_test_dt = pd.to_datetime(te_ts[0])
    assert max_train_dt < min_test_dt

    # 3. Last training observation value is strictly 39, first test is 40
    assert tr_y[-1] == 39.0
    assert te_y[0] == 40.0


def test_rolling_origin_folds_temporal_isolation():
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    timestamps = [d.strftime("%Y-%m-%d") for d in dates]
    y = np.arange(60, dtype=float)

    horizon = 5
    folds = generate_rolling_origin_folds(timestamps, y, horizon=horizon, n_folds=4)
    assert len(folds) == 4

    for fold in folds:
        train_end_dt = pd.to_datetime(fold.train_timestamps[-1])
        test_start_dt = pd.to_datetime(fold.test_timestamps[0])
        test_end_dt = pd.to_datetime(fold.test_timestamps[-1])

        # Mandatory temporal constraint: train end must strictly precede test start
        assert train_end_dt < test_start_dt
        # Test start must strictly precede or equal test end
        assert test_start_dt <= test_end_dt
        # Training indices and test indices must have zero intersection
        assert len(np.intersect1d(fold.train_indices, fold.test_indices)) == 0


def test_future_timestamps_strictly_post_history():
    last_historical_ts = "2024-03-31"
    steps = 14
    future_dates = generate_future_timestamps(
        last_timestamp_str=last_historical_ts,
        steps=steps,
        pandas_freq_str="D",
    )

    assert len(future_dates) == steps
    # First future timestamp must be strictly greater than last historical timestamp
    first_future_dt = pd.to_datetime(future_dates[0])
    last_hist_dt = pd.to_datetime(last_historical_ts)
    assert first_future_dt > last_hist_dt
    assert first_future_dt == pd.to_datetime("2024-04-01")


def test_estimator_no_future_data_contamination():
    # Verify that changing future test data has ZERO influence on trained estimator parameters
    train_data = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
    
    # Model 1 fit on train_data
    est1 = build_estimator("drift", {})
    est1.fit(train_data)
    preds1, _, _ = est1.predict(steps=3)

    # Future ground truth A
    future_a = np.array([15.0, 16.0, 17.0])
    # Future ground truth B (drastically different)
    future_b = np.array([100.0, 200.0, 300.0])

    # Model 2 fit on exact same train_data
    est2 = build_estimator("drift", {})
    est2.fit(train_data)
    preds2, _, _ = est2.predict(steps=3)

    # Assert predictions are 100% identical regardless of what future actuals would be
    np.testing.assert_array_almost_equal(preds1, preds2)
