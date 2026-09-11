"""
Golden Multi-User Test: Cross-Tenant Isolation & Membership Progression.
Verifies complete boundary enforcement between tenants, role upgrades, and instant revocation.
"""

import pytest
from backend.app.engines.auth.models import (
    MembershipStatus,
    RoleName,
    User,
    UserStatus,
    WorkspaceMember,
)
from backend.app.engines.auth.permissions import Permissions
from backend.app.engines.auth.repository import AuthRepository
from backend.app.engines.workspace.models import Asset, AssetType, Project, Workspace
from backend.app.engines.workspace.repository import WorkspaceRepository
from backend.app.services.auth.authorization_service import AuthorizationService
from backend.app.services.auth.membership_service import MembershipService


def test_cross_tenant_isolation_and_progression(tmp_path):
    auth_dir = str(tmp_path / "auth")
    ws_dir = str(tmp_path / "workspace")
    auth_repo = AuthRepository(storage_dir=auth_dir)
    ws_repo = WorkspaceRepository(storage_dir=ws_dir)
    authz = AuthorizationService(auth_repository=auth_repo, workspace_repository=ws_repo)
    membership_srv = MembershipService(repository=auth_repo, authz_service=authz)

    # 1. Create User A, Workspace A, Project A, Asset A
    user_a = User(
        user_id="usr_a",
        email="alice@tenant-a.com",
        email_normalized="alice@tenant-a.com",
        password_hash="scrypt$dummy",
        display_name="Alice",
    )
    auth_repo.save_user(user_a)

    ws_a = Workspace(workspace_id="ws_a", name="Workspace A", slug="workspace-a")
    ws_repo.save_workspace(ws_a)
    auth_repo.save_workspace_member(
        WorkspaceMember(workspace_id="ws_a", user_id="usr_a", role=RoleName.OWNER)
    )

    proj_a = Project(project_id="proj_a", workspace_id="ws_a", name="Project A", slug="project-a")
    ws_repo.save_project(proj_a)

    asset_a = Asset(
        asset_id="asset_dataset_a",
        workspace_id="ws_a",
        project_id="proj_a",
        name="Sales Dataset A",
        asset_type=AssetType.DATASET,
        source_entity_id="ds_a",
    )
    ws_repo.save_asset(asset_a)

    # 2. Create User B, Workspace B, Project B, Asset B
    user_b = User(
        user_id="usr_b",
        email="bob@tenant-b.com",
        email_normalized="bob@tenant-b.com",
        password_hash="scrypt$dummy",
        display_name="Bob",
    )
    auth_repo.save_user(user_b)

    ws_b = Workspace(workspace_id="ws_b", name="Workspace B", slug="workspace-b")
    ws_repo.save_workspace(ws_b)
    auth_repo.save_workspace_member(
        WorkspaceMember(workspace_id="ws_b", user_id="usr_b", role=RoleName.OWNER)
    )

    proj_b = Project(project_id="proj_b", workspace_id="ws_b", name="Project B", slug="project-b")
    ws_repo.save_project(proj_b)

    asset_b = Asset(
        asset_id="asset_dataset_b",
        workspace_id="ws_b",
        project_id="proj_b",
        name="Financial Dataset B",
        asset_type=AssetType.DATASET,
        source_entity_id="ds_b",
    )
    ws_repo.save_asset(asset_b)

    # 3. VERIFY ISOLATION: User A cannot access Workspace B / Project B / Asset B
    assert authz.can(user_a.user_id, Permissions.WORKSPACE_READ, workspace_id="ws_b") is False
    assert authz.can(user_a.user_id, Permissions.PROJECT_READ, project_id="proj_b") is False
    assert authz.can(user_a.user_id, Permissions.DATASET_READ, resource="asset_dataset_b") is False
    assert authz.can(user_a.user_id, Permissions.DATASET_READ, resource="ds_b") is False

    # VERIFY ISOLATION: User B cannot access Workspace A / Project A / Asset A
    assert authz.can(user_b.user_id, Permissions.WORKSPACE_READ, workspace_id="ws_a") is False
    assert authz.can(user_b.user_id, Permissions.PROJECT_READ, project_id="proj_a") is False
    assert authz.can(user_b.user_id, Permissions.DATASET_READ, resource="asset_dataset_a") is False

    # 4. ADD User B to Workspace A as VIEWER
    membership_srv.add_workspace_member(
        workspace_id="ws_a",
        email="bob@tenant-b.com",
        role=RoleName.VIEWER,
        actor_user_id=user_a.user_id,
    )

    # Bob can now READ Asset A
    assert authz.can(user_b.user_id, Permissions.DATASET_READ, resource="asset_dataset_a") is True
    # But Bob CANNOT delete Asset A or manage members
    assert authz.can(user_b.user_id, Permissions.DATASET_DELETE, resource="asset_dataset_a") is False
    assert authz.can(user_b.user_id, Permissions.WORKSPACE_MANAGE_MEMBERS, workspace_id="ws_a") is False

    # 5. UPGRADE User B to EDITOR
    membership_srv.update_workspace_member_role(
        workspace_id="ws_a",
        target_user_id=user_b.user_id,
        new_role=RoleName.EDITOR,
        actor_user_id=user_a.user_id,
    )

    # Bob can now update Asset A
    assert authz.can(user_b.user_id, Permissions.DATASET_UPDATE, resource="asset_dataset_a") is True
    # Still cannot manage members
    assert authz.can(user_b.user_id, Permissions.WORKSPACE_MANAGE_MEMBERS, workspace_id="ws_a") is False

    # 6. UPGRADE User B to ADMIN
    membership_srv.update_workspace_member_role(
        workspace_id="ws_a",
        target_user_id=user_b.user_id,
        new_role=RoleName.ADMIN,
        actor_user_id=user_a.user_id,
    )
    assert authz.can(user_b.user_id, Permissions.WORKSPACE_MANAGE_MEMBERS, workspace_id="ws_a") is True
    # But cannot transfer ownership (only OWNER can)
    assert authz.can(user_b.user_id, Permissions.WORKSPACE_TRANSFER_OWNERSHIP, workspace_id="ws_a") is False

    # 7. REMOVE User B from Workspace A
    membership_srv.remove_workspace_member(
        workspace_id="ws_a",
        target_user_id=user_b.user_id,
        actor_user_id=user_a.user_id,
    )

    # Access instantly disappears!
    assert authz.can(user_b.user_id, Permissions.WORKSPACE_READ, workspace_id="ws_a") is False
    assert authz.can(user_b.user_id, Permissions.PROJECT_READ, project_id="proj_a") is False
    assert authz.can(user_b.user_id, Permissions.DATASET_READ, resource="asset_dataset_a") is False
