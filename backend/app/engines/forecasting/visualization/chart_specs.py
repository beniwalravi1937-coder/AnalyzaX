"""
AnalyzaX — Phase 12: Forecasting Visualization Integration.
Translates deterministic time-series forecasts, decomposition, ACF, and diagnostics
into standard Phase 9 ChartSpecs for seamless rendering in ChartRenderer.
"""

from typing import Any, Dict, List, Optional
import uuid
import pandas as pd

from backend.app.engines.forecasting.models import (
    ACFResult,
    DecompositionResult,
    ForecastModelRun,
    ForecastPoint,
    ResidualDiagnostics,
)
from backend.app.engines.visualization.models import (
    ChartAxesConfig,
    ChartLegendConfig,
    ChartSamplingMetadata,
    ChartSpec,
    ChartType,
    VisualizationProvenance,
)


def build_forecast_chart_spec(
    historical_timestamps: List[str],
    historical_values: List[float],
    forecast_points: List[ForecastPoint],
    model_name: str,
    dataset_id: str,
    dataset_version_id: str,
    target_column: str,
    confidence_level: float = 0.95,
) -> Optional[Dict[str, Any]]:
    """
    Build multi-series line chart depicting historical series, point forecast,
    and lower/upper prediction interval bounds.
    """
    if not historical_values or not forecast_points:
        return None

    # Keep at most last 100 historical points for a crisp, readable visual transition
    hist_slice_len = min(100, len(historical_values))
    hist_ts = historical_timestamps[-hist_slice_len:]
    hist_vals = historical_values[-hist_slice_len:]

    data: List[Dict[str, Any]] = []

    # Historical observations
    for ts, val in zip(hist_ts, hist_vals):
        data.append({
            "timestamp": ts,
            "series": "Historical",
            "value": round(val, 4),
            "lower": None,
            "upper": None,
        })

    # Bridge connection point (last historical observation as start of forecast line)
    if hist_ts and hist_vals:
        data.append({
            "timestamp": hist_ts[-1],
            "series": f"Forecast ({model_name})",
            "value": round(hist_vals[-1], 4),
            "lower": round(hist_vals[-1], 4),
            "upper": round(hist_vals[-1], 4),
        })

    # Forecast points
    for pt in forecast_points:
        data.append({
            "timestamp": pt.timestamp,
            "series": f"Forecast ({model_name})",
            "value": round(pt.value, 4),
            "lower": round(pt.lower_bound, 4) if pt.lower_bound is not None else None,
            "upper": round(pt.upper_bound, 4) if pt.upper_bound is not None else None,
        })

    conf_pct = int(round(confidence_level * 100))
    spec = ChartSpec(
        chart_id=f"fc_line_{uuid.uuid4().hex[:8]}",
        chart_type=ChartType.LINE,
        title=f"Time Series Forecast: {target_column}",
        subtitle=f"Historical trajectory and future projection by {model_name} with {conf_pct}% prediction intervals.",
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        source_type="forecasting",
        x="timestamp",
        y="value",
        series="series",
        data=data,
        axes=ChartAxesConfig(x_label="Timestamp", y_label=target_column, x_rotate=30),
        legend=ChartLegendConfig(show=True, position="top"),
        sampling=ChartSamplingMetadata(original_row_count=len(historical_values) + len(forecast_points), displayed_points=len(data)),
        provenance=VisualizationProvenance(
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            source_type="forecasting",
            source_reference=model_name,
            created_at=str(pd.Timestamp.now(tz="UTC")),
        ),
    )
    return spec.model_dump()


def build_decomposition_chart_spec(
    decomp: Optional[DecompositionResult],
    dataset_id: str,
    dataset_version_id: str,
    target_column: str,
) -> Optional[Dict[str, Any]]:
    """Build multi-series line chart displaying Trend, Seasonal, and Residual decomposition."""
    if not decomp:
        return None

    data: List[Dict[str, Any]] = []
    step = max(1, len(decomp.timestamps) // 100)
    for i in range(0, len(decomp.timestamps), step):
        ts = decomp.timestamps[i]
        if decomp.trend[i] is not None:
            data.append({"timestamp": ts, "component": "Trend", "value": decomp.trend[i]})
        if decomp.seasonal[i] is not None:
            data.append({"timestamp": ts, "component": "Seasonal", "value": decomp.seasonal[i]})
        if decomp.residual[i] is not None:
            data.append({"timestamp": ts, "component": "Residual", "value": decomp.residual[i]})

    spec = ChartSpec(
        chart_id=f"fc_decomp_{uuid.uuid4().hex[:8]}",
        chart_type=ChartType.LINE,
        title=f"Seasonal Decomposition: {target_column}",
        subtitle=f"Classical additive components (Period = {decomp.period}).",
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        source_type="forecasting",
        x="timestamp",
        y="value",
        series="component",
        data=data,
        axes=ChartAxesConfig(x_label="Timestamp", y_label="Value", x_rotate=30),
        legend=ChartLegendConfig(show=True, position="top"),
        sampling=ChartSamplingMetadata(original_row_count=len(decomp.timestamps), displayed_points=len(data)),
        provenance=VisualizationProvenance(
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            source_type="forecasting",
            source_reference="decomposition",
            created_at=str(pd.Timestamp.now(tz="UTC")),
        ),
    )
    return spec.model_dump()


def build_acf_chart_spec(
    acf_result: Optional[ACFResult],
    dataset_id: str,
    dataset_version_id: str,
    target_column: str,
) -> Optional[Dict[str, Any]]:
    """Build bar chart showing Autocorrelation Function coefficients across lags."""
    if not acf_result or not acf_result.acf_values:
        return None

    data = [
        {
            "lag": f"Lag {lag}",
            "autocorrelation": acf_result.acf_values[lag],
            "upper_bound": acf_result.confidence_bound,
            "lower_bound": -acf_result.confidence_bound,
        }
        for lag in acf_result.lags[1:]  # skip lag 0 (always 1.0)
    ]

    spec = ChartSpec(
        chart_id=f"fc_acf_{uuid.uuid4().hex[:8]}",
        chart_type=ChartType.BAR,
        title=f"Autocorrelation Function (ACF): {target_column}",
        subtitle=f"Lag correlation coefficients with 95% Bartlett confidence threshold (±{acf_result.confidence_bound:.3f}).",
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        source_type="forecasting",
        x="lag",
        y="autocorrelation",
        data=data,
        axes=ChartAxesConfig(x_label="Lag", y_label="Autocorrelation", x_rotate=30),
        legend=ChartLegendConfig(show=False),
        sampling=ChartSamplingMetadata(original_row_count=len(acf_result.lags), displayed_points=len(data)),
        provenance=VisualizationProvenance(
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            source_type="forecasting",
            source_reference="acf",
            created_at=str(pd.Timestamp.now(tz="UTC")),
        ),
    )
    return spec.model_dump()


def build_model_comparison_chart_spec(
    runs: List[ForecastModelRun],
    primary_metric: str,
    dataset_id: str,
    dataset_version_id: str,
) -> Optional[Dict[str, Any]]:
    """Build horizontal bar chart comparing models on primary backtest metric."""
    if not runs:
        return None

    data = []
    for r in runs:
        score = getattr(r.backtest_result.mean_metrics, primary_metric.lower(), None)
        if score is not None:
            data.append({
                "model": r.model_name,
                "score": score,
            })

    # Sort ascending for error metrics (lower is better)
    data.sort(key=lambda x: x["score"])

    spec = ChartSpec(
        chart_id=f"fc_cmp_{uuid.uuid4().hex[:8]}",
        chart_type=ChartType.BAR,
        title=f"Model Comparison ({primary_metric.upper()})",
        subtitle="Average out-of-sample error across rolling-origin validation folds (Lower is better).",
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        source_type="forecasting",
        x="model",
        y="score",
        data=data,
        axes=ChartAxesConfig(x_label="Model", y_label=primary_metric.upper(), x_rotate=25),
        legend=ChartLegendConfig(show=False),
        sampling=ChartSamplingMetadata(original_row_count=len(runs), displayed_points=len(data)),
        provenance=VisualizationProvenance(
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            source_type="forecasting",
            source_reference="comparison",
            created_at=str(pd.Timestamp.now(tz="UTC")),
        ),
    )
    return spec.model_dump()


def build_residual_chart_spec(
    diag: Optional[ResidualDiagnostics],
    dataset_id: str,
    dataset_version_id: str,
    model_name: str,
) -> Optional[Dict[str, Any]]:
    """Build residual line chart over backtest time steps."""
    if not diag or not diag.residuals:
        return None

    data = [
        {
            "index": str(i + 1),
            "residual": diag.residuals[i],
            "zero_line": 0.0,
        }
        for i in range(len(diag.residuals))
    ]

    spec = ChartSpec(
        chart_id=f"fc_resid_{uuid.uuid4().hex[:8]}",
        chart_type=ChartType.LINE,
        title=f"Forecast Residuals: {model_name}",
        subtitle="Difference between actual and backtest predicted values over historical test steps.",
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        source_type="forecasting",
        x="index",
        y="residual",
        data=data,
        axes=ChartAxesConfig(x_label="Backtest Step", y_label="Residual Error"),
        legend=ChartLegendConfig(show=False),
        sampling=ChartSamplingMetadata(original_row_count=len(diag.residuals), displayed_points=len(data)),
        provenance=VisualizationProvenance(
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            source_type="forecasting",
            source_reference=model_name,
            created_at=str(pd.Timestamp.now(tz="UTC")),
        ),
    )
    return spec.model_dump()
