"""
AnalyzaX — Phase 10: Statistical Intelligence API Router
Exposes endpoints for running statistical analyses, deterministic method recommendations,
validations, method catalog, history, and visualization retrieval.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

from backend.app.core.logging import logger
from backend.app.engines.statistics.models import (
    MethodCatalogItem,
    MethodRecommendation,
    MethodRecommendationRequest,
    StatisticalAnalysisRequest,
    StatisticalResult,
    ValidationResponse,
)
from backend.app.services.statistics_service import statistics_service

router = APIRouter(prefix="/statistics", tags=["Statistical Intelligence Engine"])


@router.get(
    "/methods",
    response_model=List[MethodCatalogItem],
    summary="List supported statistical methods catalog",
)
async def list_statistical_methods():
    """Returns the catalog of all supported parametric and non-parametric statistical methods."""
    return statistics_service.get_methods_catalog()


@router.post(
    "/recommend",
    response_model=MethodRecommendation,
    summary="Recommend optimal statistical test",
)
async def recommend_method(req: MethodRecommendationRequest):
    """
    Deterministically evaluates variable data types, group counts, sample size,
    and distribution indicators to recommend the optimal statistical method and alternatives.
    """
    try:
        return statistics_service.recommend_method(req)
    except Exception as e:
        logger.error(f"Failed to recommend statistical method: {e}")
        raise HTTPException(status_code=400, detail=f"Recommendation failed: {str(e)}")


@router.post(
    "/validate",
    response_model=ValidationResponse,
    summary="Validate statistical analysis inputs",
)
async def validate_analysis_request(req: StatisticalAnalysisRequest):
    """Validates analysis inputs against dataset version schema and reports missingness impact."""
    return statistics_service.validate_request(req)


@router.post(
    "/analyze",
    response_model=StatisticalResult,
    summary="Execute deterministic statistical analysis",
)
async def run_analysis(req: StatisticalAnalysisRequest):
    """
    Executes a statistical computation explicitly bound to a dataset_id and dataset_version_id.
    Computes deterministic statistics, effect sizes, confidence intervals, assumptions, findings,
    and ChartSpecs using SciPy, statsmodels, NumPy, and Polars.
    """
    try:
        return statistics_service.execute_analysis(req)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error executing statistical analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Statistical analysis failed: {str(e)}")


@router.get(
    "/history",
    response_model=List[StatisticalResult],
    summary="List historical statistical analyses",
)
async def list_history(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    dataset_version_id: Optional[str] = Query(None, description="Filter by version ID"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """Returns historical statistical analysis results, optionally filtered and paginated."""
    items = statistics_service.list_history(dataset_id, dataset_version_id)
    return items[offset : offset + limit]


@router.post(
    "/{analysis_id}/cancel",
    summary="Cancel a statistical analysis",
)
async def cancel_analysis(analysis_id: str):
    """
    Cancels an in-progress or queued statistical analysis.
    If the analysis is already completed, returns the completed state without invalidation.
    """
    result = statistics_service.get_analysis(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Statistical analysis '{analysis_id}' not found.")
    if result.status in ["QUEUED", "RUNNING"]:
        result.status = "CANCELLED"
        statistics_service._save_history_record(result)
        return {"status": "CANCELLED", "analysis_id": analysis_id}
    return {"status": result.status, "message": f"Analysis already in terminal state: {result.status}", "analysis_id": analysis_id}


@router.get(
    "/{analysis_id}",
    response_model=StatisticalResult,
    summary="Get saved statistical analysis result",
)
async def get_analysis(analysis_id: str):
    """Retrieves a saved statistical result by its ID."""
    result = statistics_service.get_analysis(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Statistical analysis '{analysis_id}' not found.")
    return result


@router.delete(
    "/{analysis_id}",
    summary="Delete a saved statistical analysis",
)
async def delete_analysis(analysis_id: str):
    """Deletes a saved statistical analysis result from persistent history."""
    deleted = statistics_service.delete_analysis(analysis_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Statistical analysis '{analysis_id}' not found.")
    return {"status": "deleted", "analysis_id": analysis_id}


@router.get(
    "/{analysis_id}/visualizations",
    response_model=List[Dict[str, Any]],
    summary="Get visualization ChartSpecs for an analysis",
)
async def get_analysis_visualizations(analysis_id: str):
    """Returns the Phase 9 ChartSpec objects generated by this statistical analysis."""
    result = statistics_service.get_analysis(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Statistical analysis '{analysis_id}' not found.")
    return result.chart_specs
