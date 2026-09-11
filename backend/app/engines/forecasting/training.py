"""
AnalyzaX — Phase 12: Forecasting Model Trainers & Backtesting Engine.
Implements deterministic statistical estimators using statsmodels and analytical formulas.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.api import (
    ARIMA,
    ExponentialSmoothing,
    Holt,
    SimpleExpSmoothing,
)
from statsmodels.tsa.statespace.sarimax import SARIMAX

from backend.app.engines.forecasting.evaluation import (
    _safe_float,
    calculate_forecast_metrics,
    compute_residual_diagnostics,
)
from backend.app.engines.forecasting.exceptions import ForecastErrorCode, ForecastException
from backend.app.engines.forecasting.models import (
    BacktestFoldResult,
    BacktestResult,
    ForecastMetrics,
    ForecastModelRun,
    ForecastPoint,
)
from backend.app.engines.forecasting.splitting import SplitWindow


def _get_z_score(confidence_level: float) -> float:
    # Two-sided z-score: e.g. 0.95 -> alpha=0.05 -> z=1.96
    alpha = 1.0 - confidence_level
    return float(stats.norm.ppf(1.0 - alpha / 2.0))


class BaseForecastEstimator:
    """Base interface for statistical forecasting models."""

    def fit(self, y: np.ndarray) -> "BaseForecastEstimator":
        raise NotImplementedError

    def predict(self, steps: int, confidence_level: float = 0.95) -> Tuple[np.ndarray, Optional[np.ndarray], Optional[np.ndarray]]:
        """Returns (point_forecasts, lower_bounds, upper_bounds)."""
        raise NotImplementedError


class NaiveEstimator(BaseForecastEstimator):
    def fit(self, y: np.ndarray) -> "NaiveEstimator":
        self.last_val = float(y[-1])
        # Residual std dev from in-sample naive 1-step errors
        diffs = np.diff(y)
        self.sigma = float(np.std(diffs)) if len(diffs) > 1 else 1.0
        return self

    def predict(self, steps: int, confidence_level: float = 0.95) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        z = _get_z_score(confidence_level)
        preds = np.full(steps, self.last_val, dtype=float)
        # Variance increases with sqrt(h)
        h = np.arange(1, steps + 1)
        half_width = z * self.sigma * np.sqrt(h)
        return preds, preds - half_width, preds + half_width


class SeasonalNaiveEstimator(BaseForecastEstimator):
    def __init__(self, seasonal_period: int = 7):
        self.m = max(2, int(seasonal_period))

    def fit(self, y: np.ndarray) -> "SeasonalNaiveEstimator":
        self.y_history = np.asarray(y, dtype=float)
        # Residual std dev
        if len(y) > self.m:
            diffs = y[self.m:] - y[:-self.m]
            self.sigma = float(np.std(diffs)) if len(diffs) > 1 else 1.0
        else:
            self.sigma = 1.0
        return self

    def predict(self, steps: int, confidence_level: float = 0.95) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        z = _get_z_score(confidence_level)
        preds = []
        n = len(self.y_history)
        for i in range(steps):
            idx = n - self.m + (i % self.m)
            preds.append(self.y_history[idx if idx >= 0 else 0])

        preds = np.asarray(preds, dtype=float)
        k = np.floor(np.arange(steps) / self.m) + 1.0
        half_width = z * self.sigma * np.sqrt(k)
        return preds, preds - half_width, preds + half_width


class DriftEstimator(BaseForecastEstimator):
    def fit(self, y: np.ndarray) -> "DriftEstimator":
        self.n = len(y)
        self.y_last = float(y[-1])
        self.y_first = float(y[0])
        self.slope = (self.y_last - self.y_first) / max(1, self.n - 1)
        # Residual std dev
        trend_line = self.y_first + self.slope * np.arange(self.n)
        resids = y - trend_line
        self.sigma = float(np.std(resids)) if len(resids) > 1 else 1.0
        return self

    def predict(self, steps: int, confidence_level: float = 0.95) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        z = _get_z_score(confidence_level)
        h = np.arange(1, steps + 1)
        preds = self.y_last + h * self.slope
        se = self.sigma * np.sqrt(h * (1.0 + h / max(1, self.n - 1)))
        half_width = z * se
        return preds, preds - half_width, preds + half_width


class SESEstimator(BaseForecastEstimator):
    def __init__(self, smoothing_level: Optional[float] = None):
        self.alpha = smoothing_level

    def fit(self, y: np.ndarray) -> "SESEstimator":
        model = SimpleExpSmoothing(y, initialization_method="estimated")
        self.res = model.fit(smoothing_level=self.alpha, optimized=self.alpha is None)
        self.sigma = float(np.std(self.res.resid)) if len(self.res.resid) > 1 else 1.0
        return self

    def predict(self, steps: int, confidence_level: float = 0.95) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        preds = np.asarray(self.res.forecast(steps), dtype=float)
        z = _get_z_score(confidence_level)
        h = np.arange(1, steps + 1)
        half_width = z * self.sigma * np.sqrt(h)
        return preds, preds - half_width, preds + half_width


class HoltEstimator(BaseForecastEstimator):
    def __init__(self, damped_trend: bool = False):
        self.damped = damped_trend

    def fit(self, y: np.ndarray) -> "HoltEstimator":
        model = Holt(y, damped_trend=self.damped, initialization_method="estimated")
        self.res = model.fit(optimized=True)
        self.sigma = float(np.std(self.res.resid)) if len(self.res.resid) > 1 else 1.0
        return self

    def predict(self, steps: int, confidence_level: float = 0.95) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        preds = np.asarray(self.res.forecast(steps), dtype=float)
        z = _get_z_score(confidence_level)
        h = np.arange(1, steps + 1)
        half_width = z * self.sigma * np.sqrt(h)
        return preds, preds - half_width, preds + half_width


class HoltWintersEstimator(BaseForecastEstimator):
    def __init__(self, trend: str = "add", seasonal: str = "add", seasonal_period: int = 7):
        self.trend = trend if trend in ("add", "mul") else None
        self.seasonal = seasonal if seasonal in ("add", "mul") else None
        self.sp = max(2, int(seasonal_period))

    def fit(self, y: np.ndarray) -> "HoltWintersEstimator":
        # Handle zero/negative for multiplicative
        trend_type = self.trend
        seasonal_type = self.seasonal
        if np.any(y <= 0) and (trend_type == "mul" or seasonal_type == "mul"):
            trend_type = "add" if trend_type == "mul" else trend_type
            seasonal_type = "add" if seasonal_type == "mul" else seasonal_type

        # Ensure enough history for seasonal
        if len(y) < self.sp * 2:
            seasonal_type = None

        model = ExponentialSmoothing(
            y,
            trend=trend_type,
            seasonal=seasonal_type,
            seasonal_periods=self.sp if seasonal_type else None,
            initialization_method="estimated",
        )
        self.res = model.fit(optimized=True)
        self.sigma = float(np.std(self.res.resid)) if len(self.res.resid) > 1 else 1.0
        return self

    def predict(self, steps: int, confidence_level: float = 0.95) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        preds = np.asarray(self.res.forecast(steps), dtype=float)
        z = _get_z_score(confidence_level)
        h = np.arange(1, steps + 1)
        half_width = z * self.sigma * np.sqrt(h)
        return preds, preds - half_width, preds + half_width


class ARIMAEstimator(BaseForecastEstimator):
    def __init__(self, p: int = 1, d: int = 1, q: int = 1):
        self.order = (p, d, q)

    def fit(self, y: np.ndarray) -> "ARIMAEstimator":
        model = ARIMA(y, order=self.order)
        self.res = model.fit()
        return self

    def predict(self, steps: int, confidence_level: float = 0.95) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        fc = self.res.get_forecast(steps=steps)
        preds = np.asarray(fc.predicted_mean, dtype=float)
        alpha = 1.0 - confidence_level
        conf = fc.conf_int(alpha=alpha)
        lower = np.asarray(conf[:, 0], dtype=float)
        upper = np.asarray(conf[:, 1], dtype=float)
        return preds, lower, upper


class SARIMAEstimator(BaseForecastEstimator):
    def __init__(self, p: int = 1, d: int = 1, q: int = 1, P: int = 1, D: int = 0, Q: int = 1, m: int = 7):
        self.order = (p, d, q)
        self.s_order = (P, D, Q, max(2, m))

    def fit(self, y: np.ndarray) -> "SARIMAEstimator":
        # Check if enough history for seasonal order
        if len(y) < self.s_order[3] * 2:
            s_order = (0, 0, 0, 0)
        else:
            s_order = self.s_order

        model = SARIMAX(y, order=self.order, seasonal_order=s_order, enforce_stationarity=False, enforce_invertibility=False)
        self.res = model.fit(disp=False)
        return self

    def predict(self, steps: int, confidence_level: float = 0.95) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        fc = self.res.get_forecast(steps=steps)
        preds = np.asarray(fc.predicted_mean, dtype=float)
        alpha = 1.0 - confidence_level
        conf = fc.conf_int(alpha=alpha)
        lower = np.asarray(conf[:, 0], dtype=float)
        upper = np.asarray(conf[:, 1], dtype=float)
        return preds, lower, upper


def build_estimator(model_id: str, parameters: Dict[str, Any]) -> BaseForecastEstimator:
    """Factory creating configured estimator instance."""
    if model_id == "naive":
        return NaiveEstimator()
    elif model_id == "seasonal_naive":
        return SeasonalNaiveEstimator(seasonal_period=parameters.get("seasonal_period", 7))
    elif model_id == "drift":
        return DriftEstimator()
    elif model_id == "simple_exp_smoothing":
        return SESEstimator(smoothing_level=parameters.get("smoothing_level"))
    elif model_id == "holt":
        return HoltEstimator(damped_trend=parameters.get("damped_trend", False))
    elif model_id == "holt_winters":
        return HoltWintersEstimator(
            trend=parameters.get("trend", "add"),
            seasonal=parameters.get("seasonal", "add"),
            seasonal_period=parameters.get("seasonal_period", 7),
        )
    elif model_id == "arima":
        return ARIMAEstimator(
            p=parameters.get("p", 1),
            d=parameters.get("d", 1),
            q=parameters.get("q", 1),
        )
    elif model_id == "sarima":
        return SARIMAEstimator(
            p=parameters.get("p", 1),
            d=parameters.get("d", 1),
            q=parameters.get("q", 1),
            P=parameters.get("P", 1),
            D=parameters.get("D", 0),
            Q=parameters.get("Q", 1),
            m=parameters.get("m", 7),
        )
    else:
        raise ForecastException(
            code=ForecastErrorCode.FORECAST_INVALID_MODEL,
            message=f"Unsupported model identifier: '{model_id}'",
        )


def train_and_backtest_model(
    model_id: str,
    parameters: Dict[str, Any],
    folds: List[SplitWindow],
    full_timestamps: List[str],
    full_y: np.ndarray,
    future_timestamps: List[str],
    horizon: int,
    confidence_level: float = 0.95,
) -> ForecastModelRun:
    """
    Train and backtest a single forecasting model.
    1. Runs walk-forward rolling-origin backtesting across folds.
    2. Refits on full historical series to produce future forecast with prediction intervals.
    """
    start_time = time.perf_counter()
    warnings: List[str] = []

    # 1. Backtest across folds
    fold_results: List[BacktestFoldResult] = []
    for fold in folds:
        est = build_estimator(model_id, parameters)
        try:
            est.fit(fold.train_y)
            preds, _, _ = est.predict(steps=len(fold.test_y), confidence_level=confidence_level)
            metrics = calculate_forecast_metrics(fold.test_y, preds, y_train=fold.train_y)
            fold_results.append(
                BacktestFoldResult(
                    fold_index=fold.fold_index,
                    train_end=fold.train_timestamps[-1],
                    test_start=fold.test_timestamps[0],
                    test_end=fold.test_timestamps[-1],
                    actuals=[round(float(v), 4) for v in fold.test_y],
                    predictions=[round(_safe_float(v), 4) for v in preds],
                    metrics=metrics,
                )
            )
        except Exception as e:
            warnings.append(f"Fold {fold.fold_index} training issue: {str(e)}")
            # Fallback naive prediction for fold
            naive_pred = np.full(len(fold.test_y), fold.train_y[-1])
            metrics = calculate_forecast_metrics(fold.test_y, naive_pred, y_train=fold.train_y)
            fold_results.append(
                BacktestFoldResult(
                    fold_index=fold.fold_index,
                    train_end=fold.train_timestamps[-1],
                    test_start=fold.test_timestamps[0],
                    test_end=fold.test_timestamps[-1],
                    actuals=[round(float(v), 4) for v in fold.test_y],
                    predictions=[round(float(v), 4) for v in naive_pred],
                    metrics=metrics,
                )
            )

    # 2. Mean metrics aggregation
    mean_mae = float(np.mean([f.metrics.mae for f in fold_results]))
    mean_mse = float(np.mean([f.metrics.mse for f in fold_results]))
    mean_rmse = float(np.mean([f.metrics.rmse for f in fold_results]))
    mase_vals = [f.metrics.mase for f in fold_results if f.metrics.mase is not None]
    mean_mase = float(np.mean(mase_vals)) if mase_vals else None
    mean_smape = float(np.mean([f.metrics.smape for f in fold_results]))
    mean_wape = float(np.mean([f.metrics.wape for f in fold_results]))
    mape_vals = [f.metrics.mape for f in fold_results if f.metrics.mape is not None]
    mean_mape = float(np.mean(mape_vals)) if mape_vals else None

    std_metrics = {
        "mae": float(np.std([f.metrics.mae for f in fold_results])),
        "rmse": float(np.std([f.metrics.rmse for f in fold_results])),
        "smape": float(np.std([f.metrics.smape for f in fold_results])),
    }

    backtest = BacktestResult(
        folds=fold_results,
        mean_metrics=ForecastMetrics(
            mae=round(mean_mae, 4),
            mse=round(mean_mse, 4),
            rmse=round(mean_rmse, 4),
            mase=round(mean_mase, 4) if mean_mase is not None else None,
            smape=round(mean_smape, 4),
            wape=round(mean_wape, 4),
            mape=round(mean_mape, 4) if mean_mape is not None else None,
        ),
        std_metrics=std_metrics,
    )

    # 3. Refit on full series to produce future forecast
    full_estimator = build_estimator(model_id, parameters)
    full_estimator.fit(full_y)
    future_preds, lowers, uppers = full_estimator.predict(steps=horizon, confidence_level=confidence_level)

    forecast_points: List[ForecastPoint] = []
    for step_i in range(horizon):
        ts = future_timestamps[step_i] if step_i < len(future_timestamps) else f"Step_{step_i+1}"
        val = round(_safe_float(future_preds[step_i]), 4)
        lb = round(_safe_float(lowers[step_i]), 4) if lowers is not None else None
        ub = round(_safe_float(uppers[step_i]), 4) if uppers is not None else None
        forecast_points.append(
            ForecastPoint(
                timestamp=ts,
                value=val,
                lower_bound=lb,
                upper_bound=ub,
                horizon_step=step_i + 1,
            )
        )

    # 4. Residual diagnostics from latest fold or in-sample
    resids = np.array([])
    if fold_results:
        latest_fold = fold_results[-1]
        resids = np.array(latest_fold.actuals) - np.array(latest_fold.predictions)
    resid_diag = compute_residual_diagnostics(resids)

    duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

    return ForecastModelRun(
        run_id=f"run_{model_id}_{int(time.time()*1000)%1000000}",
        model_id=model_id,
        model_name=model_id.replace("_", " ").title(),
        parameters=parameters,
        training_status="COMPLETED",
        training_duration_ms=duration_ms,
        sample_count=len(full_y),
        backtest_result=backtest,
        future_forecasts=forecast_points,
        residual_diagnostics=resid_diag,
        warnings=warnings,
    )
