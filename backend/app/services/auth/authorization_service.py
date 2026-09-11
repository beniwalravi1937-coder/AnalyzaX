"""
Centralized Authorization Service for Phase 17.
Enforces multi-tier RBAC, workspace & project scope resolution, permission checks,
cross-workspace isolation, IDOR prevention, and Owner Protection.
"""

from typing import Any, List, Optional

from backend.app.core.logging import logger
from backend.app.engines.auth.models import (
    MembershipStatus,
    RoleName,
    User,
    UserStatus,
)
from backend.app.engines.auth.permissions import has_permission
from backend.app.engines.auth.repository import AuthRepository, auth_repo
from backend.app.engines.workspace.repository import WorkspaceRepository, workspace_repo


class AuthorizationService:
    """
    Evaluates server-side authorization decisions for all analytical resources and actions.
    Rule: Never trust the frontend; all authorization must be determined server-side.
    """

    def __init__(
        self,
        auth_repository: Optional[AuthRepository] = None,
        workspace_repository: Optional[WorkspaceRepository] = None,
    ):
        self._auth_repo = auth_repository or auth_repo
        self._ws_repo = workspace_repository or workspace_repo

    def can(
        self,
        user_id: str,
        permission: str,
        workspace_id: Optional[str] = None,
        project_id: Optional[str] = None,
        resource: Optional[Any] = None,
    ) -> bool:
        """
        Determines whether user_id is authorized to perform permission in the given scope.
        Flow:
          1. Verify user exists and status == ACTIVE.
          2. If workspace_id is provided, verify active membership in that workspace.
          3. If project_id is provided:
             a. Verify project exists and belongs to workspace_id (cross-project / IDOR protection).
             b. Look for explicit project membership override.
             c. If no explicit project membership, inherit workspace role.
          4. Evaluate role against permission matrix.
        """
        user = self._auth_repo.get_user(user_id)
        if not user or user.status != UserStatus.ACTIVE:
            logger.debug(f"Auth check failed: User {user_id} not found or not active")
            return False

        # If resource is provided, resolve workspace_id and project_id from it
        if resource:
            if isinstance(resource, str):
                # Check if resource is a project ID
                proj = self._ws_repo.get_project(resource)
                if proj:
                    project_id = proj.project_id
                    workspace_id = proj.workspace_id
                else:
                    # Check if resource is a workspace ID
                    ws = self._ws_repo.get_workspace(resource)
                    if ws:
                        workspace_id = ws.workspace_id
                    else:
                        # Check if resource is an asset ID or source entity ID
                        asset = self._ws_repo.get_asset(resource) or self._ws_repo.find_asset_by_source_id(resource)
                        if asset:
                            workspace_id = asset.workspace_id
                            project_id = asset.project_id
            else:
                if not workspace_id and hasattr(resource, "workspace_id"):
                    workspace_id = getattr(resource, "workspace_id")
                if not project_id and hasattr(resource, "project_id"):
                    project_id = getattr(resource, "project_id")

        role: Optional[RoleName] = None

        if workspace_id:
            # Check active workspace membership
            ws_member = self._auth_repo.get_workspace_member(workspace_id, user_id)
            if not ws_member or ws_member.status != MembershipStatus.ACTIVE:
                logger.debug(f"Auth check failed: User {user_id} not a member of workspace {workspace_id}")
                return False

            role = ws_member.role

            # If project_id is also supplied, check project scope & inheritance
            if project_id:
                # IDOR check: verify project belongs to workspace_id
                project = self._ws_repo.get_project(project_id)
                if not project or project.workspace_id != workspace_id:
                    logger.debug(
                        f"Auth check failed: Project {project_id} not in workspace {workspace_id} (IDOR attempt)"
                    )
                    return False

                # Check if there is an explicit project membership override
                proj_member = self._auth_repo.get_project_member(project_id, user_id)
                if proj_member:
                    if proj_member.status == MembershipStatus.ACTIVE:
                        role = proj_member.role
                    elif proj_member.status == MembershipStatus.SUSPENDED:
                        return False
                # If no explicit project membership, role remains inherited from workspace

        elif project_id:
            # Only project_id was provided: resolve project to find its workspace
            project = self._ws_repo.get_project(project_id)
            if not project:
                logger.debug(f"Auth check failed: Project {project_id} does not exist")
                return False

            workspace_id = project.workspace_id
            return self.can(user_id, permission, workspace_id=workspace_id, project_id=project_id, resource=resource)

        else:
            # Global/account-level permission (e.g. profile management)
            return True

        if role and has_permission(role, permission):
            return True

        # Check if direct ResourceShare grants access for this specific resource
        if resource:
            try:
                from backend.app.services.collaboration.access_service import access_service
                from backend.app.engines.collaboration.models import ResourceType
                res_id = str(resource) if isinstance(resource, str) else getattr(resource, "asset_id", getattr(resource, "id", None))
                if res_id:
                    eff = access_service.resolve_effective_access(user_id, ResourceType.DATASET, res_id)
                    if permission.endswith(":read") and eff.can_view:
                        return True
                    if permission.endswith(":update") and eff.can_edit:
                        return True
                    if permission.startswith("export:") and eff.can_export:
                        return True
            except Exception:
                pass

        return False

    def get_effective_role(
        self,
        user_id: str,
        workspace_id: str,
        project_id: Optional[str] = None,
    ) -> Optional[RoleName]:
        """Resolves the effective role for a user in a given workspace/project scope."""
        ws_member = self._auth_repo.get_workspace_member(workspace_id, user_id)
        if not ws_member or ws_member.status != MembershipStatus.ACTIVE:
            return None

        role = ws_member.role
        if project_id:
            proj_member = self._auth_repo.get_project_member(project_id, user_id)
            if proj_member and proj_member.status == MembershipStatus.ACTIVE:
                role = proj_member.role

        return role

    def get_accessible_workspaces(self, user_id: str) -> List[str]:
        """Returns list of workspace IDs where user has an ACTIVE membership."""
        memberships = self._auth_repo.list_user_workspaces(user_id)
        return [m.workspace_id for m in memberships if m.status == MembershipStatus.ACTIVE]

    def get_accessible_projects(self, user_id: str, workspace_id: str) -> List[str]:
        """
        Returns list of project IDs within workspace accessible to the user.
        By default, all projects in the workspace are accessible via inherited membership,
        unless explicitly suspended at the project level.
        """
        ws_member = self._auth_repo.get_workspace_member(workspace_id, user_id)
        if not ws_member or ws_member.status != MembershipStatus.ACTIVE:
            return []

        all_projects = self._ws_repo.list_projects(workspace_id=workspace_id)
        accessible = []
        for p in all_projects:
            pm = self._auth_repo.get_project_member(p.project_id, user_id)
            if pm and pm.status == MembershipStatus.SUSPENDED:
                continue
            accessible.append(p.project_id)
        return accessible

    def can_remove_or_downgrade_owner(self, workspace_id: str, target_user_id: str) -> bool:
        """
        Owner Protection (AUTH-37):
        Checks whether the target user can safely be removed or have their role changed.
        If the target is currently an OWNER, there must be at least one OTHER active OWNER.
        """
        target_member = self._auth_repo.get_workspace_member(workspace_id, target_user_id)
        if not target_member or target_member.role != RoleName.OWNER:
            return True

        active_owners = self._auth_repo.count_active_workspace_owners(workspace_id)
        return active_owners > 1


# Global instance
authorization_service = AuthorizationService()
authz_service = authorization_service
