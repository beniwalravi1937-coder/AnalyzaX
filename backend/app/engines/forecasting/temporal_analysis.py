"""
AnalyzaX — Phase 12: Temporal Analysis (Trend, Seasonality, ACF/PACF, Decomposition).
Pure deterministic computations evaluating time-series structure and seasonal properties.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import acf, pacf

from backend.app.engines.forecasting.models import (
    ACFResult,
    DecompositionResult,
    ForecastFrequency,
    SeasonalityFinding,
    TemporalAnalysisSummary,
    TrendDirection,
    TrendFinding,
)


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        f = float(val)
        return default if np.isnan(f) or np.isinf(f) else f
    except (ValueError, TypeError):
        return default


def analyze_trend(y: np.ndarray) -> TrendFinding:
    """Analyze linear trend in target series using OLS."""
    n = len(y)
    if n < 4:
        return TrendFinding(
            detected=False,
            direction=TrendDirection.FLAT,
            slope=0.0,
            p_value=1.0,
            r_squared=0.0,
            description="Insufficient observations to reliably determine trend.",
        )

    x = np.arange(n)
    res = stats.linregress(x, y)
    slope = _safe_float(res.slope)
    p_val = _safe_float(res.pvalue, default=1.0)
    r2 = _safe_float(res.rvalue ** 2)

    is_significant = p_val < 0.05
    if not is_significant or abs(slope) < 1e-5:
        direction = TrendDirection.FLAT
        desc = "The series exhibits no statistically significant linear trend."
    elif slope > 0:
        direction = TrendDirection.UPWARD
        desc = f"Statistically significant upward trend detected (slope: +{slope:.4f}/step, R²={r2:.3f}, p={p_val:.4g})."
    else:
        direction = TrendDirection.DOWNWARD
        desc = f"Statistically significant downward trend detected (slope: {slope:.4f}/step, R²={r2:.3f}, p={p_val:.4g})."

    return TrendFinding(
        detected=is_significant and direction != TrendDirection.FLAT,
        direction=direction,
        slope=round(slope, 6),
        p_value=round(p_val, 6),
        r_squared=round(r2, 4),
        description=desc,
    )


def detect_seasonality(
    y: np.ndarray,
    frequency: ForecastFrequency,
) -> SeasonalityFinding:
    """Detect seasonal cycles using autocorrelation analysis on detrended series."""
    n = len(y)
    candidate_lags: List[Tuple[int, str]] = []

    if frequency == ForecastFrequency.DAILY:
        candidate_lags = [(7, "weekly (7 days)"), (14, "biweekly (14 days)")]
    elif frequency == ForecastFrequency.HOURLY:
        candidate_lags = [(24, "daily (24 hours)"), (168, "weekly (168 hours)")]
    elif frequency == ForecastFrequency.MONTHLY:
        candidate_lags = [(12, "annual (12 months)")]
    elif frequency == ForecastFrequency.QUARTERLY:
        candidate_lags = [(4, "annual (4 quarters)")]
    elif frequency == ForecastFrequency.WEEKLY:
        candidate_lags = [(52, "annual (52 weeks)")]
    else:
        candidate_lags = [(7, "period 7"), (12, "period 12")]

    # Detrend series using linear fit to isolate periodic oscillations
    x = np.arange(n)
    try:
        slope, intercept, _, _, _ = stats.linregress(x, y)
        y_detrended = y - (slope * x + intercept)
    except Exception:
        y_detrended = y - np.mean(y)

    significance_threshold = 1.96 / np.sqrt(n) if n > 0 else 0.5
    valid_candidates = []

    for lag, label in candidate_lags:
        # Require at least 2 full seasonal cycles
        if n >= lag * 2:
            try:
                autocorr_val = pd.Series(y_detrended).autocorr(lag=lag)
                if not np.isnan(autocorr_val) and autocorr_val > significance_threshold:
                    valid_candidates.append({
                        "lag": lag,
                        "label": label,
                        "strength": _safe_float(autocorr_val),
                    })
            except Exception:
                pass

    if valid_candidates:
        # Check if fundamental period exists (e.g. 7 is fundamental of 14)
        best = valid_candidates[0]
        for cand in valid_candidates[1:]:
            # If candidate is a multiple of best and strength difference is small (<0.15), keep fundamental
            if cand["lag"] % best["lag"] == 0 and abs(cand["strength"] - best["strength"]) < 0.15:
                continue
            elif cand["strength"] > best["strength"] + 0.15:
                best = cand

        if best["strength"] > 0.20:
            return SeasonalityFinding(
                detected=True,
                candidate_period=best["lag"],
                frequency_label=best["label"],
                seasonal_strength=round(best["strength"], 4),
                confidence=round(min(1.0, best["strength"] + 0.2), 2),
                description=f"Strong seasonal pattern detected with a cycle of {best['lag']} observations ({best['label']}, ACF={best['strength']:.3f}).",
                evidence={"lag": best["lag"], "autocorrelation": best["strength"], "threshold": round(significance_threshold, 3)},
            )

    return SeasonalityFinding(
        detected=False,
        candidate_period=None,
        seasonal_strength=0.0,
        confidence=0.0,
        description="No dominant seasonal cycle detected exceeding statistical significance thresholds.",
    )


def compute_acf_pacf(y: np.ndarray, max_lags: int = 24) -> ACFResult:
    """Compute bounded Autocorrelation Function (ACF) and Partial Autocorrelation Function (PACF)."""
    n = len(y)
    nlags = min(max_lags, max(2, n // 3))
    
    # 1. ACF
    acf_vals = acf(y, nlags=nlags, fft=True)
    # 2. PACF
    try:
        pacf_vals = pacf(y, nlags=nlags, method="yule_walker")
    except Exception:
        pacf_vals = np.zeros(len(acf_vals))

    conf_bound = _safe_float(1.96 / np.sqrt(n), default=0.2)

    return ACFResult(
        lags=list(range(len(acf_vals))),
        acf_values=[round(_safe_float(v), 4) for v in acf_vals],
        pacf_values=[round(_safe_float(v), 4) for v in pacf_vals],
        confidence_bound=round(conf_bound, 4),
    )


def decompose_series(
    timestamps: List[str],
    y: np.ndarray,
    period: int = 7,
) -> Optional[DecompositionResult]:
    """Perform classical seasonal decomposition (Trend, Seasonal, Residual)."""
    n = len(y)
    if n < period * 2 or period < 2:
        return None

    try:
        s = pd.Series(y)
        decomp = seasonal_decompose(s, model="additive", period=period, extrapolate_trend="freq")
        
        trend_clean = [None if np.isnan(v) else round(float(v), 4) for v in decomp.trend]
        seasonal_clean = [None if np.isnan(v) else round(float(v), 4) for v in decomp.seasonal]
        residual_clean = [None if np.isnan(v) else round(float(v), 4) for v in decomp.resid]

        return DecompositionResult(
            method="classical_additive",
            period=period,
            timestamps=timestamps,
            observed=[round(float(v), 4) for v in y],
            trend=trend_clean,
            seasonal=seasonal_clean,
            residual=residual_clean,
        )
    except Exception:
        return None


def run_temporal_analysis(
    timestamps: List[str],
    y: np.ndarray,
    frequency: ForecastFrequency,
) -> TemporalAnalysisSummary:
    """Execute complete temporal analysis pipeline."""
    trend = analyze_trend(y)
    seasonality = detect_seasonality(y, frequency)
    
    acf_result = compute_acf_pacf(y, max_lags=24)
    
    decomp_period = seasonality.candidate_period or (7 if frequency == ForecastFrequency.DAILY else 12)
    decomposition = decompose_series(timestamps, y, period=decomp_period)

    # Anomaly count: residuals outside 3 standard deviations if decomposition succeeded
    anomalies = 0
    if decomposition and decomposition.residual:
        valid_resids = [r for r in decomposition.residual if r is not None]
        if valid_resids:
            res_arr = np.array(valid_resids)
            r_mean, r_std = res_arr.mean(), res_arr.std()
            if r_std > 0:
                anomalies = int((np.abs(res_arr - r_mean) > 3 * r_std).sum())

    return TemporalAnalysisSummary(
        trend=trend,
        seasonality=seasonality,
        acf=acf_result,
        decomposition=decomposition,
        anomalies_detected=anomalies,
    )
