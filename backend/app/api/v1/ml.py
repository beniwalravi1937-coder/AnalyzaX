"""
AnalyzaX — Phase 11: Machine Learning API Router.
Exposes endpoints for suitability analysis, experiment execution, model comparison,
inference, diagnostics, and experiment history.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.app.core.logging import logger
from backend.app.engines.ml.exceptions import MLException
from backend.app.engines.ml.models import (
    MLExperiment,
    MLExperimentRequest,
    MLModelDefinition,
    MLModelRun,
    MLResult,
    MLTaskType,
    PredictionRequest,
    PredictionResult,
    SuitabilityReport,
)
from backend.app.services.ml_service import ml_service

router = APIRouter(prefix="/ml", tags=["Machine Learning Engine"])


class SuitabilityCheckRequest(BaseModel):
    dataset_id: str
    dataset_version_id: str
    target_column: Optional[str] = None
    task_type: Optional[MLTaskType] = None
    candidate_features: Optional[List[str]] = None


@router.post(
    "/suitability",
    response_model=SuitabilityReport,
    summary="Analyze dataset ML suitability",
)
async def check_ml_suitability(req: SuitabilityCheckRequest):
    """
    Evaluates dataset version for ML readiness, checking row counts, class balance,
    target variance, identifier columns, and data leakage candidates.
    """
    try:
        return ml_service.analyze_suitability(
            dataset_id=req.dataset_id,
            version_id=req.dataset_version_id,
            target_column=req.target_column,
            task_type=req.task_type,
            candidate_features=req.candidate_features,
        )
    except MLException as me:
        raise HTTPException(status_code=400, detail=me.to_dict())
    except Exception as e:
        logger.error(f"Suitability check failed: {e}")
        raise HTTPException(status_code=500, detail={"message": str(e), "error_code": "ML_SUITABILITY_ERROR"})


@router.post(
    "/validate",
    response_model=SuitabilityReport,
    summary="Validate target and feature selection",
)
async def validate_ml_inputs(req: SuitabilityCheckRequest):
    """Validates target and predictor features against dataset version schema."""
    try:
        return ml_service.analyze_suitability(
            dataset_id=req.dataset_id,
            version_id=req.dataset_version_id,
            target_column=req.target_column,
            task_type=req.task_type,
            candidate_features=req.candidate_features,
        )
    except MLException as me:
        raise HTTPException(status_code=400, detail=me.to_dict())
    except Exception as e:
        logger.error(f"Input validation failed: {e}")
        raise HTTPException(status_code=500, detail={"message": str(e), "error_code": "ML_VALIDATION_ERROR"})


@router.get(
    "/models",
    response_model=List[MLModelDefinition],
    summary="List supported machine learning models",
)
async def list_models(task_type: Optional[MLTaskType] = Query(None)):
    """Returns the central registry of supported models and parameter definitions."""
    return ml_service.list_models(task_type)


@router.get(
    "/metrics",
    summary="List supported evaluation metrics",
)
async def list_metrics(task_type: Optional[MLTaskType] = Query(None)):
    """Returns valid metrics by ML task type."""
    metrics_map = {
        "regression": ["rmse", "mae", "r2", "adjusted_r2", "mape", "median_absolute_error"],
        "binary_classification": ["accuracy", "balanced_accuracy", "f1_macro", "f1_weighted", "precision_macro", "recall_macro", "roc_auc", "pr_auc", "log_loss"],
        "multiclass_classification": ["accuracy", "balanced_accuracy", "f1_macro", "f1_weighted", "precision_macro", "recall_macro", "roc_auc", "log_loss"],
        "clustering": ["inertia", "silhouette_score", "calinski_harabasz_score", "davies_bouldin_score"],
    }
    if task_type:
        return {task_type.value: metrics_map.get(task_type.value, [])}
    return metrics_map


@router.post(
    "/experiments",
    response_model=MLResult,
    summary="Create and execute an ML experiment",
)
async def create_experiment(req: MLExperimentRequest):
    """
    Executes a complete ML experiment:
    Preprocessing -> Splitting -> Model Training -> Cross-Validation -> Evaluation -> Persistence -> ChartSpecs.
    """
    try:
        return ml_service.create_and_run_experiment(req)
    except MLException as me:
        raise HTTPException(status_code=400, detail=me.to_dict())
    except Exception as e:
        logger.error(f"Experiment execution failed: {e}")
        raise HTTPException(status_code=500, detail={"message": str(e), "error_code": "ML_TRAINING_ERROR"})


@router.get(
    "/experiments",
    response_model=List[MLExperiment],
    summary="List ML experiments",
)
async def list_experiments(
    dataset_id: Optional[str] = Query(None),
    version_id: Optional[str] = Query(None),
):
    """Lists persistent experiment history, optionally filtered by dataset version."""
    return ml_service.list_experiments(dataset_id=dataset_id, version_id=version_id)


@router.get(
    "/history",
    response_model=List[MLExperiment],
    summary="Get ML experiment history",
)
async def get_history(
    dataset_id: Optional[str] = Query(None),
    version_id: Optional[str] = Query(None),
):
    """Alias for listing experiment history."""
    return ml_service.list_experiments(dataset_id=dataset_id, version_id=version_id)


@router.get(
    "/experiments/{experiment_id}",
    response_model=MLExperiment,
    summary="Get experiment status and metadata",
)
async def get_experiment(experiment_id: str):
    """Retrieves experiment execution status and parameters."""
    try:
        return ml_service.get_experiment(experiment_id)
    except MLException as me:
        raise HTTPException(status_code=404, detail=me.to_dict())


@router.post(
    "/experiments/{experiment_id}/cancel",
    summary="Cancel a running ML experiment",
)
async def cancel_experiment(experiment_id: str):
    """Attempts to cancel an active experiment."""
    try:
        return ml_service.cancel_experiment(experiment_id)
    except MLException as me:
        raise HTTPException(status_code=404, detail=me.to_dict())


@router.get(
    "/experiments/{experiment_id}/results",
    response_model=MLResult,
    summary="Get structured ML result for experiment",
)
async def get_experiment_result(experiment_id: str):
    """Retrieves full structured analytical result including model comparisons, diagnostics, and ChartSpecs."""
    try:
        return ml_service.get_experiment_result(experiment_id)
    except MLException as me:
        raise HTTPException(status_code=404, detail=me.to_dict())


@router.get(
    "/experiments/{experiment_id}/models",
    response_model=List[MLModelRun],
    summary="List model runs for an experiment",
)
async def get_experiment_models(experiment_id: str):
    """Lists all trained model runs and evaluation metrics in an experiment."""
    try:
        res = ml_service.get_experiment_result(experiment_id)
        return res.model_runs
    except MLException as me:
        raise HTTPException(status_code=404, detail=me.to_dict())


@router.get(
    "/models/{model_run_id}",
    response_model=MLModelRun,
    summary="Get details for a specific model run",
)
async def get_model_run_details(model_run_id: str):
    """Retrieves metrics, confusion matrix, and feature importances for a single model run."""
    try:
        run, _ = ml_service.get_model_run(model_run_id)
        return run
    except MLException as me:
        raise HTTPException(status_code=404, detail=me.to_dict())


@router.post(
    "/models/{model_run_id}/predict",
    response_model=PredictionResult,
    summary="Generate predictions from a registered model",
)
async def predict_with_model(model_run_id: str, req: PredictionRequest):
    """
    Executes inference against incoming rows or a compatible dataset version
    using a persistent registered model artifact.
    """
    try:
        return ml_service.predict(model_run_id=model_run_id, request=req)
    except MLException as me:
        raise HTTPException(status_code=400, detail=me.to_dict())
    except Exception as e:
        logger.error(f"Inference execution failed: {e}")
        raise HTTPException(status_code=500, detail={"message": str(e), "error_code": "ML_INFERENCE_ERROR"})
