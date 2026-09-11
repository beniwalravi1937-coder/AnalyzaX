"""
Notification Preference Application Service for Phase 19.
Manages user notification preferences with security-critical non-suppressibility enforcement.
"""

from datetime import datetime, timezone
import logging
from typing import List, Optional

from fastapi import HTTPException

from backend.app.engines.notifications.models import (
    NotificationCategory,
    NotificationChannel,
    NotificationPreference,
)
from backend.app.engines.notifications.repository import (
    NotificationRepository,
    notification_repo,
)

logger = logging.getLogger("analyzax")


class PreferenceService:
    """Manages user-level notification preferences."""

    def __init__(self, repository: Optional[NotificationRepository] = None):
        self._repo = repository or notification_repo

    def get_user_preferences(self, user_id: str) -> List[NotificationPreference]:
        """
        Retrieves all category preferences for a user.
        Injects default ENABLED=True for any categories not explicitly customized.
        """
        saved = {p.category: p for p in self._repo.list_preferences(user_id)}
        results: List[NotificationPreference] = []

        for cat in NotificationCategory:
            if cat in saved:
                results.append(saved[cat])
            else:
                # Default is enabled
                results.append(
                    NotificationPreference(
                        user_id=user_id,
                        category=cat,
                        channel=NotificationChannel.IN_APP,
                        enabled=True,
                    )
                )
        return results

    def is_category_enabled(self, user_id: str, category: NotificationCategory) -> bool:
        """Checks if a notification category is active for the user."""
        # Security notifications can NEVER be suppressed
        if category == NotificationCategory.SECURITY:
            return True

        pref = self._repo.get_preference(user_id, category)
        if pref is not None:
            return pref.enabled
        # Default is enabled
        return True

    def update_preference(
        self,
        user_id: str,
        category: NotificationCategory,
        enabled: bool,
        channel: NotificationChannel = NotificationChannel.IN_APP,
    ) -> NotificationPreference:
        """
        Updates a user preference.
        Enforces security rule: SECURITY notifications cannot be disabled.
        """
        if category == NotificationCategory.SECURITY and not enabled:
            raise HTTPException(
                status_code=400,
                detail="Security-critical notifications cannot be disabled and are mandatory for account safety.",
            )

        pref = self._repo.get_preference(user_id, category)
        if pref:
            pref.enabled = enabled
            pref.channel = channel
            pref.updated_at = datetime.now(timezone.utc).isoformat()
        else:
            pref = NotificationPreference(
                user_id=user_id,
                category=category,
                channel=channel,
                enabled=enabled,
            )

        self._repo.save_preference(pref)
        logger.info(f"Updated notification preference for user={user_id} category={category.value} enabled={enabled}")
        return pref


# Singleton instance
preference_service = PreferenceService()
