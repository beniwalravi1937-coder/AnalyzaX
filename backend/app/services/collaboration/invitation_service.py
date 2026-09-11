"""
Application Service for Workspace Invitations (Phase 18).
Coordinates invitation generation with cryptographic single-use tokens,
SHA-256 hash storage, verification, acceptance, resend, and revocation.
"""

from datetime import datetime, timedelta, timezone
import secrets
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException

from backend.app.core.logging import logger
from backend.app.engines.auth.crypto import hash_session_token
from backend.app.engines.auth.models import (
    MembershipStatus,
    RoleName,
    SecurityAuditEvent,
    SecurityEventType,
    User,
    WorkspaceMember,
    normalize_email,
    validate_email_format,
)
from backend.app.engines.auth.permissions import Permission
from backend.app.engines.auth.repository import AuthRepository, auth_repo
from backend.app.engines.collaboration.invitation_delivery import (
    InvitationDeliveryService,
    NotificationProvider,
    invitation_delivery_service,
)
from backend.app.engines.collaboration.models import (
    CollaborationActivityEvent,
    CollaborationEventType,
    CreateInvitationRequest,
    InvitationResponse,
    InvitationStatus,
    InvitationVerifyResponse,
    Notification,
    NotificationType,
    WorkspaceInvitation,
)
from backend.app.engines.collaboration.repository import CollaborationRepository, collaboration_repo
from backend.app.engines.workspace.repository import WorkspaceRepository, workspace_repo
from backend.app.engines.notifications.models import ApplicationEventType
from backend.app.services.notifications.event_dispatcher import event_dispatcher
from backend.app.services.auth.authorization_service import AuthorizationService


class InvitationService:
    """Coordinates workspace invitations, acceptance, and security auditing."""

    def __init__(
        self,
        collab_repository: Optional[CollaborationRepository] = None,
        auth_repository: Optional[AuthRepository] = None,
        workspace_repository: Optional[WorkspaceRepository] = None,
        delivery_service: Optional[NotificationProvider] = None,
    ):
        self._collab_repo = collab_repository or collaboration_repo
        self._auth_repo = auth_repository or auth_repo
        self._ws_repo = workspace_repository or workspace_repo
        self._delivery = delivery_service or invitation_delivery_service
        self._authz = AuthorizationService(self._auth_repo, self._ws_repo)

    def create_invitation(
        self,
        workspace_id: str,
        invited_by_user_id: str,
        req: CreateInvitationRequest,
    ) -> Tuple[WorkspaceInvitation, str]:
        """
        Creates a new workspace invitation with a single-use cryptographic token.
        Returns the invitation record and the raw token.
        """
        # 1. Authorization check
        if not self._authz.can(invited_by_user_id, Permission.WORKSPACE_MEMBERS_MANAGE, workspace_id=workspace_id):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to invite members to this workspace",
            )

        workspace = self._ws_repo.get_workspace(workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")

        # 1b. Enforce member limit quota
        from backend.app.services.usage import quota_service
        from backend.app.engines.usage.metrics import UsageMetrics
        quota_service.enforce_quota(
            workspace_id=workspace_id,
            metric_key=UsageMetrics.WORKSPACE_MEMBER_COUNT.key,
            quantity=1.0,
        )

        clean_email = validate_email_format(req.email)
        norm_email = normalize_email(clean_email)

        # 2. Check if already an active member
        existing_user = self._auth_repo.get_user_by_email(norm_email)
        if existing_user:
            m = self._auth_repo.get_workspace_member(workspace_id, existing_user.user_id)
            if m and m.status == MembershipStatus.ACTIVE:
                raise HTTPException(
                    status_code=400,
                    detail=f"User '{clean_email}' is already an active member of this workspace",
                )

        # 3. Check for existing pending invitation for this email in this workspace
        existing_pending = self._collab_repo.find_pending_invitation(workspace_id, norm_email)
        if existing_pending:
            # Revoke prior pending invitation so only one active invitation exists
            existing_pending.status = InvitationStatus.REVOKED
            existing_pending.revoked_at = datetime.now(timezone.utc).isoformat()
            self._collab_repo.save_invitation(existing_pending)

        # 4. Generate cryptographically secure token & SHA-256 hash
        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_session_token(raw_token)
        expires_at = (datetime.now(timezone.utc) + timedelta(days=req.expires_in_days)).isoformat()

        invitation = WorkspaceInvitation(
            workspace_id=workspace_id,
            email=clean_email,
            normalized_email=norm_email,
            invited_by_user_id=invited_by_user_id,
            intended_role=req.intended_role,
            status=InvitationStatus.PENDING,
            token_hash=token_hash,
            expires_at=expires_at,
            metadata=req.metadata,
        )
        self._collab_repo.save_invitation(invitation)

        # 5. Security audit & collaboration activity
        inviter = self._auth_repo.get_user(invited_by_user_id)
        inviter_name = inviter.display_name if inviter else "Administrator"

        self._auth_repo.record_audit_event(
            SecurityAuditEvent(
                user_id=invited_by_user_id,
                workspace_id=workspace_id,
                event_type=SecurityEventType.MEMBERSHIP_CREATED,
                result="SUCCESS",
                metadata={
                    "action": "INVITATION_CREATED",
                    "invitation_id": invitation.invitation_id,
                    "recipient_email": clean_email,
                    "intended_role": req.intended_role.value,
                },
            )
        )

        self._collab_repo.record_activity(
            CollaborationActivityEvent(
                workspace_id=workspace_id,
                actor_user_id=invited_by_user_id,
                event_type=CollaborationEventType.INVITATION_CREATED,
                details={
                    "invitation_id": invitation.invitation_id,
                    "email": clean_email,
                    "intended_role": req.intended_role.value,
                },
            )
        )

        # 6. Delivery & in-app notification if recipient has an existing user account
        self._delivery.deliver_invitation(invitation, raw_token, workspace.name, inviter_name)

        if existing_user:
            self._collab_repo.save_notification(
                Notification(
                    recipient_user_id=existing_user.user_id,
                    type=NotificationType.INVITATION_RECEIVED,
                    title=f"Invitation to {workspace.name}",
                    message=f"{inviter_name} invited you to join '{workspace.name}' as {req.intended_role.value}.",
                    action_url=f"/invite/{raw_token}",
                    metadata={"invitation_id": invitation.invitation_id, "workspace_id": workspace_id},
                )
            )
            # Phase 19 Enterprise Event Dispatch (safe deep-link without raw token)
            event_dispatcher.create_and_dispatch(
                event_type=ApplicationEventType.INVITATION_CREATED,
                actor_user_id=invited_by_user_id,
                workspace_id=workspace_id,
                resource_type="WORKSPACE",
                resource_id=workspace_id,
                metadata={
                    "recipient_user_id": existing_user.user_id,
                    "workspace_name": workspace.name,
                    "intended_role": req.intended_role.value,
                    "invitation_id": invitation.invitation_id,
                },
            )

        return invitation, raw_token

    def verify_invitation(self, raw_token: str) -> InvitationVerifyResponse:
        """Inspects invitation details for a given raw token without accepting it."""
        if not raw_token or len(raw_token) < 10:
            raise HTTPException(status_code=400, detail="Invalid invitation token")

        token_hash = hash_session_token(raw_token)
        invitation = self._collab_repo.get_invitation_by_token_hash(token_hash)
        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found or has been revoked")

        if invitation.status == InvitationStatus.REVOKED:
            raise HTTPException(status_code=410, detail="This invitation has been revoked")

        if invitation.status == InvitationStatus.ACCEPTED:
            raise HTTPException(status_code=400, detail="This invitation has already been accepted")

        exp = datetime.fromisoformat(invitation.expires_at)
        now = datetime.now(timezone.utc)
        if exp <= now or invitation.status == InvitationStatus.EXPIRED:
            raise HTTPException(status_code=410, detail="This invitation has expired")

        workspace = self._ws_repo.get_workspace(invitation.workspace_id)
        workspace_name = workspace.name if workspace else "Workspace"

        inviter = self._auth_repo.get_user(invitation.invited_by_user_id)
        inviter_name = inviter.display_name if inviter else "Administrator"

        return InvitationVerifyResponse(
            invitation_id=invitation.invitation_id,
            workspace_id=invitation.workspace_id,
            workspace_name=workspace_name,
            email=invitation.email,
            intended_role=invitation.intended_role,
            status=invitation.status,
            expires_at=invitation.expires_at,
            is_expired=False,
            invited_by_name=inviter_name,
        )

    def accept_invitation(self, raw_token: str, accepting_user_id: str) -> WorkspaceMember:
        """
        Accepts a valid invitation, grants workspace membership, and marks the token used.
        """
        token_hash = hash_session_token(raw_token)
        invitation = self._collab_repo.get_invitation_by_token_hash(token_hash)
        if not invitation:
            raise HTTPException(
                status_code=400,
                detail="Invitation is invalid or not found",
            )

        if invitation.status == InvitationStatus.REVOKED:
            raise HTTPException(status_code=410, detail="This invitation has been revoked")

        if invitation.status == InvitationStatus.EXPIRED:
            raise HTTPException(status_code=410, detail="This invitation has expired")

        if invitation.status == InvitationStatus.ACCEPTED:
            raise HTTPException(status_code=400, detail="This invitation has already been accepted")

        exp = datetime.fromisoformat(invitation.expires_at)
        if exp <= datetime.now(timezone.utc):
            invitation.status = InvitationStatus.EXPIRED
            self._collab_repo.save_invitation(invitation)
            raise HTTPException(status_code=410, detail="This invitation has expired")

        workspace = self._ws_repo.get_workspace(invitation.workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace no longer exists")

        user = self._auth_repo.get_user(accepting_user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User account not found")

        # 1. Create or reactivate WorkspaceMember
        existing_member = self._auth_repo.get_workspace_member(invitation.workspace_id, accepting_user_id)
        if existing_member:
            existing_member.status = MembershipStatus.ACTIVE
            existing_member.role = invitation.intended_role
            self._auth_repo.save_workspace_member(existing_member)
            member = existing_member
        else:
            member = WorkspaceMember(
                workspace_id=invitation.workspace_id,
                user_id=accepting_user_id,
                role=invitation.intended_role,
                status=MembershipStatus.ACTIVE,
            )
            self._auth_repo.save_workspace_member(member)

        # 2. Mark invitation ACCEPTED
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = datetime.now(timezone.utc).isoformat()
        self._collab_repo.save_invitation(invitation)

        # 3. Security audit & collaboration activity
        self._auth_repo.record_audit_event(
            SecurityAuditEvent(
                user_id=accepting_user_id,
                workspace_id=invitation.workspace_id,
                event_type=SecurityEventType.MEMBERSHIP_CREATED,
                result="SUCCESS",
                metadata={
                    "action": "INVITATION_ACCEPTED",
                    "invitation_id": invitation.invitation_id,
                    "role": invitation.intended_role.value,
                },
            )
        )

        self._collab_repo.record_activity(
            CollaborationActivityEvent(
                workspace_id=invitation.workspace_id,
                actor_user_id=accepting_user_id,
                event_type=CollaborationEventType.INVITATION_ACCEPTED,
                details={
                    "invitation_id": invitation.invitation_id,
                    "role": invitation.intended_role.value,
                },
            )
        )

        # 4. Notify inviter
        self._collab_repo.save_notification(
            Notification(
                recipient_user_id=invitation.invited_by_user_id,
                type=NotificationType.INVITATION_ACCEPTED,
                title="Invitation Accepted",
                message=f"{user.display_name} ({user.email}) accepted your invitation to '{workspace.name}'.",
                metadata={"workspace_id": invitation.workspace_id, "user_id": accepting_user_id},
            )
        )
        # Phase 19 Enterprise Event Dispatch
        event_dispatcher.create_and_dispatch(
            event_type=ApplicationEventType.INVITATION_ACCEPTED,
            actor_user_id=accepting_user_id,
            workspace_id=invitation.workspace_id,
            resource_type="WORKSPACE",
            resource_id=invitation.workspace_id,
            metadata={
                "recipient_user_id": invitation.invited_by_user_id,
                "workspace_name": workspace.name,
                "member_name": user.display_name,
                "invitation_id": invitation.invitation_id,
            },
        )

        logger.info(
            f"User {accepting_user_id} ({user.email}) accepted invitation {invitation.invitation_id} "
            f"to workspace {invitation.workspace_id} with role {invitation.intended_role.value}"
        )
        return member

    def revoke_invitation(self, invitation_id: str, revoker_user_id: str) -> WorkspaceInvitation:
        """Revokes an outstanding pending invitation."""
        invitation = self._collab_repo.get_invitation(invitation_id)
        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found")

        if not self._authz.can(revoker_user_id, Permission.WORKSPACE_MEMBERS_MANAGE, workspace_id=invitation.workspace_id):
            raise HTTPException(status_code=403, detail="Permission denied to revoke invitations")

        if invitation.status == InvitationStatus.ACCEPTED:
            raise HTTPException(status_code=400, detail="Cannot revoke an invitation that was already accepted")

        invitation.status = InvitationStatus.REVOKED
        invitation.revoked_at = datetime.now(timezone.utc).isoformat()
        self._collab_repo.save_invitation(invitation)

        self._collab_repo.record_activity(
            CollaborationActivityEvent(
                workspace_id=invitation.workspace_id,
                actor_user_id=revoker_user_id,
                event_type=CollaborationEventType.INVITATION_REVOKED,
                details={"invitation_id": invitation.invitation_id, "email": invitation.email},
            )
        )

        return invitation

    def resend_invitation(self, invitation_id: str, resender_user_id: str) -> Tuple[WorkspaceInvitation, str]:
        """
        Invalidates existing token, generates a fresh token, and resets expiration.
        """
        invitation = self._collab_repo.get_invitation(invitation_id)
        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found")

        if not self._authz.can(resender_user_id, Permission.WORKSPACE_MEMBERS_MANAGE, workspace_id=invitation.workspace_id):
            raise HTTPException(status_code=403, detail="Permission denied to resend invitations")

        if invitation.status == InvitationStatus.ACCEPTED:
            raise HTTPException(status_code=400, detail="Cannot resend an invitation that has already been accepted")

        # Generate new token and hash
        raw_token = secrets.token_urlsafe(32)
        invitation.token_hash = hash_session_token(raw_token)
        invitation.status = InvitationStatus.PENDING
        invitation.expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        invitation.revoked_at = None
        self._collab_repo.save_invitation(invitation)

        workspace = self._ws_repo.get_workspace(invitation.workspace_id)
        ws_name = workspace.name if workspace else "Workspace"
        resender = self._auth_repo.get_user(resender_user_id)
        resender_name = resender.display_name if resender else "Administrator"

        self._delivery.deliver_invitation(invitation, raw_token, ws_name, resender_name)

        self._collab_repo.record_activity(
            CollaborationActivityEvent(
                workspace_id=invitation.workspace_id,
                actor_user_id=resender_user_id,
                event_type=CollaborationEventType.INVITATION_RESENT,
                details={"invitation_id": invitation.invitation_id, "email": invitation.email},
            )
        )

        return invitation, raw_token

    def list_invitations(
        self,
        workspace_id: str,
        requesting_user_id: str,
        status: Optional[InvitationStatus] = None,
    ) -> List[InvitationResponse]:
        """Lists workspace invitations for authorized team members."""
        if not self._authz.can(requesting_user_id, Permission.WORKSPACE_MEMBERS_READ, workspace_id=workspace_id):
            raise HTTPException(status_code=403, detail="Permission denied to view workspace invitations")

        workspace = self._ws_repo.get_workspace(workspace_id)
        ws_name = workspace.name if workspace else "Workspace"

        invitations = self._collab_repo.list_invitations(workspace_id, status=status)
        results = []
        for inv in invitations:
            inviter = self._auth_repo.get_user(inv.invited_by_user_id)
            results.append(
                InvitationResponse(
                    invitation_id=inv.invitation_id,
                    workspace_id=inv.workspace_id,
                    workspace_name=ws_name,
                    email=inv.email,
                    intended_role=inv.intended_role,
                    status=inv.status,
                    expires_at=inv.expires_at,
                    created_at=inv.created_at,
                    invited_by_user_id=inv.invited_by_user_id,
                    invited_by_name=inviter.display_name if inviter else "Administrator",
                )
            )
        return results


# Global singleton instance
invitation_service = InvitationService()
