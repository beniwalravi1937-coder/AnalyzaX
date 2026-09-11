"""
AnalyzaX — Phase 25: AI Copilot API Endpoints.
Mounted at /api/v1/ai/copilot
Provides chat orchestration, agentic workflow controls, and dashboard plan execution.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.app.engines.ai_copilot.models import (
    AIWorkflow,
    CopilotContext,
    CopilotResponse,
    DashboardPlan,
)
from backend.app.services.copilot_service import copilot_service

router = APIRouter(prefix="/ai/copilot", tags=["ai-copilot"])


class CopilotChatRequest(BaseModel):
    message: str
    context: CopilotContext
    session_id: Optional[str] = None
    tone: str = "ANALYST"
    user_workspace_id: Optional[str] = None


class ApproveWorkflowStepRequest(BaseModel):
    step_id: str
    user_id: str = "user_default"


class ExecuteDashboardPlanRequest(BaseModel):
    plan: DashboardPlan
    workspace_id: str
    user_id: str = "user_default"
    project_id: Optional[str] = None


@router.post("/chat", response_model=CopilotResponse)
async def chat(request: CopilotChatRequest):
    """Processes user query with AI Copilot, enforcing tenant isolation, safety, and quotas."""
    try:
        return await copilot_service.chat(
            message=request.message,
            context=request.context,
            session_id=request.session_id,
            tone=request.tone,
            user_workspace_id=request.user_workspace_id,
        )
    except Exception as exc:
        from backend.app.core.errors import QuotaExceededException
        if isinstance(exc, QuotaExceededException):
            raise exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/workflows/{workflow_id}", response_model=AIWorkflow)
def get_workflow(workflow_id: str):
    """Retrieves an active or paused workflow by ID."""
    wf = copilot_service.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow '{workflow_id}' not found.")
    return wf


@router.post("/workflows/{workflow_id}/approve", response_model=AIWorkflow)
async def approve_workflow_step(workflow_id: str, request: ApproveWorkflowStepRequest):
    """Explicitly approves a paused mutating step in a workflow and resumes execution."""
    try:
        return await copilot_service.approve_workflow_step(
            workflow_id=workflow_id,
            step_id=request.step_id,
            user_id=request.user_id,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/workflows/{workflow_id}/cancel", response_model=AIWorkflow)
def cancel_workflow(workflow_id: str):
    """Cancels a workflow."""
    try:
        return copilot_service.cancel_workflow(workflow_id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))


@router.post("/dashboards/execute")
def execute_dashboard_plan(request: ExecuteDashboardPlanRequest):
    """Materializes an approved DashboardPlan into a live dashboard."""
    try:
        return copilot_service.execute_dashboard_plan(
            plan=request.plan,
            workspace_id=request.workspace_id,
            user_id=request.user_id,
            project_id=request.project_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
