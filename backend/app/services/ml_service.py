"""
AnalyzaX — Phase 11: Machine Learning Application Service.
Coordinates dataset version resolution, experiment lifecycle management,
caching, background execution, persistent history, and inference.
"""

import hashlib
import json
import os
import threading
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import polars as pl

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.ml.artifacts import get_models_storage_dir, load_model_artifact
from backend.app.engines.ml.engine import ml_engine
from backend.app.engines.ml.exceptions import MLErrorCode, MLException
from backend.app.engines.ml.models import (
    MLExperiment,
    MLExperimentRequest,
    MLJobStatus,
    MLModelDefinition,
    MLModelRun,
    MLResult,
    MLTaskType,
    PredictionRequest,
    PredictionResult,
    SuitabilityReport,
)
from backend.app.engines.ml.registry import model_registry
from backend.app.services.cleaning import version_service
from backend.app.services.dataset_service import dataset_service


class MLService:
    """Application service coordinating dataset versions, experiments, and inference."""

    def __init__(self) -> None:
        self._storage_dir = os.path.abspath(getattr(settings, "DATA_ML_DIR", "./data/ml"))
        os.makedirs(self._storage_dir, exist_ok=True)
        self._history_file = os.path.join(self._storage_dir, "history.json")

        self._experiments: Dict[str, MLExperiment] = {}
        self._results: Dict[str, MLResult] = {}
        self._cancelled_jobs: set = set()
        self._cache: Dict[str, MLResult] = {}

        self._load_history()

    def _load_history(self) -> None:
        if os.path.exists(self._history_file):
            try:
                with open(self._history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for exp_dict in data.get("experiments", []):
                        exp = MLExperiment(**exp_dict)
                        self._experiments[exp.experiment_id] = exp
                    for res_dict in data.get("results", []):
                        res = MLResult(**res_dict)
                        self._results[res.experiment_id] = res
            except Exception as e:
                logger.warning(f"Failed to load ML history: {e}")

    def _save_history(self) -> None:
        try:
            payload = {
                "experiments": [e.model_dump() for e in self._experiments.values()],
                "results": [r.model_dump() for r in self._results.values()],
            }
            with open(self._history_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to save ML history: {e}")

    def _resolve_dataset_df(self, dataset_id: str, version_id: str) -> pl.DataFrame:
        """Resolves immutable Polars DataFrame for specific dataset version."""
        # 1. Verify dataset exists
        try:
            ds = dataset_service.get_dataset(dataset_id)
            if not ds:
                raise MLException(f"Dataset '{dataset_id}' not found.", MLErrorCode.ML_DATASET_NOT_FOUND)
        except Exception:
            raise MLException(f"Dataset '{dataset_id}' not found.", MLErrorCode.ML_DATASET_NOT_FOUND)

        # 2. Resolve version
        try:
            df = version_service.get_version_dataframe(dataset_id, version_id)
            if df is None or df.height == 0:
                raise MLException(
                    f"Version '{version_id}' of dataset '{dataset_id}' has no data.",
                    MLErrorCode.ML_DATASET_VERSION_NOT_FOUND,
                )
            return df
        except MLException:
            raise
        except Exception as e:
            raise MLException(
                f"Failed to resolve dataset version '{version_id}': {e}",
                MLErrorCode.ML_DATASET_VERSION_NOT_FOUND,
            )

    def analyze_suitability(
        self,
        dataset_id: str,
        version_id: str,
        target_column: Optional[str] = None,
        task_type: Optional[MLTaskType] = None,
        candidate_features: Optional[List[str]] = None,
    ) -> SuitabilityReport:
        df = self._resolve_dataset_df(dataset_id, version_id)
        return ml_engine.analyze_suitability(
            df=df,
            target_column=target_column,
            task_type=task_type,
            candidate_features=candidate_features,
        )

    def list_models(self, task_type: Optional[MLTaskType] = None) -> List[MLModelDefinition]:
        return model_registry.list_models(task_type)

    def create_and_run_experiment(self, request: MLExperimentRequest) -> MLResult:
        """
        Creates an experiment record and executes model training deterministically.
        """
        exp_id = f"exp_{uuid.uuid4().hex[:12]}"
        df = self._resolve_dataset_df(request.dataset_id, request.dataset_version_id)

        # Compute deterministic configuration hash for caching
        config_hash = hashlib.sha256(
            json.dumps(
                {
                    "dataset_id": request.dataset_id,
                    "dataset_version_id": request.dataset_version_id,
                    "task": request.task_type.value,
                    "target": request.target_column,
                    "features": sorted(request.feature_columns),
                    "split": request.split.model_dump(),
                    "models": sorted(request.models),
                    "seed": request.random_seed,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()[:16]

        # Check in-memory cache
        if config_hash in self._cache:
            cached = self._cache[config_hash]
            logger.info(f"Returning cached ML experiment result for hash {config_hash}")
            return cached

        # Record experiment as RUNNING
        experiment = MLExperiment(
            experiment_id=exp_id,
            dataset_id=request.dataset_id,
            dataset_version_id=request.dataset_version_id,
            task_type=request.task_type,
            target_column=request.target_column,
            feature_columns=request.feature_columns,
            preprocessing=request.preprocessing,
            split=request.split,
            cross_validation=request.cross_validation,
            models=request.models,
            primary_metric=request.primary_metric or "default",
            random_seed=request.random_seed,
            status=MLJobStatus.RUNNING,
            created_at=str(pd.Timestamp.now(tz="UTC")),
            config_hash=config_hash,
        )
        self._experiments[exp_id] = experiment

        workspace_id = getattr(request, "workspace_id", None)
        reservation_id = None
        if workspace_id:
            from backend.app.services.usage import quota_service
            from backend.app.engines.usage.metrics import UsageMetrics

            quota_service.enforce_feature(workspace_id, "MACHINE_LEARNING")
            res = quota_service.reserve_quota(
                workspace_id=workspace_id,
                metric_key=UsageMetrics.ML_EXPERIMENTS.key,
                quantity=1.0,
                operation_id=exp_id,
                resource_type="ml_experiment",
                resource_id=exp_id,
            )
            reservation_id = res.reservation_id

        try:
            start_t = time.perf_counter()
            result = ml_engine.execute_experiment(df=df, request=request, experiment_id=exp_id)
            duration_ms = int((time.perf_counter() - start_t) * 1000)

            # Check if cancelled during execution
            if exp_id in self._cancelled_jobs:
                experiment.status = MLJobStatus.CANCELLED
                experiment.error_message = "Experiment was cancelled by user request."
                if reservation_id:
                    from backend.app.services.usage import quota_service
                    quota_service.release_quota(reservation_id)
                raise MLException("Experiment was cancelled.", MLErrorCode.ML_CANCELLED)

            experiment.status = MLJobStatus.COMPLETED
            experiment.completed_at = str(pd.Timestamp.now(tz="UTC"))
            experiment.duration_ms = duration_ms

            self._results[exp_id] = result
            self._cache[config_hash] = result
            self._save_history()

            # Finalize reserved quota
            if reservation_id:
                from backend.app.services.usage import quota_service
                quota_service.finalize_quota(reservation_id)

            return result

        except MLException as me:
            experiment.status = MLJobStatus.FAILED
            experiment.error_message = me.message
            self._save_history()
            if reservation_id:
                from backend.app.services.usage import quota_service
                quota_service.release_quota(reservation_id)
            raise
        except Exception as e:
            experiment.status = MLJobStatus.FAILED
            experiment.error_message = str(e)
            self._save_history()
            if reservation_id:
                from backend.app.services.usage import quota_service
                quota_service.release_quota(reservation_id)
            raise MLException(f"ML experiment failed: {e}", MLErrorCode.ML_TRAINING_ERROR)

    def cancel_experiment(self, experiment_id: str) -> Dict[str, Any]:
        if experiment_id not in self._experiments:
            raise MLException(f"Experiment '{experiment_id}' not found.", MLErrorCode.ML_MODEL_NOT_FOUND)
        self._cancelled_jobs.add(experiment_id)
        exp = self._experiments[experiment_id]
        if exp.status == MLJobStatus.RUNNING:
            exp.status = MLJobStatus.CANCELLED
            exp.error_message = "Cancelled by user."
            self._save_history()
        return {"experiment_id": experiment_id, "status": exp.status.value}

    def get_experiment(self, experiment_id: str) -> MLExperiment:
        if experiment_id not in self._experiments:
            raise MLException(f"Experiment '{experiment_id}' not found.", MLErrorCode.ML_MODEL_NOT_FOUND)
        return self._experiments[experiment_id]

    def get_experiment_result(self, experiment_id: str) -> MLResult:
        if experiment_id not in self._results:
            raise MLException(f"Result for experiment '{experiment_id}' not found.", MLErrorCode.ML_MODEL_NOT_FOUND)
        return self._results[experiment_id]

    def list_experiments(
        self,
        dataset_id: Optional[str] = None,
        version_id: Optional[str] = None,
    ) -> List[MLExperiment]:
        exps = list(self._experiments.values())
        if dataset_id:
            exps = [e for e in exps if e.dataset_id == dataset_id]
        if version_id:
            exps = [e for e in exps if e.dataset_version_id == version_id]
        return sorted(exps, key=lambda e: e.created_at, reverse=True)

    def get_model_run(self, model_run_id: str) -> Tuple[MLModelRun, str]:
        """Finds a model run across stored experiment results, returning (run, experiment_id)."""
        for exp_id, res in self._results.items():
            for run in res.model_runs:
                if run.model_run_id == model_run_id:
                    return run, exp_id
        raise MLException(f"Model run '{model_run_id}' not found.", MLErrorCode.ML_MODEL_NOT_FOUND)

    def predict(self, model_run_id: str, request: PredictionRequest) -> PredictionResult:
        """Executes prediction using a registered model run."""
        run, exp_id = self.get_model_run(model_run_id)

        # Prepare DataFrame
        if request.rows:
            df_input = pd.DataFrame(request.rows)
        elif request.dataset_id and request.dataset_version_id:
            pl_df = self._resolve_dataset_df(request.dataset_id, request.dataset_version_id)
            df_input = pl_df.to_pandas()
        else:
            raise MLException(
                "PredictionRequest must specify either 'rows' or both 'dataset_id' and 'dataset_version_id'.",
                MLErrorCode.ML_INFERENCE_ERROR,
            )

        return ml_engine.predict(
            experiment_id=exp_id,
            model_run_id=model_run_id,
            df_input=df_input,
            dataset_id=request.dataset_id,
            dataset_version_id=request.dataset_version_id,
        )


ml_service = MLService()
