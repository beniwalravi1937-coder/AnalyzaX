"""
REST API Router for Activity Feeds (Phase 19).
Provides user-facing project and workspace activity timelines.
Enforces strict workspace membership and project access boundaries.
Strictly decoupled from security audit logs.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.api.deps import get_current_user
from backend.app.engines.auth.models import User
from backend.app.engines.notifications.models import (
    ActivityFeedItem,
    ActivityListResponse,
    ApplicationEventType,
)
from backend.app.services.notifications.activity_service import (
    ActivityService,
    activity_service,
)

router = APIRouter(tags=["Activity Center"])


@router.get("/projects/{project_id}/activity", response_model=ActivityListResponse)
def get_project_activity(
    project_id: str,
    event_type: Optional[ApplicationEventType] = Query(None, description="Filter by event type"),
    actor_user_id: Optional[str] = Query(None, description="Filter by actor user ID"),
    limit: int = Query(50, ge=1, le=100, description="Items to return"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    current_user: User = Depends(get_current_user),
) -> ActivityListResponse:
    """
    Returns user-facing collaborative activity feed for a project.
    Requires that the authenticated user has access to the project.
    """
    return activity_service.get_project_activity(
        project_id=project_id,
        requesting_user_id=current_user.user_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        limit=limit,
        cursor=cursor,
    )


@router.get("/workspaces/{workspace_id}/activity", response_model=ActivityListResponse)
def get_workspace_activity(
    workspace_id: str,
    event_type: Optional[ApplicationEventType] = Query(None, description="Filter by event type"),
    actor_user_id: Optional[str] = Query(None, description="Filter by actor user ID"),
    limit: int = Query(50, ge=1, le=100, description="Items to return"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    current_user: User = Depends(get_current_user),
) -> ActivityListResponse:
    """
    Returns high-level user-facing collaborative activity feed for a workspace.
    Requires active workspace membership. Excludes sensitive security audit details.
    """
    return activity_service.get_workspace_activity(
        workspace_id=workspace_id,
        requesting_user_id=current_user.user_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        limit=limit,
        cursor=cursor,
    )
