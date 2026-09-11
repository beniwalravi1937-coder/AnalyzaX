"""
Enterprise Notification Application Service for Phase 19.
Handles event-driven notification generation, recipient resolution, preference filtering,
template rendering, deduplication, read tracking, and storm protection.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from backend.app.engines.auth.repository import AuthRepository, auth_repo
from backend.app.engines.notifications.models import (
    ApplicationEvent,
    ApplicationEventType,
    Notification,
    NotificationCategory,
    NotificationListResponse,
    NotificationPriority,
    NotificationStatus,
)
from backend.app.engines.notifications.repository import (
    NotificationRepository,
    notification_repo,
)
from backend.app.engines.notifications.templates import TemplateRegistry, template_registry
from backend.app.services.notifications.preference_service import PreferenceService, preference_service

logger = logging.getLogger("analyzax")


class NotificationService:
    """Manages the full lifecycle of actionable in-app notifications."""

    def __init__(
        self,
        repository: Optional[NotificationRepository] = None,
        preferences: Optional[PreferenceService] = None,
        templates: Optional[TemplateRegistry] = None,
        auth_repository: Optional[AuthRepository] = None,
    ):
        self._repo = repository or notification_repo
        self._pref_svc = preferences or preference_service
        self._templates = templates or template_registry
        self._auth_repo = auth_repository or auth_repo

    def create_from_event(self, event: ApplicationEvent) -> List[Notification]:
        """
        Creates actionable notifications from an application event.
        Enforces recipient resolution, preferences, deduplication, and template rendering.
        """
        template = self._templates.get_template(event.event_type.value)
        if not template:
            # No notification template for this event type (e.g., standard login/logout)
            return []

        recipients = self._resolve_recipients(event)
        if not recipients:
            return []

        # Build context for template substitution
        context = self._build_context(event)

        created_notifications: List[Notification] = []

        for recipient_id in recipients:
            # 1. Deduplication check
            if self._repo.is_duplicate_notification(event.event_id, recipient_id, event.event_type.value):
                logger.info(
                    f"Deduplicating notification event={event.event_id} recipient={recipient_id} type={event.event_type.value}"
                )
                continue

            # 2. Preference check (security events bypass)
            if not template.is_security:
                if not self._pref_svc.is_category_enabled(recipient_id, template.category):
                    logger.info(
                        f"Notification suppressed by user preference: user={recipient_id} category={template.category.value}"
                    )
                    continue

            # 3. Render title & message
            title = self._templates.render(template.title_template, context)
            message = self._templates.render(template.message_template, context)

            # 4. Generate safe deep link
            deep_link = self._templates.generate_deep_link(template.deep_link_strategy, context)

            # 5. Build entity
            notif = Notification(
                recipient_user_id=recipient_id,
                event_id=event.event_id,
                notification_type=event.event_type.value,
                category=template.category,
                priority=template.priority,
                title=title,
                message=message,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                workspace_id=event.workspace_id,
                project_id=event.project_id,
                deep_link=deep_link,
                status=NotificationStatus.UNREAD,
                metadata=event.metadata,
            )
            self._repo.save_notification(notif)
            created_notifications.append(notif)
            logger.info(
                f"Created notification {notif.notification_id} ({notif.category.value}) for recipient={recipient_id}"
            )

        return created_notifications

    def get_unread_count(self, user_id: str) -> int:
        """Returns the fast aggregation of unread notifications for a user."""
        return self._repo.count_unread(user_id)

    def list_notifications(
        self,
        user_id: str,
        status: Optional[NotificationStatus] = None,
        category: Optional[NotificationCategory] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> NotificationListResponse:
        """Lists paginated notifications belonging strictly to the requesting user."""
        eff_limit = limit or page_size
        eff_page = page
        if cursor:
            try:
                eff_page = int(cursor)
            except ValueError:
                eff_page = 1

        items, total = self._repo.list_notifications(
            user_id=user_id,
            status=status,
            category=category,
            search=search,
            page=eff_page,
            page_size=eff_limit,
        )
        unread_count = self._repo.count_unread(user_id)
        has_more = (eff_page * eff_limit) < total
        next_cursor = str(eff_page + 1) if has_more else None

        return NotificationListResponse(
            items=items,
            total=total,
            total_count=total,
            page=eff_page,
            page_size=eff_limit,
            unread_count=unread_count,
            has_more=has_more,
            next_cursor=next_cursor,
        )

    def get_notification(self, notification_id: str, user_id: str) -> Notification:
        """Retrieves a single notification, verifying user ownership to prevent IDOR."""
        notif = self._repo.get_notification(notification_id)
        if not notif or notif.recipient_user_id != user_id:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notif

    def mark_as_read(self, notification_id: str, user_id: str) -> Notification:
        """Marks a notification as READ."""
        notif = self.get_notification(notification_id, user_id)
        notif.status = NotificationStatus.READ
        notif.read_at = datetime.now(timezone.utc).isoformat()
        self._repo.save_notification(notif)
        return notif

    def mark_as_unread(self, notification_id: str, user_id: str) -> Notification:
        """Marks a notification as UNREAD."""
        notif = self.get_notification(notification_id, user_id)
        notif.status = NotificationStatus.UNREAD
        notif.read_at = None
        self._repo.save_notification(notif)
        return notif

    def mark_all_read(self, user_id: str) -> int:
        """Marks all unread notifications for the user as READ."""
        return self._repo.mark_all_as_read(user_id)

    def archive_notification(self, notification_id: str, user_id: str) -> Notification:
        """Archives a notification for clean inbox management."""
        notif = self.get_notification(notification_id, user_id)
        notif.status = NotificationStatus.ARCHIVED
        self._repo.save_notification(notif)
        return notif

    def cleanup(self) -> int:
        """Performs bounded cleanup and retention enforcement."""
        return self._repo.cleanup_expired_and_bounded()

    def cleanup_retention(self, user_id: Optional[str] = None) -> int:
        """Performs bounded retention cleanup."""
        return self.cleanup()

    # ─────────────────────────────────────────────────────────────
    # Internal Helpers
    # ─────────────────────────────────────────────────────────────

    def _resolve_recipients(self, event: ApplicationEvent) -> List[str]:
        """Resolves target recipient user IDs based on event relationship semantics."""
        recipients: List[str] = []

        # 1. Explicit list in metadata
        if "recipient_user_ids" in event.metadata and isinstance(event.metadata["recipient_user_ids"], list):
            recipients.extend(event.metadata["recipient_user_ids"])

        # 2. Targeted recipient
        if "recipient_user_id" in event.metadata and isinstance(event.metadata["recipient_user_id"], str):
            recipients.append(event.metadata["recipient_user_id"])

        if "recipient_id" in event.metadata and isinstance(event.metadata["recipient_id"], str):
            recipients.append(event.metadata["recipient_id"])

        if "target_user_id" in event.metadata and isinstance(event.metadata["target_user_id"], str):
            recipients.append(event.metadata["target_user_id"])

        # 3. Requesting actor for job/export/report outcomes
        if event.event_type in (
            ApplicationEventType.EXPORT_COMPLETED,
            ApplicationEventType.EXPORT_FAILED,
            ApplicationEventType.REPORT_CREATED,
            ApplicationEventType.REPORT_EXPORTED,
            ApplicationEventType.ANALYSIS_COMPLETED,
            ApplicationEventType.ANALYSIS_FAILED,
            ApplicationEventType.ML_EXPERIMENT_COMPLETED,
            ApplicationEventType.ML_EXPERIMENT_FAILED,
            ApplicationEventType.FORECAST_COMPLETED,
            ApplicationEventType.FORECAST_FAILED,
            ApplicationEventType.PASSWORD_CHANGED,
        ):
            if event.actor_user_id:
                recipients.append(event.actor_user_id)

        # 4. Filter duplicates and eliminate actor for third-party actions
        unique_recipients = list(dict.fromkeys(recipients))
        if event.event_type in (
            ApplicationEventType.RESOURCE_SHARED,
            ApplicationEventType.RESOURCE_SHARE_REVOKED,
            ApplicationEventType.MEMBER_ROLE_CHANGED,
            ApplicationEventType.MEMBER_REMOVED,
            ApplicationEventType.INVITATION_CREATED,
        ):
            # Don't notify the actor who took the action
            unique_recipients = [r for r in unique_recipients if r != event.actor_user_id]

        return unique_recipients

    def _build_context(self, event: ApplicationEvent) -> Dict[str, Any]:
        """Constructs sanitized placeholder variables for template substitution."""
        context: Dict[str, Any] = dict(event.metadata)

        # Actor name
        actor_name = "Someone"
        if event.actor_user_id:
            user = self._auth_repo.get_user(event.actor_user_id)
            if user:
                actor_name = user.display_name
        context["actor_name"] = actor_name

        # Resource name
        if "resource_name" not in context:
            context["resource_name"] = event.resource_id or "asset"

        context["resource_id"] = event.resource_id or ""
        context["resource_type"] = event.resource_type or ""
        context["project_id"] = event.project_id or ""
        context["workspace_id"] = event.workspace_id or ""

        if "error_summary" not in context and "error" in context:
            context["error_summary"] = str(context["error"])[:150]

        return context


# Singleton instance
notification_service = NotificationService()
