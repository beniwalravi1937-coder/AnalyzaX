"""
REST API Router for Notification Preferences (Phase 19).
Allows users to configure notification categories and channels.
Strictly prohibits disabling security-critical alerts.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.deps import get_current_user
from backend.app.engines.auth.models import User
from backend.app.engines.notifications.models import (
    NotificationCategory,
    NotificationChannel,
    NotificationPreference,
    UpdatePreferenceRequest,
)
from backend.app.services.notifications.preference_service import (
    PreferenceService,
    preference_service,
)

router = APIRouter(prefix="/notification-preferences", tags=["Notification Preferences"])


@router.get("", response_model=List[NotificationPreference])
def get_user_preferences(
    current_user: User = Depends(get_current_user),
) -> List[NotificationPreference]:
    """Retrieves all notification preferences for the authenticated user."""
    return preference_service.get_user_preferences(current_user.user_id)


@router.patch("", response_model=NotificationPreference)
def update_user_preference(
    req: UpdatePreferenceRequest,
    current_user: User = Depends(get_current_user),
) -> NotificationPreference:
    """
    Updates a notification preference for the authenticated user.
    Security notifications cannot be disabled.
    """
    return preference_service.update_preference(
        user_id=current_user.user_id,
        category=req.category,
        channel=req.channel,
        enabled=req.enabled,
    )
