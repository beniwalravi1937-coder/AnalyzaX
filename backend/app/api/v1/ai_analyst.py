"""
AI Analyst API Endpoints (Phase 13)
Mounted at /api/v1/ai-analyst
Coordinates chat conversations, planning, sessions, and tool catalog.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from backend.app.engines.ai_analyst.exceptions import AIAnalystException, AIErrorCode
from backend.app.engines.ai_analyst.models import (
    AnalystChatRequest,
    AnalystChatResponse,
    AnalystMessage,
    AnalystSession,
    AnalysisPlan,
    PlanRequest,
    ToolDefinition,
)
from backend.app.services.ai_analyst_service import ai_analyst_service

router = APIRouter(prefix="/ai-analyst", tags=["ai-analyst"])


class CreateSessionRequest(BaseModel):
    title: str = "New Analysis"
    dataset_id: Optional[str] = None
    dataset_version_id: Optional[str] = None


class ConfirmCleaningRequest(BaseModel):
    proposal_id: str


@router.post("/chat", response_model=AnalystChatResponse)
async def chat(request: AnalystChatRequest):
    """Submits a natural-language query to the AI Analyst."""
    try:
        return await ai_analyst_service.chat(request)
    except Exception as exc:
        from backend.app.core.errors import QuotaExceededException
        if isinstance(exc, QuotaExceededException):
            raise exc
        if isinstance(exc, AIAnalystException):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=exc.to_dict(),
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": AIErrorCode.AI_ANALYSIS_FAILED.value, "message": str(exc)},
        )


@router.post("/plan", response_model=AnalysisPlan)
async def create_plan(request: PlanRequest):
    """Generates an inspectable multi-step analytical plan without executing."""
    try:
        return ai_analyst_service.create_plan(
            dataset_id=request.dataset_id,
            question=request.question,
            version_id=request.dataset_version_id,
        )
    except AIAnalystException as aie:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=aie.to_dict(),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": AIErrorCode.AI_ANALYSIS_FAILED.value, "message": str(exc)},
        )


@router.get("/sessions", response_model=List[AnalystSession])
def list_sessions():
    """Lists all AI Analyst conversation sessions."""
    return ai_analyst_service.list_sessions()


@router.post("/sessions", response_model=AnalystSession)
def create_session(request: CreateSessionRequest):
    """Creates a new AI Analyst conversation session."""
    return ai_analyst_service.create_session(
        title=request.title,
        dataset_id=request.dataset_id,
        dataset_version_id=request.dataset_version_id,
    )


@router.get("/sessions/{session_id}", response_model=AnalystSession)
def get_session(session_id: str):
    """Retrieves a specific conversation session."""
    try:
        return ai_analyst_service.get_session(session_id)
    except AIAnalystException as aie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=aie.to_dict(),
        )


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """Deletes a conversation session."""
    deleted = ai_analyst_service.delete_session(session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": AIErrorCode.AI_SESSION_NOT_FOUND.value, "message": "Session not found."},
        )
    return {"status": "deleted", "session_id": session_id}


@router.get("/sessions/{session_id}/messages", response_model=List[AnalystMessage])
def get_session_messages(session_id: str):
    """Retrieves all messages for a session."""
    try:
        return ai_analyst_service.get_messages(session_id)
    except AIAnalystException as aie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=aie.to_dict(),
        )


@router.post("/sessions/{session_id}/confirm-cleaning")
def confirm_cleaning(session_id: str, request: ConfirmCleaningRequest):
    """Applies a user-approved cleaning proposal, generating a new immutable dataset version."""
    try:
        return ai_analyst_service.confirm_cleaning_proposal(session_id, request.proposal_id)
    except AIAnalystException as aie:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=aie.to_dict(),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": AIErrorCode.AI_ANALYSIS_FAILED.value, "message": str(exc)},
        )


@router.get("/tools", response_model=List[ToolDefinition])
def list_tools():
    """Lists registered analytical tools and permissions."""
    return ai_analyst_service.list_tools()
