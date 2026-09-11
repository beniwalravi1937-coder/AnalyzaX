"""
REST API Router for Enterprise In-App Notifications (Phase 19).
Thin orchestration layer delegating strictly to NotificationService.
All operations are strictly scoped to the authenticated user derived from session auth.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.api.deps import get_current_user
from backend.app.engines.auth.models import User
from backend.app.engines.notifications.models import (
    Notification,
    NotificationCategory,
    NotificationListResponse,
    NotificationStatus,
)
from backend.app.services.notifications.notification_service import (
    NotificationService,
    notification_service,
)

router = APIRouter(prefix="/notifications", tags=["Enterprise Notifications"])


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    category: Optional[NotificationCategory] = Query(None, description="Filter by category"),
    status: Optional[NotificationStatus] = Query(None, description="Filter by status (UNREAD, READ, etc.)"),
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    search: Optional[str] = Query(None, max_length=100, description="Search in title/message/resource"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    current_user: User = Depends(get_current_user),
) -> NotificationListResponse:
    """
    Lists notifications for the currently authenticated user with filtering,
    pagination, and search. Never leaks other users' records.
    """
    effective_status = status
    if unread_only and not status:
        effective_status = NotificationStatus.UNREAD

    return notification_service.list_notifications(
        user_id=current_user.user_id,
        category=category,
        status=effective_status,
        search=search,
        limit=limit,
        cursor=cursor,
    )


@router.get("/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
) -> Dict[str, int]:
    """
    Returns the real unread count for the current user.
    Used by global navigation badges.
    """
    count = notification_service.get_unread_count(current_user.user_id)
    return {"unread_count": count}


@router.get("/{notification_id}", response_model=Notification)
def get_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
) -> Notification:
    """Retrieves a specific notification owned by the current user."""
    return notification_service.get_notification(notification_id, current_user.user_id)


@router.post("/{notification_id}/read", response_model=Notification)
def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
) -> Notification:
    """Marks a notification as read and updates read_at timestamp."""
    return notification_service.mark_as_read(notification_id, current_user.user_id)


@router.post("/{notification_id}/unread", response_model=Notification)
def mark_notification_as_unread(
    notification_id: str,
    current_user: User = Depends(get_current_user),
) -> Notification:
    """Marks a notification as unread."""
    return notification_service.mark_as_unread(notification_id, current_user.user_id)


@router.post("/read-all")
def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Marks all unread notifications as read for the current user."""
    count = notification_service.mark_all_read(current_user.user_id)
    return {
        "message": f"Marked {count} notification(s) as read",
        "count": count,
    }


@router.post("/{notification_id}/archive", response_model=Notification)
def archive_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
) -> Notification:
    """Archives a notification for the current user."""
    return notification_service.archive_notification(notification_id, current_user.user_id)


@router.post("/cleanup")
def run_retention_cleanup(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Triggers bounded retention cleanup for the user's notifications.
    Adheres to NOTIFICATION_RETENTION_DAYS and NOTIFICATION_MAX_PER_USER limits.
    """
    cleaned = notification_service.cleanup_retention(current_user.user_id)
    return {
        "message": f"Cleaned up {cleaned} expired/surplus notification(s)",
        "cleaned_count": cleaned,
    }
