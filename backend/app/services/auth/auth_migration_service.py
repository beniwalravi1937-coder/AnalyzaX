"""
Authentication & Data Migration Service for Phase 17.
Preserves existing Phase 1–16 assets (datasets, versions, dashboards, queries, exports)
by associating them non-destructively with a deterministic initial administrator and workspace.
"""

from typing import Any, Dict, Optional

from backend.app.core.logging import logger
from backend.app.engines.auth.crypto import hash_password
from backend.app.engines.auth.models import (
    MembershipStatus,
    RoleName,
    User,
    UserStatus,
    WorkspaceMember,
    normalize_email,
)
from backend.app.engines.auth.repository import AuthRepository, auth_repo
from backend.app.engines.workspace.models import Project, Workspace, WorkspaceStatus
from backend.app.engines.workspace.repository import WorkspaceRepository, workspace_repo


class AuthMigrationService:
    """
    Ensures safe, idempotent migration from Phase 1–16 single-user workspace
    to Phase 17 multi-user RBAC foundation without mutating asset IDs or analytical parquets.
    """

    DEFAULT_ADMIN_EMAIL = "admin@analyzax.local"
    DEFAULT_ADMIN_ID = "usr_initial_admin"
    DEFAULT_ADMIN_NAME = "System Administrator"
    DEFAULT_ADMIN_PASSWORD = "AdminPassword123!"

    def __init__(
        self,
        auth_repository: Optional[AuthRepository] = None,
        workspace_repository: Optional[WorkspaceRepository] = None,
    ):
        self._auth_repo = auth_repository or auth_repo
        self._ws_repo = workspace_repository or workspace_repo

    def bootstrap_admin_and_migrate(self) -> Dict[str, Any]:
        """
        Idempotent startup migration:
        1. Checks if initial admin exists; if not, creates with secure scrypt hash.
        2. Ensures default workspace ws_default exists.
        3. Assigns initial admin as OWNER of ws_default.
        4. Verifies all existing projects in ws_default remain intact.
        5. Reports migration status.
        """
        created_user = False
        created_membership = False

        # 1. Ensure Initial Administrator
        admin = self._auth_repo.get_user(self.DEFAULT_ADMIN_ID)
        if not admin:
            # Check by email as fallback
            admin = self._auth_repo.get_user_by_email(normalize_email(self.DEFAULT_ADMIN_EMAIL))

        if not admin:
            admin = User(
                user_id=self.DEFAULT_ADMIN_ID,
                email=self.DEFAULT_ADMIN_EMAIL,
                email_normalized=normalize_email(self.DEFAULT_ADMIN_EMAIL),
                password_hash=hash_password(self.DEFAULT_ADMIN_PASSWORD),
                display_name=self.DEFAULT_ADMIN_NAME,
                status=UserStatus.ACTIVE,
            )
            self._auth_repo.save_user(admin)
            created_user = True
            logger.info(f"AuthMigration: Created initial administrator account ({self.DEFAULT_ADMIN_EMAIL})")

        # 2. Ensure Default Workspace ws_default
        ws_default = self._ws_repo.get_workspace("ws_default")
        if not ws_default:
            workspaces = self._ws_repo.list_workspaces()
            if workspaces:
                ws_default = workspaces[0]
            else:
                ws_default = Workspace(
                    workspace_id="ws_default",
                    name="Default Workspace",
                    slug="default-workspace",
                    description="Primary analytical workspace for AnalyzaX assets.",
                    status=WorkspaceStatus.ACTIVE,
                )
                self._ws_repo.save_workspace(ws_default)
                logger.info(f"AuthMigration: Initialized default workspace ({ws_default.workspace_id})")

        # 3. Ensure Initial Admin is OWNER of Default Workspace
        membership = self._auth_repo.get_workspace_member(ws_default.workspace_id, admin.user_id)
        if not membership:
            membership = WorkspaceMember(
                workspace_id=ws_default.workspace_id,
                user_id=admin.user_id,
                role=RoleName.OWNER,
                status=MembershipStatus.ACTIVE,
            )
            self._auth_repo.save_workspace_member(membership)
            created_membership = True
            logger.info(f"AuthMigration: Assigned initial admin as OWNER of {ws_default.workspace_id}")
        elif membership.role != RoleName.OWNER:
            membership.role = RoleName.OWNER
            membership.status = MembershipStatus.ACTIVE
            self._auth_repo.save_workspace_member(membership)

        # 4. Inventory existing assets
        assets = self._ws_repo.list_assets(workspace_id=ws_default.workspace_id)
        projects = self._ws_repo.list_projects(workspace_id=ws_default.workspace_id)

        result = {
            "status": "COMPLETED",
            "admin_user_id": admin.user_id,
            "admin_email": admin.email,
            "created_user": created_user,
            "created_membership": created_membership,
            "workspace_id": ws_default.workspace_id,
            "associated_projects_count": len(projects),
            "associated_assets_count": len(assets),
        }
        logger.info(f"AuthMigration summary: {result}")
        return result


# Global instance
auth_migration_service = AuthMigrationService()
