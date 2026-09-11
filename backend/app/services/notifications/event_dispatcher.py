"""
Unified Application Event Dispatcher for Phase 19.
Coordinates activity recording, notification creation, and delivery channel dispatching.
Ensures failure isolation: notification or activity failures do not fail the underlying business operation.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from backend.app.engines.notifications.models import (
    ApplicationEvent,
    ApplicationEventType,
    Notification,
    NotificationChannel,
)
from backend.app.engines.notifications.repository import (
    NotificationRepository,
    notification_repo,
)
from backend.app.services.notifications.activity_service import (
    ActivityService,
    activity_service,
)
from backend.app.services.notifications.notification_service import (
    NotificationService,
    notification_service,
)

logger = logging.getLogger("analyzax")


class EventDispatcher:
    """Central event dispatcher for normalized application events."""

    def __init__(
        self,
        repository: Optional[NotificationRepository] = None,
        notifications: Optional[NotificationService] = None,
        activity: Optional[ActivityService] = None,
    ):
        self._repo = repository or notification_repo
        self._notification_svc = notifications or notification_service
        self._activity_svc = activity or activity_service

    def dispatch(self, event: ApplicationEvent) -> List[Notification]:
        """
        Dispatches an application event to activity feed and notification services.
        Guarantees isolation: failure in notification/activity processing is logged
        and does not propagate an unhandled exception to callers.
        """
        created_notifications: List[Notification] = []

        # 1. Persist the normalized event
        try:
            self._repo.save_event(event)
        except Exception as e:
            logger.error("Failed to persist application event %s: %s", event.event_id, e)

        # 2. Record user-facing activity (if applicable)
        try:
            self._activity_svc.record_activity(event)
        except Exception as e:
            logger.error("Failed to record activity for event %s: %s", event.event_id, e)

        # 3. Generate in-app notifications
        try:
            created_notifications = self._notification_svc.create_from_event(event)
        except Exception as e:
            logger.error("Failed to create notifications for event %s: %s", event.event_id, e)

        # 4. Delivery channel extension point (e.g., In-App, future Email/Push)
        for notif in created_notifications:
            self._dispatch_channel(notif)

        return created_notifications

    def _dispatch_channel(self, notification: Notification) -> None:
        """
        Extension point for multi-channel dispatch.
        In-App is already persisted in repository. Future channels (Email, Push) can plug in here.
        """
        # IN_APP: Already saved in database by NotificationService
        logger.debug(
            "Notification %s delivered via IN_APP to user %s",
            notification.notification_id,
            notification.recipient_user_id,
        )

    def create_and_dispatch(
        self,
        event_type: ApplicationEventType,
        actor_user_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        project_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> ApplicationEvent:
        """Convenience method to construct and dispatch an ApplicationEvent in one call."""
        event = ApplicationEvent(
            event_id=f"evt_{uuid.uuid4().hex[:16]}",
            event_type=event_type,
            actor_user_id=actor_user_id,
            workspace_id=workspace_id,
            project_id=project_id,
            resource_type=resource_type,
            resource_id=resource_id,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata or {},
            correlation_id=correlation_id,
        )
        self.dispatch(event)
        return event


# Singleton instance
event_dispatcher = EventDispatcher()
