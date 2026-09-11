"""
AnalyzaX — Phase 12: Central Forecasting Domain Engine Facade.
Coordinates temporal validation, frequency detection, chronological splitting,
rolling-origin backtesting, model training, evaluation, diagnostics, artifact persistence,
and Phase 9 ChartSpec visualization generation.
"""

import time
import uuid
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import polars as pl

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.forecasting.artifacts import save_forecast_artifact
from backend.app.engines.forecasting.exceptions import ForecastErrorCode, ForecastException
from backend.app.engines.forecasting.inference import generate_future_timestamps
from backend.app.engines.forecasting.interpretation import generate_forecast_findings
from backend.app.engines.forecasting.models import (
    ForecastExperimentRequest,
    ForecastFrequency,
    ForecastModelRun,
    ForecastResult,
    TemporalAnalysisSummary,
    TemporalValidationReport,
)
from backend.app.engines.forecasting.registry import forecast_model_registry
from backend.app.engines.forecasting.splitting import generate_rolling_origin_folds
from backend.app.engines.forecasting.temporal_analysis import run_temporal_analysis
from backend.app.engines.forecasting.training import build_estimator, train_and_backtest_model
from backend.app.engines.forecasting.validation import (
    detect_time_column_candidates,
    validate_time_series,
)
from backend.app.engines.forecasting.visualization.chart_specs import (
    build_acf_chart_spec,
    build_decomposition_chart_spec,
    build_forecast_chart_spec,
    build_model_comparison_chart_spec,
    build_residual_chart_spec,
)


class ForecastingEngine:
    """Pure domain engine executing deterministic time-series forecasting without HTTP/API dependencies."""

    def detect_time_candidates(self, df: pl.DataFrame) -> List[Dict[str, Any]]:
        return detect_time_column_candidates(df)

    def validate_series(
        self,
        df: pl.DataFrame,
        time_column: str,
        target_column: str,
        user_frequency: Optional[ForecastFrequency] = None,
    ) -> TemporalValidationReport:
        return validate_time_series(df, time_column, target_column, user_frequency)

    def analyze_temporal(
        self,
        df: pl.DataFrame,
        time_column: str,
        target_column: str,
        frequency: ForecastFrequency,
    ) -> TemporalAnalysisSummary:
        time_s = pd.to_datetime(df[time_column].to_pandas(), errors="coerce")
        val_mask = time_s.notnull()
        sorted_indices = time_s[val_mask].sort_values().index
        
        timestamps = [str(time_s.loc[i]) for i in sorted_indices]
        y = pd.to_numeric(df[target_column].to_pandas().loc[sorted_indices], errors="coerce").fillna(0.0).to_numpy()
        return run_temporal_analysis(timestamps, y, frequency)

    def execute_experiment(
        self,
        df: pl.DataFrame,
        request: ForecastExperimentRequest,
        experiment_id: Optional[str] = None,
    ) -> ForecastResult:
        """Run complete deterministic forecasting experiment."""
        start_time = time.perf_counter()
        experiment_id = experiment_id or f"fexp_{uuid.uuid4().hex[:10]}"

        # 1. Enforce resource limits
        if len(df) > settings.FORECAST_MAX_ROWS:
            raise ForecastException(
                code=ForecastErrorCode.FORECAST_RESOURCE_LIMIT_EXCEEDED,
                message=f"Dataset row count ({len(df)}) exceeds limit ({settings.FORECAST_MAX_ROWS}).",
            )
        if request.forecast_horizon > settings.FORECAST_MAX_HORIZON:
            raise ForecastException(
                code=ForecastErrorCode.FORECAST_RESOURCE_LIMIT_EXCEEDED,
                message=f"Forecast horizon ({request.forecast_horizon}) exceeds limit ({settings.FORECAST_MAX_HORIZON}).",
            )
        if len(request.models) > settings.FORECAST_MAX_MODELS_PER_EXPERIMENT:
            raise ForecastException(
                code=ForecastErrorCode.FORECAST_RESOURCE_LIMIT_EXCEEDED,
                message=f"Requested model count ({len(request.models)}) exceeds limit ({settings.FORECAST_MAX_MODELS_PER_EXPERIMENT}).",
            )

        # 2. Temporal validation
        val_report = self.validate_series(
            df=df,
            time_column=request.time_column,
            target_column=request.target_column,
            user_frequency=request.frequency,
        )
        if not val_report.is_valid:
            critical_issues = [i.description for i in val_report.issues if i.severity.value == "CRITICAL"]
            raise ForecastException(
                code=ForecastErrorCode.FORECAST_INVALID_TARGET,
                message=f"Time series validation failed: {'; '.join(critical_issues)}",
            )

        # 3. Prepare sorted chronological arrays
        time_s = pd.to_datetime(df[request.time_column].to_pandas(), errors="coerce")
        val_mask = time_s.notnull()
        sorted_indices = time_s[val_mask].sort_values().index

        full_timestamps = [str(time_s.loc[i]) for i in sorted_indices]
        full_y = pd.to_numeric(df[request.target_column].to_pandas().loc[sorted_indices], errors="coerce").fillna(0.0).to_numpy()

        # 4. Generate future timestamps for horizon
        last_ts_str = full_timestamps[-1]
        future_ts = generate_future_timestamps(
            last_timestamp_str=last_ts_str,
            steps=request.forecast_horizon,
            pandas_freq_str=val_report.pandas_frequency_str,
        )

        # 5. Generate rolling-origin validation folds
        folds = generate_rolling_origin_folds(
            timestamps=full_timestamps,
            y=full_y,
            horizon=request.forecast_horizon,
            n_folds=request.validation_folds,
            window_type=request.training_window_type,
            fixed_window_size=request.training_window_size,
        )

        # 6. Model training & backtesting
        model_runs: List[ForecastModelRun] = []
        for model_id in request.models:
            model_def = forecast_model_registry.get(model_id)
            if not model_def:
                continue

            user_params = request.model_parameters.get(model_id, {})
            validated_params = forecast_model_registry.validate_parameters(model_id, user_params)

            # Auto-configure seasonal period if not set and seasonality was detected
            if model_def.supports_seasonality and "seasonal_period" in model_def.default_parameters:
                if "seasonal_period" not in user_params:
                    # Default to 7 for daily, 12 for monthly
                    sp = 7 if val_report.inferred_frequency == ForecastFrequency.DAILY else 12
                    validated_params["seasonal_period"] = sp
            if model_id == "sarima" and "m" not in user_params:
                sp = 7 if val_report.inferred_frequency == ForecastFrequency.DAILY else 12
                validated_params["m"] = sp

            run = train_and_backtest_model(
                model_id=model_id,
                parameters=validated_params,
                folds=folds,
                full_timestamps=full_timestamps,
                full_y=full_y,
                future_timestamps=future_ts,
                horizon=request.forecast_horizon,
                confidence_level=request.confidence_level,
            )

            # Save artifact
            try:
                estimator = build_estimator(model_id, validated_params)
                estimator.fit(full_y)
                art_ref = save_forecast_artifact(
                    experiment_id=experiment_id,
                    run_id=run.run_id,
                    estimator=estimator,
                    dataset_id=request.dataset_id,
                    dataset_version_id=request.dataset_version_id,
                    time_column=request.time_column,
                    target_column=request.target_column,
                    frequency=val_report.inferred_frequency.value,
                    pandas_frequency_str=val_report.pandas_frequency_str,
                    model_id=model_id,
                    parameters=validated_params,
                )
                run.artifact_reference = art_ref
            except Exception as e:
                logger.warning(f"Could not persist forecast artifact for {run.run_id}: {str(e)}")

            model_runs.append(run)

        if not model_runs:
            raise ForecastException(
                code=ForecastErrorCode.FORECAST_TRAINING_ERROR,
                message="No forecasting models were successfully trained.",
            )

        # 7. Select best model based on primary metric
        primary_metric = request.primary_metric.lower()
        best_run = min(
            model_runs,
            key=lambda r: getattr(r.backtest_result.mean_metrics, primary_metric, float("inf")) or float("inf"),
        )

        # 8. Run temporal analysis
        temporal_summary = run_temporal_analysis(
            timestamps=full_timestamps,
            y=full_y,
            frequency=val_report.inferred_frequency,
        )

        # 9. Generate structured findings
        findings = generate_forecast_findings(
            validation=val_report,
            temporal_analysis=temporal_summary,
            model_runs=model_runs,
            best_model_run=best_run,
            primary_metric=primary_metric,
        )

        # 10. Generate Phase 9 ChartSpecs
        visualizations: List[Dict[str, Any]] = []

        # (a) Main forecast chart
        fc_spec = build_forecast_chart_spec(
            historical_timestamps=full_timestamps,
            historical_values=[float(v) for v in full_y],
            forecast_points=best_run.future_forecasts,
            model_name=best_run.model_name,
            dataset_id=request.dataset_id,
            dataset_version_id=request.dataset_version_id,
            target_column=request.target_column,
            confidence_level=request.confidence_level,
        )
        if fc_spec:
            visualizations.append(fc_spec)

        # (b) Model comparison chart
        cmp_spec = build_model_comparison_chart_spec(
            runs=model_runs,
            primary_metric=primary_metric,
            dataset_id=request.dataset_id,
            dataset_version_id=request.dataset_version_id,
        )
        if cmp_spec:
            visualizations.append(cmp_spec)

        # (c) Decomposition chart
        decomp_spec = build_decomposition_chart_spec(
            decomp=temporal_summary.decomposition,
            dataset_id=request.dataset_id,
            dataset_version_id=request.dataset_version_id,
            target_column=request.target_column,
        )
        if decomp_spec:
            visualizations.append(decomp_spec)

        # (d) ACF chart
        acf_spec = build_acf_chart_spec(
            acf_result=temporal_summary.acf,
            dataset_id=request.dataset_id,
            dataset_version_id=request.dataset_version_id,
            target_column=request.target_column,
        )
        if acf_spec:
            visualizations.append(acf_spec)

        # (e) Residual chart
        resid_spec = build_residual_chart_spec(
            diag=best_run.residual_diagnostics,
            dataset_id=request.dataset_id,
            dataset_version_id=request.dataset_version_id,
            model_name=best_run.model_name,
        )
        if resid_spec:
            visualizations.append(resid_spec)

        provenance = {
            "dataset_id": request.dataset_id,
            "dataset_version_id": request.dataset_version_id,
            "experiment_id": experiment_id,
            "engine_version": "1.0.0",
            "execution_duration_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            "library_versions": {"statsmodels": "0.14.0", "polars": pl.__version__},
        }

        return ForecastResult(
            result_id=f"fres_{uuid.uuid4().hex[:10]}",
            experiment_id=experiment_id,
            dataset_id=request.dataset_id,
            dataset_version_id=request.dataset_version_id,
            time_column=request.time_column,
            target_column=request.target_column,
            frequency=val_report.inferred_frequency,
            pandas_frequency_str=val_report.pandas_frequency_str,
            forecast_horizon=request.forecast_horizon,
            primary_metric=primary_metric,
            confidence_level=request.confidence_level,
            historical_timestamps=full_timestamps,
            historical_values=[round(float(v), 4) for v in full_y],
            models=model_runs,
            best_model_id=best_run.model_id,
            validation_report=val_report,
            temporal_analysis=temporal_summary,
            findings=findings,
            visualizations=visualizations,
            warnings=val_report.warnings,
            limitations=[
                "Future predictions assume continuation of historical regime and seasonal patterns.",
                "Prediction intervals represent statistical uncertainty and widen across extending horizons.",
            ],
            provenance=provenance,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )


forecasting_engine = ForecastingEngine()
