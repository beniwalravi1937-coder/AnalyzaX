"""
AnalyzaX — Phase 12: Forecasting REST API Endpoints.
Exposes version-aware endpoints for temporal validation, frequency detection,
decomposition, model training, backtesting, diagnostics, and future inference.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.app.engines.forecasting.exceptions import ForecastException
from backend.app.engines.forecasting.models import (
    ForecastExperiment,
    ForecastExperimentRequest,
    ForecastFrequency,
    ForecastModelDefinition,
    ForecastPoint,
    ForecastResult,
    FuturePredictRequest,
    FuturePredictResult,
    ResidualDiagnostics,
    TemporalAnalysisSummary,
    TemporalValidationReport,
)
from backend.app.services.forecasting_service import forecasting_service

router = APIRouter(prefix="/forecasting", tags=["Forecasting"])


class SuitabilityCheckRequest(BaseModel):
    dataset_id: str
    dataset_version_id: str
    time_column: str
    target_column: str
    frequency: Optional[ForecastFrequency] = None


class TemporalAnalysisRequest(BaseModel):
    dataset_id: str
    dataset_version_id: str
    time_column: str
    target_column: str
    frequency: ForecastFrequency = ForecastFrequency.DAILY


@router.get("/models", response_model=List[ForecastModelDefinition])
async def get_forecasting_models():
    """Retrieve list of supported forecasting algorithms from the central registry."""
    return forecasting_service.get_models()


@router.get("/metrics")
async def get_forecasting_metrics():
    """Retrieve supported forecasting evaluation metrics."""
    return forecasting_service.get_metrics()


@router.get("/candidates/{dataset_id}/{version_id}")
async def get_time_candidates(dataset_id: str, version_id: str):
    """Detect and rank candidate time/date columns for a dataset version."""
    try:
        candidates = forecasting_service.detect_time_candidates(dataset_id, version_id)
        return {"candidates": candidates}
    except ForecastException as fe:
        raise HTTPException(status_code=400, detail=fe.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": str(e)})


@router.post("/suitability", response_model=TemporalValidationReport)
async def check_suitability(request: SuitabilityCheckRequest):
    """Run temporal validation, frequency detection, and data quality check."""
    try:
        return forecasting_service.analyze_suitability(
            dataset_id=request.dataset_id,
            version_id=request.dataset_version_id,
            time_column=request.time_column,
            target_column=request.target_column,
            frequency=request.frequency,
        )
    except ForecastException as fe:
        raise HTTPException(status_code=400, detail=fe.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": str(e)})


@router.post("/analyze", response_model=TemporalAnalysisSummary)
async def analyze_temporal_properties(request: TemporalAnalysisRequest):
    """Compute trend, seasonality, ACF/PACF, and classical decomposition."""
    try:
        return forecasting_service.analyze_temporal(
            dataset_id=request.dataset_id,
            version_id=request.dataset_version_id,
            time_column=request.time_column,
            target_column=request.target_column,
            frequency=request.frequency,
        )
    except ForecastException as fe:
        raise HTTPException(status_code=400, detail=fe.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": str(e)})


@router.post("/validate")
async def validate_experiment_request(request: ForecastExperimentRequest):
    """Validate experiment request configuration prior to launching training."""
    try:
        val = forecasting_service.analyze_suitability(
            dataset_id=request.dataset_id,
            version_id=request.dataset_version_id,
            time_column=request.time_column,
            target_column=request.target_column,
            frequency=request.frequency,
        )
        return {"valid": val.is_valid, "validation_report": val}
    except ForecastException as fe:
        raise HTTPException(status_code=400, detail=fe.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": str(e)})


@router.post("/experiments", response_model=ForecastExperiment)
async def create_experiment(request: ForecastExperimentRequest, sync: bool = False):
    """Launch a forecasting experiment job."""
    try:
        return forecasting_service.submit_experiment(request, run_sync=sync)
    except ForecastException as fe:
        raise HTTPException(status_code=400, detail=fe.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": str(e)})


@router.get("/experiments", response_model=List[ForecastExperiment])
async def list_experiments(
    dataset_id: Optional[str] = Query(None),
    dataset_version_id: Optional[str] = Query(None),
):
    """List historical forecasting experiments."""
    return forecasting_service.list_experiments(dataset_id, dataset_version_id)


@router.get("/experiments/{experiment_id}", response_model=ForecastExperiment)
async def get_experiment(experiment_id: str):
    """Poll experiment status."""
    exp = forecasting_service.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Forecasting experiment not found.")
    return exp


@router.post("/experiments/{experiment_id}/cancel")
async def cancel_experiment(experiment_id: str):
    """Cancel a running forecasting experiment."""
    cancelled = forecasting_service.cancel_experiment(experiment_id)
    if not cancelled:
        raise HTTPException(status_code=400, detail="Experiment could not be cancelled or does not exist.")
    return {"status": "CANCELLED", "experiment_id": experiment_id}


@router.get("/experiments/{experiment_id}/results", response_model=ForecastResult)
async def get_experiment_results(experiment_id: str):
    """Retrieve full structured results including Leaderboard, Findings, and Phase 9 ChartSpecs."""
    res = forecasting_service.get_experiment_results(experiment_id)
    if not res:
        exp = forecasting_service.get_experiment(experiment_id)
        if exp and exp.status.value == "FAILED":
            raise HTTPException(status_code=400, detail=f"Experiment failed: {exp.error_message}")
        raise HTTPException(status_code=404, detail="Results not ready or experiment not found.")
    return res


@router.get("/experiments/{experiment_id}/forecasts", response_model=List[ForecastPoint])
async def get_forecast_points(experiment_id: str):
    """Fetch future forecast observations from the best model."""
    res = forecasting_service.get_experiment_results(experiment_id)
    if not res:
        raise HTTPException(status_code=404, detail="Results not found.")
    best_run = next((m for m in res.models if m.model_id == res.best_model_id), res.models[0] if res.models else None)
    if not best_run:
        return []
    return best_run.future_forecasts


@router.get("/experiments/{experiment_id}/diagnostics", response_model=Optional[ResidualDiagnostics])
async def get_residual_diagnostics(experiment_id: str):
    """Fetch residual diagnostics from the best model."""
    res = forecasting_service.get_experiment_results(experiment_id)
    if not res:
        raise HTTPException(status_code=404, detail="Results not found.")
    best_run = next((m for m in res.models if m.model_id == res.best_model_id), res.models[0] if res.models else None)
    return best_run.residual_diagnostics if best_run else None


@router.post("/models/{run_id}/predict", response_model=FuturePredictResult)
async def predict_future(run_id: str, request: FuturePredictRequest):
    """Generate future predictions from a trained forecasting model."""
    try:
        request.run_id = run_id
        return forecasting_service.predict_future(request)
    except ForecastException as fe:
        raise HTTPException(status_code=400, detail=fe.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": str(e)})


@router.get("/history")
async def get_history():
    """Retrieve global forecasting experiment history."""
    return forecasting_service.get_history()
