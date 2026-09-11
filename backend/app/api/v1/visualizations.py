"""
Phase 9: Visualization Engine REST API Endpoints.
Provides deterministic chart recommendations, spec validation, data preview,
and version-bound saved visualization management.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from backend.app.engines.visualization.models import (
    ChartSpec,
    SavedVisualization,
    VisualizationIntent,
    VisualizationRecommendation,
    VisualizationValidationResult,
)
from backend.app.engines.visualization.registry import (
    CHART_REGISTRY,
    ChartTypeDefinition,
    list_charts_by_tier,
)
from backend.app.services.visualization_service import visualization_service

router = APIRouter(prefix="/visualizations", tags=["Visualizations"])


@router.get(
    "/registry",
    response_model=List[ChartTypeDefinition],
    summary="Get centralized chart types and capability registry (VIZ-T08, VIZ-T09)",
)
async def get_chart_registry(tier: Optional[int] = Query(None, description="Optional tier filter (1, 2, or 3)")):
    """
    Returns the single source of truth for all chart types, tiers, capability flags,
    required encodings, and support status.
    """
    definitions = list(CHART_REGISTRY.values())
    if tier is not None:
        definitions = [d for d in definitions if d.tier.value == tier]
    return definitions


class RecommendRequest(BaseModel):
    dataset_id: str
    version_id: Optional[str] = None
    selected_fields: Optional[List[str]] = None
    intent: Optional[VisualizationIntent] = None


class SaveVisualizationRequest(BaseModel):
    name: str
    description: Optional[str] = None
    spec: ChartSpec
    source_reference: Optional[str] = None


class RecommendFromSqlRequest(BaseModel):
    columns: List[Dict[str, Any]]
    rows: List[Dict[str, Any]]
    query_text: Optional[str] = None


@router.post(
    "/recommend",
    response_model=List[VisualizationRecommendation],
    summary="Generate deterministic chart recommendations for a dataset version",
)
async def recommend_visualizations(req: RecommendRequest):
    try:
        return visualization_service.recommend_visualizations(
            dataset_id=req.dataset_id,
            version_id=req.version_id,
            selected_fields=req.selected_fields,
            intent=req.intent,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate recommendations: {str(e)}",
        )


@router.post(
    "/validate",
    response_model=VisualizationValidationResult,
    summary="Validate a ChartSpec against dataset version schema",
)
async def validate_spec(spec: ChartSpec):
    try:
        return visualization_service.validate_chart_spec(spec)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}",
        )


@router.post(
    "/preview",
    response_model=ChartSpec,
    summary="Prepare data and return hydrated ChartSpec",
)
async def preview_chart(spec: ChartSpec):
    try:
        return visualization_service.preview_chart(spec)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to prepare chart preview: {str(e)}",
        )


@router.post(
    "",
    response_model=SavedVisualization,
    status_code=status.HTTP_201_CREATED,
    summary="Save a visualization with dataset version provenance",
)
async def save_visualization(req: SaveVisualizationRequest):
    try:
        return visualization_service.save_visualization(
            name=req.name,
            spec=req.spec,
            description=req.description,
            source_reference=req.source_reference,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to save visualization: {str(e)}",
        )


@router.get(
    "",
    response_model=List[SavedVisualization],
    summary="List saved visualizations",
)
async def list_saved_visualizations(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    version_id: Optional[str] = Query(None, description="Filter by version ID"),
):
    try:
        return visualization_service.list_saved_visualizations(
            dataset_id=dataset_id,
            version_id=version_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve saved visualizations: {str(e)}",
        )


@router.get(
    "/{visualization_id}",
    response_model=SavedVisualization,
    summary="Get saved visualization by ID",
)
async def get_saved_visualization(visualization_id: str):
    viz = visualization_service.get_saved_visualization(visualization_id)
    if not viz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visualization '{visualization_id}' not found.",
        )
    return viz


@router.delete(
    "/{visualization_id}",
    summary="Delete a saved visualization",
)
async def delete_saved_visualization(visualization_id: str):
    deleted = visualization_service.delete_saved_visualization(visualization_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visualization '{visualization_id}' not found.",
        )
    return {"deleted": True, "id": visualization_id}


@router.get(
    "/{visualization_id}/compatibility",
    response_model=VisualizationValidationResult,
    summary="Check schema compatibility against another dataset version",
)
async def check_version_compatibility(
    visualization_id: str,
    target_version_id: str = Query(..., description="Target version ID to evaluate compatibility against"),
):
    try:
        return visualization_service.check_version_compatibility(
            visualization_id=visualization_id,
            target_version_id=target_version_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to check compatibility: {str(e)}",
        )


@router.get(
    "/{visualization_id}/data",
    summary="Retrieve underlying chart records and sampling metadata",
)
async def get_visualization_data(visualization_id: str):
    viz = visualization_service.get_saved_visualization(visualization_id)
    if not viz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visualization '{visualization_id}' not found.",
        )
    return {
        "data": viz.chart_spec.data,
        "sampling": viz.chart_spec.sampling,
        "row_count": len(viz.chart_spec.data),
    }


@router.post(
    "/recommend-from-sql",
    response_model=List[VisualizationRecommendation],
    summary="Generate deterministic recommendations from SQL query results",
)
async def recommend_from_sql(req: RecommendFromSqlRequest):
    try:
        return visualization_service.recommend_from_sql(
            columns=req.columns,
            rows=req.rows,
            query_text=req.query_text,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate SQL recommendations: {str(e)}",
        )
