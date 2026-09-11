"""
In-App Notification Service for Phase 18.
Provides notification dispatching, query listing, and read tracking for authenticated users.
"""

from typing import List, Optional

from fastapi import HTTPException

from backend.app.engines.collaboration.models import (
    Notification,
    NotificationType,
    ResourceType,
)
from backend.app.engines.collaboration.repository import CollaborationRepository, collaboration_repo


class NotificationService:
    """Manages user notifications for sharing, invitations, and role modifications."""

    def __init__(self, repository: Optional[CollaborationRepository] = None):
        self._repo = repository or collaboration_repo

    def list_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[Notification]:
        return self._repo.list_notifications(user_id, unread_only=unread_only, limit=limit)

    def mark_read(self, notification_id: str, user_id: str) -> bool:
        success = self._repo.mark_notification_read(notification_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        return True

    def mark_all_read(self, user_id: str) -> int:
        return self._repo.mark_all_notifications_read(user_id)

    def create_notification(
        self,
        recipient_user_id: str,
        notif_type: NotificationType,
        title: str,
        message: str,
        related_resource_type: Optional[ResourceType] = None,
        related_resource_id: Optional[str] = None,
        action_url: Optional[str] = None,
    ) -> Notification:
        notif = Notification(
            recipient_user_id=recipient_user_id,
            type=notif_type,
            title=title,
            message=message,
            related_resource_type=related_resource_type,
            related_resource_id=related_resource_id,
            action_url=action_url,
        )
        self._repo.save_notification(notif)
        return notif


# Global singleton instance
notification_service = NotificationService()
