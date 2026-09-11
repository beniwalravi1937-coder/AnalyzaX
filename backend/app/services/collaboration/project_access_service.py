"""
Project Access & Membership Service for Phase 18.
Coordinates explicit project-level memberships, roles, and boundaries.
Enforces the core invariant: No user may be added as a ProjectMember without active Workspace membership.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException

from backend.app.core.logging import logger
from backend.app.engines.auth.models import (
    MembershipStatus,
    ProjectMember,
    RoleName,
    SecurityAuditEvent,
    SecurityEventType,
)
from backend.app.engines.auth.permissions import Permission
from backend.app.engines.auth.repository import AuthRepository, auth_repo
from backend.app.engines.collaboration.models import (
    CollaborationActivityEvent,
    CollaborationEventType,
    Notification,
    NotificationType,
    ProjectMemberResponse,
)
from backend.app.engines.collaboration.repository import CollaborationRepository, collaboration_repo
from backend.app.engines.workspace.repository import WorkspaceRepository, workspace_repo
from backend.app.engines.notifications.models import ApplicationEventType
from backend.app.services.notifications.event_dispatcher import event_dispatcher
from backend.app.services.auth.authorization_service import AuthorizationService
from backend.app.services.collaboration.access_service import AccessService, access_service


class ProjectAccessService:
    """Coordinates explicit project memberships and role overrides."""

    def __init__(
        self,
        auth_repository: Optional[AuthRepository] = None,
        workspace_repository: Optional[WorkspaceRepository] = None,
        collab_repository: Optional[CollaborationRepository] = None,
        access_resolver: Optional[AccessService] = None,
    ):
        self._auth_repo = auth_repository or auth_repo
        self._ws_repo = workspace_repository or workspace_repo
        self._collab_repo = collab_repository or collaboration_repo
        self._access = access_resolver or access_service
        self._authz = AuthorizationService(self._auth_repo, self._ws_repo)

    def list_project_members(
        self,
        project_id: str,
        requesting_user_id: str,
    ) -> List[ProjectMemberResponse]:
        """Lists explicit project members for an authorized user."""
        project = self._ws_repo.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if not self._authz.can(requesting_user_id, Permission.PROJECT_READ, workspace_id=project.workspace_id, project_id=project_id):
            raise HTTPException(status_code=403, detail="Permission denied to view project members")

        members = self._auth_repo.list_project_members(project_id)
        results = []
        for m in members:
            u = self._auth_repo.get_user(m.user_id)
            if u:
                results.append(
                    ProjectMemberResponse(
                        membership_id=m.membership_id,
                        project_id=m.project_id,
                        user_id=u.user_id,
                        email=u.email,
                        display_name=u.display_name,
                        role=m.role,
                        status=m.status.value,
                        created_at=m.created_at,
                    )
                )
        return results

    def add_project_member(
        self,
        project_id: str,
        target_user_id: str,
        role: RoleName,
        requesting_user_id: str,
    ) -> ProjectMember:
        """
        Grants explicit project access to a user.
        Enforces invariant: User MUST have active workspace membership.
        """
        project = self._ws_repo.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 1. Authorization check
        if not self._authz.can(requesting_user_id, Permission.PROJECT_UPDATE, workspace_id=project.workspace_id, project_id=project_id):
            raise HTTPException(status_code=403, detail="Permission denied to manage project members")

        # 2. Invariant Check: Verify target user is an active member of the project's parent workspace
        ws_member = self._auth_repo.get_workspace_member(project.workspace_id, target_user_id)
        if not ws_member or ws_member.status != MembershipStatus.ACTIVE:
            raise HTTPException(
                status_code=400,
                detail="User must be an active member of the workspace before being added to a project",
            )

        target_user = self._auth_repo.get_user(target_user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="Target user not found")

        # 3. Create or update ProjectMember
        existing = self._auth_repo.get_project_member(project_id, target_user_id)
        if existing:
            existing.role = role
            existing.status = MembershipStatus.ACTIVE
            existing.updated_at = datetime.now(timezone.utc).isoformat()
            member = existing
        else:
            member = ProjectMember(
                project_id=project_id,
                user_id=target_user_id,
                role=role,
                status=MembershipStatus.ACTIVE,
            )

        self._auth_repo.save_project_member(member)
        self._access.invalidate_cache(user_id=target_user_id)

        # 4. Security Audit & Activity Logging
        self._auth_repo.record_audit_event(
            SecurityAuditEvent(
                user_id=requesting_user_id,
                workspace_id=project.workspace_id,
                project_id=project_id,
                event_type=SecurityEventType.MEMBERSHIP_ROLE_CHANGED,
                result="SUCCESS",
                metadata={"action": "PROJECT_MEMBER_ADDED", "target_user_id": target_user_id, "role": role.value},
            )
        )

        self._collab_repo.record_activity(
            CollaborationActivityEvent(
                workspace_id=project.workspace_id,
                project_id=project_id,
                actor_user_id=requesting_user_id,
                event_type=CollaborationEventType.MEMBER_ADDED,
                details={"target_user_id": target_user_id, "role": role.value},
            )
        )

        # 5. In-app notification
        self._collab_repo.save_notification(
            Notification(
                recipient_user_id=target_user_id,
                type=NotificationType.ROLE_CHANGED,
                title=f"Added to Project '{project.name}'",
                message=f"You have been granted {role.value} access to project '{project.name}'.",
                action_url=f"/projects/{project_id}",
            )
        )
        # Phase 19 Enterprise Event Dispatch
        event_dispatcher.create_and_dispatch(
            event_type=ApplicationEventType.MEMBER_ADDED,
            actor_user_id=requesting_user_id,
            workspace_id=project.workspace_id,
            project_id=project_id,
            resource_type="PROJECT",
            resource_id=project_id,
            metadata={
                "recipient_user_id": target_user_id,
                "project_name": project.name,
                "role": role.value,
            },
        )

        logger.info(f"User {target_user_id} added to project {project_id} as {role.value}")
        return member

    def update_project_member_role(
        self,
        project_id: str,
        target_user_id: str,
        new_role: RoleName,
        requesting_user_id: str,
    ) -> ProjectMember:
        """Updates a user's role on a specific project."""
        project = self._ws_repo.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if not self._authz.can(requesting_user_id, Permission.PROJECT_UPDATE, workspace_id=project.workspace_id, project_id=project_id):
            raise HTTPException(status_code=403, detail="Permission denied to update project member roles")

        member = self._auth_repo.get_project_member(project_id, target_user_id)
        if not member or member.status != MembershipStatus.ACTIVE:
            raise HTTPException(status_code=404, detail="Active project membership not found")

        member.role = new_role
        member.updated_at = datetime.now(timezone.utc).isoformat()
        self._auth_repo.save_project_member(member)
        self._access.invalidate_cache(user_id=target_user_id)

        self._collab_repo.record_activity(
            CollaborationActivityEvent(
                workspace_id=project.workspace_id,
                project_id=project_id,
                actor_user_id=requesting_user_id,
                event_type=CollaborationEventType.MEMBER_ROLE_CHANGED,
                details={"target_user_id": target_user_id, "new_role": new_role.value},
            )
        )
        # Phase 19 Enterprise Event Dispatch
        event_dispatcher.create_and_dispatch(
            event_type=ApplicationEventType.MEMBER_ROLE_CHANGED,
            actor_user_id=requesting_user_id,
            workspace_id=project.workspace_id,
            project_id=project_id,
            resource_type="PROJECT",
            resource_id=project_id,
            metadata={
                "recipient_user_id": target_user_id,
                "project_name": project.name,
                "new_role": new_role.value,
            },
        )
        return member

    def remove_project_member(
        self,
        project_id: str,
        target_user_id: str,
        requesting_user_id: str,
    ) -> bool:
        """Removes a user's explicit access to a project."""
        project = self._ws_repo.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if not self._authz.can(requesting_user_id, Permission.PROJECT_UPDATE, workspace_id=project.workspace_id, project_id=project_id):
            raise HTTPException(status_code=403, detail="Permission denied to remove project members")

        success = self._auth_repo.delete_project_member(project_id, target_user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Project member not found")

        self._access.invalidate_cache(user_id=target_user_id)

        self._collab_repo.record_activity(
            CollaborationActivityEvent(
                workspace_id=project.workspace_id,
                project_id=project_id,
                actor_user_id=requesting_user_id,
                event_type=CollaborationEventType.MEMBER_REMOVED,
                details={"target_user_id": target_user_id},
            )
        )
        # Phase 19 Enterprise Event Dispatch
        event_dispatcher.create_and_dispatch(
            event_type=ApplicationEventType.MEMBER_REMOVED,
            actor_user_id=requesting_user_id,
            workspace_id=project.workspace_id,
            project_id=project_id,
            resource_type="PROJECT",
            resource_id=project_id,
            metadata={
                "recipient_user_id": target_user_id,
                "project_name": project.name,
            },
        )
        return True


# Global singleton instance
project_access_service = ProjectAccessService()
