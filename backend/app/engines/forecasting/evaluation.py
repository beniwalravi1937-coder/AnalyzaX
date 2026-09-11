"""
AnalyzaX — Phase 12: Forecasting Metrics & Residual Diagnostics.
Deterministic, mathematically sound evaluation calculations (MAE, MSE, RMSE, MASE,
sMAPE, WAPE, MAPE, and Ljung-Box autocorrelation).
"""

from typing import Any, Dict, List, Optional
import numpy as np
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox

from backend.app.engines.forecasting.models import ForecastMetrics, ResidualDiagnostics


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        f = float(val)
        return default if np.isnan(f) or np.isinf(f) else f
    except (ValueError, TypeError):
        return default


def calculate_forecast_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_train: Optional[np.ndarray] = None,
) -> ForecastMetrics:
    """
    Calculate comprehensive forecast accuracy metrics.
    Guarantees mathematical correctness and zero division safety.
    """
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)

    if len(yt) != len(yp):
        raise ValueError(f"Actuals length ({len(yt)}) and predictions length ({len(yp)}) must match.")

    n = len(yt)
    if n == 0:
        return ForecastMetrics(mae=0.0, mse=0.0, rmse=0.0, smape=0.0, wape=0.0)

    errors = yt - yp
    abs_errors = np.abs(errors)
    sq_errors = errors ** 2

    mae = _safe_float(np.mean(abs_errors))
    mse = _safe_float(np.mean(sq_errors))
    rmse = _safe_float(np.sqrt(mse))

    # sMAPE: 200 * |y - y_hat| / (|y| + |y_hat| + eps)
    denom_smape = np.abs(yt) + np.abs(yp)
    smape_terms = np.where(denom_smape > 1e-9, 2.0 * abs_errors / denom_smape, 0.0)
    smape = _safe_float(100.0 * np.mean(smape_terms))

    # WAPE: 100 * sum(|y - y_hat|) / sum(|y|)
    sum_yt = np.sum(np.abs(yt))
    wape = _safe_float(100.0 * np.sum(abs_errors) / sum_yt) if sum_yt > 1e-9 else 0.0

    # MAPE: only valid if all |yt| > 1e-5
    mape: Optional[float] = None
    if np.all(np.abs(yt) > 1e-5):
        mape = _safe_float(100.0 * np.mean(abs_errors / np.abs(yt)))

    # MASE (Mean Absolute Scaled Error)
    mase: Optional[float] = None
    if y_train is not None and len(y_train) > 1:
        # In-sample naive scale
        naive_diffs = np.abs(np.diff(y_train))
        scale = np.mean(naive_diffs)
        if scale > 1e-9:
            mase = _safe_float(mae / scale)

    return ForecastMetrics(
        mae=round(mae, 4),
        mse=round(mse, 4),
        rmse=round(rmse, 4),
        mase=round(mase, 4) if mase is not None else None,
        smape=round(smape, 4),
        wape=round(wape, 4),
        mape=round(mape, 4) if mape is not None else None,
    )


def compute_residual_diagnostics(
    residuals: np.ndarray,
    timestamps: Optional[List[str]] = None,
) -> ResidualDiagnostics:
    """Calculate statistical diagnostics on model forecast residuals."""
    res = np.asarray(residuals, dtype=float)
    n = len(res)

    if n < 3:
        return ResidualDiagnostics(
            mean=_safe_float(np.mean(res)),
            std=_safe_float(np.std(res)),
            residuals=[round(_safe_float(r), 4) for r in res],
            residual_timestamps=timestamps or [],
        )

    r_mean = _safe_float(np.mean(res))
    r_std = _safe_float(np.std(res))

    # Ljung-Box test for autocorrelation
    lb_stat: Optional[float] = None
    lb_p: Optional[float] = None
    autocorr = False
    try:
        lags = min(10, n // 2)
        if lags >= 1:
            lb_df = acorr_ljungbox(res, lags=[lags], return_df=True)
            lb_stat = _safe_float(lb_df["lb_stat"].iloc[0])
            lb_p = _safe_float(lb_df["lb_pvalue"].iloc[0], default=1.0)
            autocorr = lb_p < 0.05
    except Exception:
        pass

    # Normality test
    norm_stat: Optional[float] = None
    norm_p: Optional[float] = None
    try:
        if 3 <= n <= 5000:
            sh_stat, sh_p = stats.shapiro(res)
            norm_stat = _safe_float(sh_stat)
            norm_p = _safe_float(sh_p)
        else:
            jb_stat, jb_p = stats.jarque_bera(res)
            norm_stat = _safe_float(jb_stat)
            norm_p = _safe_float(jb_p)
    except Exception:
        pass

    return ResidualDiagnostics(
        mean=round(r_mean, 4),
        std=round(r_std, 4),
        ljung_box_stat=round(lb_stat, 4) if lb_stat is not None else None,
        ljung_box_pvalue=round(lb_p, 4) if lb_p is not None else None,
        normality_stat=round(norm_stat, 4) if norm_stat is not None else None,
        normality_pvalue=round(norm_p, 4) if norm_p is not None else None,
        autocorrelation_detected=autocorr,
        residuals=[round(_safe_float(r), 4) for r in res],
        residual_timestamps=timestamps or [],
    )
