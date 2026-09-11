"""
Membership Application Service for Phase 17.
Coordinates workspace and project member administration, role changes, member removal,
and owner protection enforcement.
"""

from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from backend.app.core.logging import logger
from backend.app.engines.auth.models import (
    MembershipStatus,
    RoleName,
    SecurityEventType,
    UserStatus,
    WorkspaceMember,
    normalize_email,
)
from backend.app.engines.auth.permissions import Permissions
from backend.app.engines.auth.repository import AuthRepository, auth_repo
from backend.app.services.auth.authorization_service import AuthorizationService, authorization_service
from backend.app.services.auth.security_audit_service import SecurityAuditService, security_audit_service


class MembershipService:
    """
    Coordinates workspace and project membership management with strict permission
    and owner protection rules.
    """

    def __init__(
        self,
        repository: Optional[AuthRepository] = None,
        authz_service: Optional[AuthorizationService] = None,
        audit_service: Optional[SecurityAuditService] = None,
    ):
        self._repo = repository or auth_repo
        self._authz = authz_service or authorization_service
        self._audit = audit_service or security_audit_service

    def list_workspace_members(
        self,
        workspace_id: str,
        actor_user_id: str,
    ) -> List[Dict[str, Any]]:
        """Lists all active and suspended members of a workspace."""
        if not self._authz.can(actor_user_id, Permissions.WORKSPACE_READ, workspace_id=workspace_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view members of this workspace",
            )

        members = self._repo.list_workspace_members(workspace_id)
        result = []
        for m in members:
            user = self._repo.get_user(m.user_id)
            if user:
                result.append({
                    "membership_id": m.membership_id,
                    "workspace_id": m.workspace_id,
                    "user_id": user.user_id,
                    "email": user.email,
                    "display_name": user.display_name,
                    "role": m.role.value,
                    "status": m.status.value,
                    "created_at": m.created_at,
                    "updated_at": m.updated_at,
                })
        return result

    def add_workspace_member(
        self,
        workspace_id: str,
        email: str,
        role: RoleName,
        actor_user_id: str,
    ) -> WorkspaceMember:
        """Adds an existing user to a workspace."""
        if not self._authz.can(actor_user_id, Permissions.WORKSPACE_MANAGE_MEMBERS, workspace_id=workspace_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to manage members in this workspace",
            )

        email_norm = normalize_email(email)
        user = self._repo.get_user_by_email(email_norm)
        if not user or user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active user found with this email address",
            )

        existing = self._repo.get_workspace_member(workspace_id, user.user_id)
        if existing and existing.status == MembershipStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already an active member of this workspace",
            )

        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user.user_id,
            role=role,
            status=MembershipStatus.ACTIVE,
        )
        self._repo.save_workspace_member(member)

        self._audit.record_event(
            event_type=SecurityEventType.MEMBERSHIP_CREATED,
            user_id=actor_user_id,
            workspace_id=workspace_id,
            metadata={"target_user_id": user.user_id, "role": role.value},
        )
        return member

    def update_workspace_member_role(
        self,
        workspace_id: str,
        target_user_id: str,
        new_role: RoleName,
        actor_user_id: str,
    ) -> WorkspaceMember:
        """Updates a member's role within the workspace, enforcing owner protection."""
        if not self._authz.can(actor_user_id, Permissions.WORKSPACE_MANAGE_MEMBERS, workspace_id=workspace_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to change member roles in this workspace",
            )

        member = self._repo.get_workspace_member(workspace_id, target_user_id)
        if not member or member.status == MembershipStatus.REMOVED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace membership not found",
            )

        # Owner Protection Check (AUTH-37)
        if member.role == RoleName.OWNER and new_role != RoleName.OWNER:
            if not self._authz.can_remove_or_downgrade_owner(workspace_id, target_user_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot downgrade the last active workspace owner. Transfer ownership or promote another owner first.",
                )

        member.role = new_role
        self._repo.save_workspace_member(member)

        self._audit.record_event(
            event_type=SecurityEventType.MEMBERSHIP_ROLE_CHANGED,
            user_id=actor_user_id,
            workspace_id=workspace_id,
            metadata={"target_user_id": target_user_id, "new_role": new_role.value},
        )
        return member

    def remove_workspace_member(
        self,
        workspace_id: str,
        target_user_id: str,
        actor_user_id: str,
    ) -> bool:
        """Removes a member from the workspace, enforcing owner protection."""
        if not self._authz.can(actor_user_id, Permissions.WORKSPACE_MANAGE_MEMBERS, workspace_id=workspace_id):
            # Allow users to remove themselves from a workspace
            if actor_user_id != target_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to remove members from this workspace",
                )

        member = self._repo.get_workspace_member(workspace_id, target_user_id)
        if not member or member.status == MembershipStatus.REMOVED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace membership not found",
            )

        # Owner Protection Check (AUTH-37)
        if member.role == RoleName.OWNER:
            if not self._authz.can_remove_or_downgrade_owner(workspace_id, target_user_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the last active workspace owner. Transfer ownership first.",
                )

        success = self._repo.delete_workspace_member(workspace_id, target_user_id)
        if success:
            self._audit.record_event(
                event_type=SecurityEventType.MEMBERSHIP_REMOVED,
                user_id=actor_user_id,
                workspace_id=workspace_id,
                metadata={"removed_user_id": target_user_id},
            )
        return success

    def transfer_workspace_ownership(
        self,
        workspace_id: str,
        target_user_id: str,
        actor_user_id: str,
    ) -> bool:
        """Explicitly transfers primary workspace ownership from actor to target."""
        if not self._authz.can(actor_user_id, Permissions.WORKSPACE_TRANSFER_OWNERSHIP, workspace_id=workspace_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace owners can transfer ownership",
            )

        target_member = self._repo.get_workspace_member(workspace_id, target_user_id)
        if not target_member or target_member.status != MembershipStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user is not an active member of this workspace",
            )

        actor_member = self._repo.get_workspace_member(workspace_id, actor_user_id)
        if not actor_member or actor_member.role != RoleName.OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Actor is not an active owner",
            )

        # Promote target to OWNER
        target_member.role = RoleName.OWNER
        self._repo.save_workspace_member(target_member)

        # Demote previous owner to ADMIN
        actor_member.role = RoleName.ADMIN
        self._repo.save_workspace_member(actor_member)

        self._audit.record_event(
            event_type=SecurityEventType.OWNERSHIP_TRANSFERRED,
            user_id=actor_user_id,
            workspace_id=workspace_id,
            metadata={"new_owner_user_id": target_user_id, "previous_owner_user_id": actor_user_id},
        )
        return True


# Global instance
membership_service = MembershipService()
