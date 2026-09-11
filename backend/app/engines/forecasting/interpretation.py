"""
AnalyzaX — Phase 12: Forecasting Findings & Interpretation Engine.
Generates deterministic, evidence-based analytical findings without using an LLM.
"""

from typing import List, Optional
import uuid

from backend.app.engines.forecasting.models import (
    FindingCategory,
    ForecastFinding,
    ForecastModelRun,
    QualitySeverity,
    TemporalAnalysisSummary,
    TemporalValidationReport,
)


def generate_forecast_findings(
    validation: TemporalValidationReport,
    temporal_analysis: TemporalAnalysisSummary,
    model_runs: List[ForecastModelRun],
    best_model_run: ForecastModelRun,
    primary_metric: str,
) -> List[ForecastFinding]:
    """Produce deterministic, structured time-series findings."""
    findings: List[ForecastFinding] = []

    # 1. Data Quality / Regularity
    if validation.missing_timestamp_count > 0:
        findings.append(
            ForecastFinding(
                finding_id=f"fnd_{uuid.uuid4().hex[:8]}",
                category=FindingCategory.DATA_QUALITY,
                severity=QualitySeverity.MEDIUM if validation.missing_timestamp_count < 10 else QualitySeverity.HIGH,
                title="Missing Timestamps in Historical Grid",
                description=f"Identified {validation.missing_timestamp_count} missing timestamps based on inferred {validation.inferred_frequency.value} frequency.",
                evidence={"missing_count": validation.missing_timestamp_count, "regularity": validation.regularity.value},
                methodology="Calculated difference between expected regular calendar date range and observed unique timestamps.",
                limitations="Irregular historical intervals can introduce slight bias into lag-dependent estimators.",
            )
        )

    # 2. Trend Finding
    trend = temporal_analysis.trend
    if trend.detected:
        findings.append(
            ForecastFinding(
                finding_id=f"fnd_{uuid.uuid4().hex[:8]}",
                category=FindingCategory.TREND,
                severity=QualitySeverity.INFO,
                title=f"Significant {trend.direction.value.title()} Trend",
                description=trend.description,
                evidence={"slope": trend.slope, "p_value": trend.p_value, "r_squared": trend.r_squared},
                methodology="Ordinary Least Squares (OLS) linear regression on chronological observation indices.",
                limitations="Assumes constant linear trajectory; does not model non-linear saturation or structural breaks.",
            )
        )

    # 3. Seasonality Finding
    seas = temporal_analysis.seasonality
    if seas.detected:
        findings.append(
            ForecastFinding(
                finding_id=f"fnd_{uuid.uuid4().hex[:8]}",
                category=FindingCategory.SEASONALITY,
                severity=QualitySeverity.INFO,
                title=f"Dominant Seasonality ({seas.frequency_label})",
                description=seas.description,
                evidence=seas.evidence,
                methodology="Autocorrelation Function (ACF) local peak analysis across domain calendar frequencies.",
                limitations="Requires continuous historical periods to maintain reliable cycle alignment.",
            )
        )

    # 4. Model Performance & Baseline Comparison
    best_metric_val = getattr(best_model_run.backtest_result.mean_metrics, primary_metric.lower(), None)
    metric_str = f"{primary_metric.upper()} = {best_metric_val}" if best_metric_val is not None else ""

    # Compare against Naive baseline if present
    naive_run = next((m for m in model_runs if m.model_id == "naive"), None)
    baseline_note = ""
    if naive_run and naive_run.run_id != best_model_run.run_id:
        naive_val = getattr(naive_run.backtest_result.mean_metrics, primary_metric.lower(), None)
        if naive_val and best_metric_val and naive_val > 0:
            pct_gain = ((naive_val - best_metric_val) / naive_val) * 100.0
            baseline_note = f" (an improvement of {pct_gain:.1f}% over the Naive baseline)"

    findings.append(
        ForecastFinding(
            finding_id=f"fnd_{uuid.uuid4().hex[:8]}",
            category=FindingCategory.MODEL_PERFORMANCE,
            severity=QualitySeverity.INFO,
            title=f"Top Performing Model: {best_model_run.model_name}",
            description=f"Model {best_model_run.model_name} achieved the best out-of-sample backtest score ({metric_str}){baseline_note} across walk-forward validation folds.",
            evidence={
                "model_id": best_model_run.model_id,
                "primary_metric": primary_metric,
                "score": best_metric_val,
            },
            methodology="Rolling-origin walk-forward validation preserving strict historical chronology.",
            limitations="Future operational accuracy depends on pattern stability across subsequent forecast horizons.",
        )
    )

    # 5. Residual Diagnostics
    diag = best_model_run.residual_diagnostics
    if diag and diag.autocorrelation_detected:
        findings.append(
            ForecastFinding(
                finding_id=f"fnd_{uuid.uuid4().hex[:8]}",
                category=FindingCategory.MODEL_DIAGNOSTICS,
                severity=QualitySeverity.LOW,
                title="Remaining Residual Autocorrelation",
                description="Ljung-Box diagnostic indicates statistically significant autocorrelation in forecast residuals (p < 0.05). Some predictable temporal patterns may remain uncaptured.",
                evidence={"ljung_box_stat": diag.ljung_box_stat, "p_value": diag.ljung_box_pvalue},
                methodology="Ljung-Box portmanteau test for white noise residuals.",
                limitations="Higher lag parameters (e.g. higher ARIMA orders or seasonality) may improve fit if history allows.",
            )
        )

    # 6. Prediction Interval Uncertainty
    if best_model_run.future_forecasts:
        pts = best_model_run.future_forecasts
        first_width = (pts[0].upper_bound - pts[0].lower_bound) if pts[0].upper_bound is not None and pts[0].lower_bound is not None else 0.0
        last_width = (pts[-1].upper_bound - pts[-1].lower_bound) if pts[-1].upper_bound is not None and pts[-1].lower_bound is not None else 0.0

        if last_width > first_width and first_width > 0:
            findings.append(
                ForecastFinding(
                    finding_id=f"fnd_{uuid.uuid4().hex[:8]}",
                    category=FindingCategory.FORECAST_UNCERTAINTY,
                    severity=QualitySeverity.INFO,
                    title="Expanding Forecast Uncertainty Interval",
                    description=f"Prediction interval width expands from {first_width:.2f} at Step 1 to {last_width:.2f} at Step {len(pts)}, reflecting standard compound variance growth over long forecast horizons.",
                    evidence={"initial_width": round(first_width, 2), "terminal_width": round(last_width, 2)},
                    methodology="Analytical standard error expansion based on Gaussian disturbance assumptions.",
                )
            )

    return findings
