"""
AnalyzaX — Phase 12: Forecasting Application Service.
Coordinates dataset version resolution, background job lifecycle management,
caching, persistent experiment history, and future prediction generation.
"""

import hashlib
import json
import os
import threading
import time
import uuid
from typing import Any, Dict, List, Optional
import polars as pl

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.forecasting.artifacts import load_forecast_artifact
from backend.app.engines.forecasting.engine import forecasting_engine
from backend.app.engines.forecasting.exceptions import ForecastErrorCode, ForecastException
from backend.app.engines.forecasting.inference import (
    generate_future_timestamps,
    predict_future_points,
)
from backend.app.engines.forecasting.models import (
    ForecastExperiment,
    ForecastExperimentRequest,
    ForecastFrequency,
    ForecastJobStatus,
    ForecastModelDefinition,
    ForecastResult,
    FuturePredictRequest,
    FuturePredictResult,
    TemporalAnalysisSummary,
    TemporalValidationReport,
)
from backend.app.engines.forecasting.registry import forecast_model_registry
from backend.app.services.cleaning import version_service
from backend.app.services.dataset_service import dataset_service


class ForecastingService:
    """Application service coordinating dataset versions, experiments, and inference."""

    def __init__(self) -> None:
        self._storage_dir = os.path.abspath(getattr(settings, "DATA_FORECASTING_DIR", "./data/forecasting"))
        os.makedirs(self._storage_dir, exist_ok=True)
        self._history_file = os.path.join(self._storage_dir, "history.json")

        self._experiments: Dict[str, ForecastExperiment] = {}
        self._results: Dict[str, ForecastResult] = {}
        self._cancelled_jobs: set = set()
        self._cache: Dict[str, ForecastResult] = {}

        self._load_history()

    def _load_history(self) -> None:
        if os.path.exists(self._history_file):
            try:
                with open(self._history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for exp_dict in data.get("experiments", []):
                        exp = ForecastExperiment(**exp_dict)
                        self._experiments[exp.experiment_id] = exp
                    for res_dict in data.get("results", []):
                        res = ForecastResult(**res_dict)
                        self._results[res.experiment_id] = res
            except Exception as e:
                logger.error(f"Error loading forecasting history: {e}")

    def _save_history(self) -> None:
        try:
            payload = {
                "experiments": [e.model_dump() for e in self._experiments.values()],
                "results": [r.model_dump() for r in self._results.values()],
            }
            with open(self._history_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving forecasting history: {e}")

    def _resolve_dataframe(self, dataset_id: str, version_id: Optional[str] = None) -> pl.DataFrame:
        """Resolve dataset version into a Polars DataFrame with fallback checking."""
        if version_id:
            try:
                df = version_service.get_version_dataframe(dataset_id, version_id)
                if df is not None and df.height > 0:
                    return df
            except Exception:
                pass

        # Check direct processed file
        target_file = os.path.join(settings.DATA_PROCESSED_DIR, f"{dataset_id}.parquet")
        if os.path.exists(target_file):
            return pl.read_parquet(target_file)

        raw_file = os.path.join(settings.DATA_UPLOADS_DIR, f"{dataset_id}_raw.parquet")
        if os.path.exists(raw_file):
            return pl.read_parquet(raw_file)

        # Fallback to dataset_service
        dataset = dataset_service.get_dataset(dataset_id)
        if not dataset:
            raise ForecastException(
                code=ForecastErrorCode.FORECAST_DATASET_NOT_FOUND,
                message=f"Dataset '{dataset_id}' not found.",
            )

        if hasattr(dataset, "current_version") and dataset.current_version and dataset.current_version.storage_path:
            p = dataset.current_version.storage_path
            if os.path.exists(p):
                return pl.read_parquet(p)

        raise ForecastException(
            code=ForecastErrorCode.FORECAST_VERSION_NOT_FOUND,
            message=f"Could not resolve storage path for dataset '{dataset_id}'.",
        )

    def get_models(self) -> List[ForecastModelDefinition]:
        return forecast_model_registry.list_models()

    def get_metrics(self) -> List[Dict[str, Any]]:
        return [
            {"id": "rmse", "name": "Root Mean Squared Error (RMSE)", "default": True, "lower_is_better": True},
            {"id": "mae", "name": "Mean Absolute Error (MAE)", "default": False, "lower_is_better": True},
            {"id": "mase", "name": "Mean Absolute Scaled Error (MASE)", "default": False, "lower_is_better": True},
            {"id": "smape", "name": "Symmetric Mean Absolute Percentage Error (sMAPE)", "default": False, "lower_is_better": True},
            {"id": "wape", "name": "Weighted Absolute Percentage Error (WAPE)", "default": False, "lower_is_better": True},
        ]

    def detect_time_candidates(self, dataset_id: str, version_id: str) -> List[Dict[str, Any]]:
        df = self._resolve_dataframe(dataset_id, version_id)
        return forecasting_engine.detect_time_candidates(df)

    def analyze_suitability(
        self,
        dataset_id: str,
        version_id: str,
        time_column: str,
        target_column: str,
        frequency: Optional[ForecastFrequency] = None,
    ) -> TemporalValidationReport:
        df = self._resolve_dataframe(dataset_id, version_id)
        return forecasting_engine.validate_series(
            df=df,
            time_column=time_column,
            target_column=target_column,
            user_frequency=frequency,
        )

    def analyze_temporal(
        self,
        dataset_id: str,
        version_id: str,
        time_column: str,
        target_column: str,
        frequency: ForecastFrequency,
    ) -> TemporalAnalysisSummary:
        df = self._resolve_dataframe(dataset_id, version_id)
        return forecasting_engine.analyze_temporal(
            df=df,
            time_column=time_column,
            target_column=target_column,
            frequency=frequency,
        )

    def submit_experiment(
        self,
        request: ForecastExperimentRequest,
        run_sync: bool = False,
    ) -> ForecastExperiment:
        """Create and launch forecasting experiment."""
        exp_id = f"fexp_{uuid.uuid4().hex[:10]}"
        df = self._resolve_dataframe(request.dataset_id, request.dataset_version_id)

        inferred_freq = request.frequency or ForecastFrequency.DAILY

        experiment = ForecastExperiment(
            experiment_id=exp_id,
            dataset_id=request.dataset_id,
            dataset_version_id=request.dataset_version_id,
            time_column=request.time_column,
            target_column=request.target_column,
            frequency=inferred_freq,
            forecast_horizon=request.forecast_horizon,
            validation_folds=request.validation_folds,
            models=request.models,
            primary_metric=request.primary_metric,
            confidence_level=request.confidence_level,
            status=ForecastJobStatus.QUEUED,
            progress_stage="VALIDATING",
            progress_percent=10,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        self._experiments[exp_id] = experiment

        workspace_id = getattr(request, "workspace_id", None)
        reservation_id = None
        if workspace_id:
            from backend.app.services.usage import quota_service
            from backend.app.engines.usage.metrics import UsageMetrics

            quota_service.enforce_feature(workspace_id, "FORECASTING")
            res = quota_service.reserve_quota(
                workspace_id=workspace_id,
                metric_key=UsageMetrics.FORECAST_RUNS.key,
                quantity=1.0,
                operation_id=exp_id,
                resource_type="forecast_experiment",
                resource_id=exp_id,
            )
            reservation_id = res.reservation_id

        def _execute():
            experiment.status = ForecastJobStatus.RUNNING
            experiment.progress_stage = "BACKTESTING"
            experiment.progress_percent = 30
            try:
                if exp_id in self._cancelled_jobs:
                    experiment.status = ForecastJobStatus.CANCELLED
                    if reservation_id:
                        from backend.app.services.usage import quota_service
                        quota_service.release_quota(reservation_id)
                    return

                result = forecasting_engine.execute_experiment(df=df, request=request, experiment_id=exp_id)

                if exp_id in self._cancelled_jobs:
                    experiment.status = ForecastJobStatus.CANCELLED
                    if reservation_id:
                        from backend.app.services.usage import quota_service
                        quota_service.release_quota(reservation_id)
                    return

                self._results[exp_id] = result
                experiment.status = ForecastJobStatus.COMPLETED
                experiment.progress_stage = "COMPLETED"
                experiment.progress_percent = 100
                experiment.completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                self._save_history()

                # Finalize reserved quota on successful completion
                if reservation_id:
                    from backend.app.services.usage import quota_service
                    quota_service.finalize_quota(reservation_id)

            except Exception as e:
                logger.error(f"Forecasting experiment {exp_id} failed: {e}")
                experiment.status = ForecastJobStatus.FAILED
                experiment.error_message = str(e)
                experiment.completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                self._save_history()
                # Release quota on failure
                if reservation_id:
                    from backend.app.services.usage import quota_service
                    quota_service.release_quota(reservation_id)

        if run_sync:
            _execute()
        else:
            thread = threading.Thread(target=_execute, daemon=True)
            thread.start()

        return experiment

    def get_experiment(self, experiment_id: str) -> Optional[ForecastExperiment]:
        return self._experiments.get(experiment_id)

    def cancel_experiment(self, experiment_id: str) -> bool:
        if experiment_id in self._experiments:
            self._cancelled_jobs.add(experiment_id)
            exp = self._experiments[experiment_id]
            if exp.status in (ForecastJobStatus.QUEUED, ForecastJobStatus.RUNNING):
                exp.status = ForecastJobStatus.CANCELLED
                exp.completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                self._save_history()
                return True
        return False

    def get_experiment_results(self, experiment_id: str) -> Optional[ForecastResult]:
        return self._results.get(experiment_id)

    def list_experiments(
        self,
        dataset_id: Optional[str] = None,
        dataset_version_id: Optional[str] = None,
    ) -> List[ForecastExperiment]:
        items = list(self._experiments.values())
        if dataset_id:
            items = [e for e in items if e.dataset_id == dataset_id]
        if dataset_version_id:
            items = [e for e in items if e.dataset_version_id == dataset_version_id]
        return sorted(items, key=lambda x: x.created_at, reverse=True)

    def get_history(self) -> Dict[str, Any]:
        return {
            "experiments": [e.model_dump() for e in self._experiments.values()],
            "total_count": len(self._experiments),
        }

    def predict_future(self, request: FuturePredictRequest) -> FuturePredictResult:
        """Run inference on an existing trained model run."""
        # Find the experiment containing this run_id
        target_exp_id: Optional[str] = None
        target_run = None
        target_result: Optional[ForecastResult] = None

        for exp_id, res in self._results.items():
            for m in res.models:
                if m.run_id == request.run_id:
                    target_exp_id = exp_id
                    target_run = m
                    target_result = res
                    break
            if target_run:
                break

        if not target_run or not target_exp_id or not target_result:
            raise ForecastException(
                code=ForecastErrorCode.FORECAST_INFERENCE_ERROR,
                message=f"Model run '{request.run_id}' not found.",
            )

        estimator, manifest = load_forecast_artifact(target_exp_id, request.run_id)

        last_ts = target_result.historical_timestamps[-1]
        future_ts = generate_future_timestamps(
            last_timestamp_str=last_ts,
            steps=request.periods,
            pandas_freq_str=manifest.get("pandas_frequency_str", "D"),
        )

        conf = request.confidence_level or target_result.confidence_level
        points = predict_future_points(
            estimator=estimator,
            steps=request.periods,
            future_timestamps=future_ts,
            confidence_level=conf,
        )

        return FuturePredictResult(
            prediction_id=f"fpred_{uuid.uuid4().hex[:10]}",
            run_id=request.run_id,
            model_id=target_run.model_id,
            model_name=target_run.model_name,
            forecast_points=points,
            confidence_level=conf,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )


forecasting_service = ForecastingService()
