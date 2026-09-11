"""
AnalyzaX — Phase 25: Governed Metrics API Endpoints.
Mounted at /api/v1/metrics
Provides CRUD, AST formula validation, deterministic previews, and version history.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.app.engines.semantic.models import (
    AggregationType,
    MetricCalculationResult,
    MetricDefinition,
    MetricStatus,
    MetricVersionRecord,
)
from backend.app.services.semantic_service import semantic_service

router = APIRouter(prefix="/metrics", tags=["metrics"])


class CreateMetricRequest(BaseModel):
    workspace_id: str
    name: str
    expression: str
    owner_id: str = "user_default"
    project_id: Optional[str] = None
    description: str = ""
    aggregation: AggregationType = AggregationType.SUM
    unit: Optional[str] = None
    dimensions: List[str] = Field(default_factory=list)
    synonyms: List[str] = Field(default_factory=list)


class UpdateMetricRequest(BaseModel):
    user_id: str = "user_default"
    name: Optional[str] = None
    description: Optional[str] = None
    expression: Optional[str] = None
    status: Optional[MetricStatus] = None
    unit: Optional[str] = None
    synonyms: Optional[List[str]] = None
    change_summary: str = "Updated metric"


class ValidateFormulaRequest(BaseModel):
    expression: str
    available_columns: Optional[List[str]] = None


class PreviewMetricRequest(BaseModel):
    dataset_path: str
    filters: Optional[Dict[str, Any]] = None


@router.post("", response_model=MetricDefinition, status_code=status.HTTP_201_CREATED)
def create_metric(request: CreateMetricRequest):
    """Creates and persists a new governed metric."""
    try:
        return semantic_service.create_metric(
            workspace_id=request.workspace_id,
            name=request.name,
            expression=request.expression,
            owner_id=request.owner_id,
            project_id=request.project_id,
            description=request.description,
            aggregation=request.aggregation,
            unit=request.unit,
            dimensions=request.dimensions,
            synonyms=request.synonyms,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.get("", response_model=List[MetricDefinition])
def list_metrics(
    workspace_id: str = Query(...),
    project_id: Optional[str] = Query(None),
    status: Optional[MetricStatus] = Query(None),
):
    """Lists governed metrics for a workspace/project."""
    return semantic_service.list_metrics(
        workspace_id=workspace_id,
        project_id=project_id,
        status=status,
    )


@router.get("/{metric_id}", response_model=MetricDefinition)
def get_metric(metric_id: str):
    """Retrieves a governed metric by ID."""
    metric = semantic_service.get_metric(metric_id)
    if not metric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Metric '{metric_id}' not found.")
    return metric


@router.put("/{metric_id}", response_model=MetricDefinition)
def update_metric(metric_id: str, request: UpdateMetricRequest):
    """Updates metric definition and logs an auditable version record."""
    try:
        return semantic_service.update_metric(
            metric_id=metric_id,
            user_id=request.user_id,
            name=request.name,
            description=request.description,
            expression=request.expression,
            status=request.status,
            unit=request.unit,
            synonyms=request.synonyms,
            change_summary=request.change_summary,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.delete("/{metric_id}")
def delete_metric(metric_id: str):
    """Deletes a metric definition."""
    deleted = semantic_service.delete_metric(metric_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Metric '{metric_id}' not found.")
    return {"status": "deleted", "metric_id": metric_id}


@router.post("/validate")
def validate_formula(request: ValidateFormulaRequest):
    """Performs AST validation on a metric expression."""
    return semantic_service.validate_formula(
        expression=request.expression,
        available_columns=request.available_columns,
    )


@router.post("/{metric_id}/preview", response_model=MetricCalculationResult)
def preview_metric(metric_id: str, request: PreviewMetricRequest):
    """Executes deterministic calculation of a metric using DuckDB."""
    try:
        return semantic_service.preview_metric(
            metric_id=metric_id,
            dataset_path=request.dataset_path,
            filters=request.filters,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{metric_id}/versions", response_model=List[MetricVersionRecord])
def get_metric_versions(metric_id: str):
    """Retrieves historical versions for a metric definition."""
    return semantic_service.get_version_history(metric_id)
