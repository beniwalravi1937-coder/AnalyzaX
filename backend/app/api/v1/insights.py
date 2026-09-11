"""
AnalyzaX — Phase 25: Proactive Insights API Endpoints.
Mounted at /api/v1/ai/insights
Provides discovery, ranking, dismissal, and retrieval of multi-engine insights.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.app.engines.insights.models import (
    Insight,
    InsightSeverity,
    InsightStatus,
    InsightType,
)
from backend.app.services.insight_service import insight_service

router = APIRouter(prefix="/ai/insights", tags=["insights"])


class GenerateInsightsRequest(BaseModel):
    workspace_id: str
    dataset_id: str
    version_id: str
    project_id: Optional[str] = None
    profile_data: Optional[Dict[str, Any]] = None
    quality_data: Optional[Dict[str, Any]] = None
    eda_data: Optional[Dict[str, Any]] = None
    stats_data: Optional[Dict[str, Any]] = None


@router.get("", response_model=List[Insight])
def list_insights(
    workspace_id: str = Query(...),
    project_id: Optional[str] = Query(None),
    dataset_id: Optional[str] = Query(None),
    severity: Optional[InsightSeverity] = Query(None),
    status: Optional[InsightStatus] = Query(None),
    insight_type: Optional[InsightType] = Query(None),
):
    """Lists proactive insights sorted by analytical priority score."""
    return insight_service.list_insights(
        workspace_id=workspace_id,
        project_id=project_id,
        dataset_id=dataset_id,
        severity=severity,
        status=status,
        insight_type=insight_type,
    )


@router.get("/{insight_id}", response_model=Insight)
def get_insight(insight_id: str):
    """Retrieves single insight details including evidence graph."""
    ins = insight_service.get_insight(insight_id)
    if not ins:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Insight '{insight_id}' not found.")
    return ins


@router.post("/{insight_id}/dismiss")
def dismiss_insight(insight_id: str):
    """Marks an insight as dismissed."""
    success = insight_service.dismiss_insight(insight_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Insight '{insight_id}' not found.")
    return {"status": "dismissed", "insight_id": insight_id}


@router.post("/generate", response_model=List[Insight])
def generate_insights(request: GenerateInsightsRequest):
    """Executes deterministic signal detection across analytical outputs for a dataset version."""
    return insight_service.generate_insights_for_dataset(
        workspace_id=request.workspace_id,
        dataset_id=request.dataset_id,
        version_id=request.version_id,
        project_id=request.project_id,
        profile_data=request.profile_data,
        quality_data=request.quality_data,
        eda_data=request.eda_data,
        stats_data=request.stats_data,
    )
