"""
AnalyzaX — Phase 12: Time-Aware Splitting and Rolling-Origin Backtest Generator.
Enforces strict chronological data isolation. Random splitting and temporal data leakage
are strictly prohibited.
"""

from typing import Dict, Generator, List, NamedTuple, Optional, Tuple
import numpy as np
import pandas as pd

from backend.app.engines.forecasting.exceptions import ForecastErrorCode, ForecastException


class SplitWindow(NamedTuple):
    fold_index: int
    train_indices: np.ndarray
    test_indices: np.ndarray
    train_timestamps: List[str]
    test_timestamps: List[str]
    train_y: np.ndarray
    test_y: np.ndarray


def chronological_train_test_split(
    timestamps: List[str],
    y: np.ndarray,
    test_size: int,
) -> Tuple[np.ndarray, np.ndarray, List[str], List[str], np.ndarray, np.ndarray]:
    """
    Split series strictly chronologically: [0 : N - test_size] for training,
    [N - test_size : N] for testing.
    """
    n = len(y)
    if test_size >= n or test_size <= 0:
        raise ForecastException(
            code=ForecastErrorCode.FORECAST_SPLIT_ERROR,
            message=f"Test size ({test_size}) must be strictly between 1 and dataset length ({n} - 1).",
        )

    split_idx = n - test_size
    train_idx = np.arange(0, split_idx)
    test_idx = np.arange(split_idx, n)

    train_ts = [timestamps[i] for i in train_idx]
    test_ts = [timestamps[i] for i in test_idx]

    train_y = y[train_idx]
    test_y = y[test_idx]

    return train_idx, test_idx, train_ts, test_ts, train_y, test_y


def generate_rolling_origin_folds(
    timestamps: List[str],
    y: np.ndarray,
    horizon: int,
    n_folds: int = 3,
    window_type: str = "expanding",
    fixed_window_size: Optional[int] = None,
) -> List[SplitWindow]:
    """
    Generate rolling-origin (walk-forward) validation folds.
    Fold 0 evaluates earliest historical test window, advancing forward to Fold K-1.
    Chronology is strictly preserved.
    """
    n = len(y)
    total_required = horizon * n_folds + 5
    if n < total_required:
        # Gracefully reduce folds if dataset is small
        n_folds = max(1, (n - 5) // horizon)
        if n_folds < 1:
            raise ForecastException(
                code=ForecastErrorCode.FORECAST_INSUFFICIENT_HISTORY,
                message=f"Series length {n} is too short for horizon {horizon} and minimum training requirements.",
            )

    folds: List[SplitWindow] = []
    
    # Origins: origins for test periods of length `horizon`
    # E.g. for n_folds=3: test windows are [n - 3*h : n - 2*h], [n - 2*h : n - h], [n - h : n]
    for k in range(n_folds):
        test_start_idx = n - (n_folds - k) * horizon
        test_end_idx = test_start_idx + horizon

        if window_type == "rolling" and fixed_window_size and fixed_window_size > 5:
            train_start_idx = max(0, test_start_idx - fixed_window_size)
        else:
            # Expanding window
            train_start_idx = 0

        train_indices = np.arange(train_start_idx, test_start_idx)
        test_indices = np.arange(test_start_idx, test_end_idx)

        train_ts = [timestamps[i] for i in train_indices]
        test_ts = [timestamps[i] for i in test_indices]

        folds.append(
            SplitWindow(
                fold_index=k,
                train_indices=train_indices,
                test_indices=test_indices,
                train_timestamps=train_ts,
                test_timestamps=test_ts,
                train_y=y[train_indices],
                test_y=y[test_indices],
            )
        )

    return folds
