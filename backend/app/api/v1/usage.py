"""
Usage Metering & Quotas REST API (Phase 20)
Mounted at /api/v1/usage
Provides workspace usage summaries, health indicators, event audit history, and reconciliation.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status

from backend.app.api.deps import get_current_user_optional
from backend.app.engines.auth.models import User
from backend.app.engines.usage.models import UsageEvent, UsageSummaryDTO
from backend.app.services.usage import plan_service, usage_service
from backend.app.services.workspace.workspace_service import workspace_service

router = APIRouter(prefix="/usage", tags=["usage"])


def _resolve_target_workspace(
    workspace_id: Optional[str] = None,
    x_workspace_id: Optional[str] = None,
) -> str:
    ws_id = workspace_id or x_workspace_id
    if not ws_id:
        def_ws = workspace_service.get_or_create_default_workspace()
        ws_id = def_ws.workspace_id
    return ws_id


@router.get(
    "/summary",
    response_model=UsageSummaryDTO,
    summary="Get Workspace Usage Summary",
    description="Returns current plan, quota health indicators, usage breakdown, and point-in-time resource consumption.",
)
def get_usage_summary(
    workspace_id: Optional[str] = Query(None, description="Workspace ID"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: Optional[User] = Depends(get_current_user_optional),
) -> UsageSummaryDTO:
    target_ws = _resolve_target_workspace(workspace_id, x_workspace_id)
    return usage_service.get_usage_summary(target_ws)


@router.get(
    "/history",
    summary="Get Usage Events Audit History",
    description="Returns paginated, immutable usage events for the specified workspace and metric filter.",
)
def get_usage_history(
    workspace_id: Optional[str] = Query(None, description="Workspace ID"),
    metric_key: Optional[str] = Query(None, description="Filter by metric key"),
    period_key: Optional[str] = Query(None, description="Filter by YYYY-MM period"),
    limit: int = Query(50, ge=1, le=200),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: Optional[User] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    target_ws = _resolve_target_workspace(workspace_id, x_workspace_id)
    history_resp = usage_service.list_history(
        workspace_id=target_ws,
        metric_key=metric_key,
        period_key=period_key,
        limit=limit,
        cursor=cursor,
    )
    return {
        "workspace_id": target_ws,
        "total": history_resp.total,
        "next_cursor": history_resp.next_cursor,
        "has_more": history_resp.has_more,
        "events": [item.model_dump() for item in history_resp.items],
    }


@router.get(
    "/reconcile",
    summary="Reconcile Usage Aggregation & Storage",
    description="Admin diagnostic endpoint to audit aggregated usage vs append-only source events.",
)
def reconcile_usage(
    workspace_id: Optional[str] = Query(None, description="Workspace ID"),
    period_key: Optional[str] = Query(None, description="Filter by YYYY-MM period"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: Optional[User] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    target_ws = _resolve_target_workspace(workspace_id, x_workspace_id)
    report = usage_service.reconcile_usage(workspace_id=target_ws, period_key=period_key)
    return report.model_dump()
