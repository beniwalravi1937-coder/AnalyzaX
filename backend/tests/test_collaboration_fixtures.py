"""
Test fixtures and helpers for Phase 18 Multi-User Collaboration & Sharing tests.
Sets up User A (OWNER), User B (EDITOR), and User C (VIEWER) in isolated workspaces.
"""

from datetime import datetime, timezone
import os
import shutil
import tempfile
from typing import Dict, Tuple

import pytest

from backend.app.engines.auth.crypto import hash_password
from backend.app.engines.auth.models import MembershipStatus, RoleName, User, WorkspaceMember
from backend.app.engines.auth.repository import AuthRepository
from backend.app.engines.collaboration.models import (
    ResourceType,
    SharePermission,
    ShareRecipientType,
    ShareStatus,
)
from backend.app.engines.collaboration.repository import CollaborationRepository
from backend.app.engines.workspace.models import (
    Asset,
    AssetStatus,
    AssetType,
    Project,
    Workspace,
)
from backend.app.engines.workspace.repository import WorkspaceRepository
from backend.app.services.auth.authorization_service import AuthorizationService
from backend.app.services.collaboration.access_service import AccessService
from backend.app.services.collaboration.invitation_service import InvitationService
from backend.app.services.collaboration.project_access_service import ProjectAccessService
from backend.app.services.collaboration.share_service import ShareService
from backend.app.services.collaboration.shared_resource_service import SharedResourceService


class CollabTestContext:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="collab_test_")
        self.auth_dir = os.path.join(self.temp_dir, "auth")
        self.ws_dir = os.path.join(self.temp_dir, "workspace")
        self.collab_dir = os.path.join(self.temp_dir, "collaboration")

        self.auth_repo = AuthRepository(storage_dir=self.auth_dir)
        self.ws_repo = WorkspaceRepository(storage_dir=self.ws_dir)
        self.collab_repo = CollaborationRepository(storage_dir=self.collab_dir)

        self.authz = AuthorizationService(self.auth_repo, self.ws_repo)
        self.access = AccessService(self.collab_repo, self.auth_repo, self.ws_repo)
        self.inv_service = InvitationService(self.collab_repo, self.auth_repo, self.ws_repo)
        self.share_service = ShareService(self.collab_repo, self.auth_repo, self.ws_repo, self.access)
        self.project_access = ProjectAccessService(self.auth_repo, self.ws_repo, self.collab_repo, self.access)
        self.shared_res = SharedResourceService(self.collab_repo, self.auth_repo, self.ws_repo, self.access)

        self._setup_fixtures()

    def _setup_fixtures(self):
        # 1. Users
        self.user_a = User(
            user_id="usr_a_owner",
            email="alice@analyzax.local",
            email_normalized="alice@analyzax.local",
            password_hash=hash_password("Password123!")[0],
            display_name="Alice Owner",
        )
        self.user_b = User(
            user_id="usr_b_editor",
            email="bob@analyzax.local",
            email_normalized="bob@analyzax.local",
            password_hash=hash_password("Password123!")[0],
            display_name="Bob Editor",
        )
        self.user_c = User(
            user_id="usr_c_viewer",
            email="charlie@analyzax.local",
            email_normalized="charlie@analyzax.local",
            password_hash=hash_password("Password123!")[0],
            display_name="Charlie Viewer",
        )
        self.user_external = User(
            user_id="usr_ext_user",
            email="eve@external.local",
            email_normalized="eve@external.local",
            password_hash=hash_password("Password123!")[0],
            display_name="Eve External",
        )

        for u in (self.user_a, self.user_b, self.user_c, self.user_external):
            self.auth_repo.save_user(u)

        # 2. Workspace A
        self.ws_a = Workspace(
            workspace_id="ws_collab_a",
            name="Workspace A",
            slug="workspace-a",
            owner_user_id=self.user_a.user_id,
        )
        self.ws_repo.save_workspace(self.ws_a)

        # Workspace memberships
        self.auth_repo.save_workspace_member(
            WorkspaceMember(
                workspace_id=self.ws_a.workspace_id,
                user_id=self.user_a.user_id,
                role=RoleName.OWNER,
                status=MembershipStatus.ACTIVE,
            )
        )
        self.auth_repo.save_workspace_member(
            WorkspaceMember(
                workspace_id=self.ws_a.workspace_id,
                user_id=self.user_b.user_id,
                role=RoleName.EDITOR,
                status=MembershipStatus.ACTIVE,
            )
        )
        self.auth_repo.save_workspace_member(
            WorkspaceMember(
                workspace_id=self.ws_a.workspace_id,
                user_id=self.user_c.user_id,
                role=RoleName.VIEWER,
                status=MembershipStatus.ACTIVE,
            )
        )

        # 3. Projects
        self.proj_a = Project(
            project_id="proj_collab_a",
            workspace_id=self.ws_a.workspace_id,
            name="Project A",
            slug="project-a",
            created_by=self.user_a.user_id,
        )
        self.proj_b = Project(
            project_id="proj_collab_b",
            workspace_id=self.ws_a.workspace_id,
            name="Project B",
            slug="project-b",
            created_by=self.user_a.user_id,
        )
        self.ws_repo.save_project(self.proj_a)
        self.ws_repo.save_project(self.proj_b)

        # 4. Assets
        self.ds_a = Asset(
            asset_id="ds_collab_a",
            project_id=self.proj_a.project_id,
            workspace_id=self.ws_a.workspace_id,
            asset_type=AssetType.DATASET,
            source_entity_id="ds_collab_a",
            name="Dataset Alpha",
            created_by=self.user_a.user_id,
        )
        self.dash_a = Asset(
            asset_id="dash_collab_a",
            project_id=self.proj_a.project_id,
            workspace_id=self.ws_a.workspace_id,
            asset_type=AssetType.DASHBOARD,
            source_entity_id="dash_collab_a",
            name="Dashboard Alpha",
            created_by=self.user_a.user_id,
        )
        self.report_a = Asset(
            asset_id="rep_collab_a",
            project_id=self.proj_a.project_id,
            workspace_id=self.ws_a.workspace_id,
            asset_type=AssetType.REPORT,
            source_entity_id="rep_collab_a",
            name="Report Alpha",
            created_by=self.user_a.user_id,
        )
        self.ws_repo.save_asset(self.ds_a)
        self.ws_repo.save_asset(self.dash_a)
        self.ws_repo.save_asset(self.report_a)

    def cleanup(self):
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass
