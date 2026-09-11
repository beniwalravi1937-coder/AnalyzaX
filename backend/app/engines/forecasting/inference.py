"""
AnalyzaX — Phase 12: Future Timestamp Generation & Out-of-Sample Inference.
Generates valid future calendar dates and prediction intervals without data mutation.
"""

from typing import Any, List, Optional
import numpy as np
import pandas as pd

from backend.app.engines.forecasting.evaluation import _safe_float
from backend.app.engines.forecasting.models import ForecastPoint


def generate_future_timestamps(
    last_timestamp_str: str,
    steps: int,
    pandas_freq_str: str = "D",
) -> List[str]:
    """
    Generate sequential future timestamps starting strictly from the period after the last historical timestamp.
    Respects calendar rules (month start, business days, etc.).
    """
    try:
        last_dt = pd.to_datetime(last_timestamp_str)
        # Create date range of steps+1 and slice [1:] to skip last_dt
        future_range = pd.date_range(start=last_dt, periods=steps + 1, freq=pandas_freq_str)[1:]
        return [dt.strftime("%Y-%m-%d %H:%M:%S") if ":" in str(last_dt) else dt.strftime("%Y-%m-%d") for dt in future_range]
    except Exception:
        # Fallback integer steps if custom non-standard timestamp
        return [f"Step_+{i+1}" for i in range(steps)]


def predict_future_points(
    estimator: Any,
    steps: int,
    future_timestamps: List[str],
    confidence_level: float = 0.95,
) -> List[ForecastPoint]:
    """Generate forecast points with prediction intervals from a trained estimator."""
    preds, lowers, uppers = estimator.predict(steps=steps, confidence_level=confidence_level)
    points: List[ForecastPoint] = []

    for i in range(steps):
        ts = future_timestamps[i] if i < len(future_timestamps) else f"Step_{i+1}"
        val = round(_safe_float(preds[i]), 4)
        lb = round(_safe_float(lowers[i]), 4) if lowers is not None else None
        ub = round(_safe_float(uppers[i]), 4) if uppers is not None else None
        points.append(
            ForecastPoint(
                timestamp=ts,
                value=val,
                lower_bound=lb,
                upper_bound=ub,
                horizon_step=i + 1,
            )
        )

    return points
