"""
Integration tests for SQL, AI Analyst, and Export scope authorization (AUTH-30, AUTH-31, AUTH-32).
Verifies that analytical execution layers strictly inherit user RBAC scope and reject foreign resources.
"""

import pytest

from backend.app.engines.auth.models import RoleName, User, WorkspaceMember
from backend.app.engines.auth.permissions import Permissions
from backend.app.engines.auth.repository import AuthRepository
from backend.app.engines.workspace.models import Asset, AssetType, Project, Workspace
from backend.app.engines.workspace.repository import WorkspaceRepository
from backend.app.services.auth.authorization_service import AuthorizationService


def test_sql_and_export_authorization_boundaries(tmp_path):
    auth_dir = str(tmp_path / "auth")
    ws_dir = str(tmp_path / "workspace")
    auth_repo = AuthRepository(storage_dir=auth_dir)
    ws_repo = WorkspaceRepository(storage_dir=ws_dir)
    authz = AuthorizationService(auth_repository=auth_repo, workspace_repository=ws_repo)

    # 1. Setup User A in WS A
    ua = User(user_id="usr_analyst_a", email="a@co.com", email_normalized="a@co.com", password_hash="dummy", display_name="Analyst A")
    auth_repo.save_user(ua)
    wsa = Workspace(workspace_id="ws_a", name="WS A", slug="ws-a")
    ws_repo.save_workspace(wsa)
    auth_repo.save_workspace_member(WorkspaceMember(workspace_id="ws_a", user_id="usr_analyst_a", role=RoleName.ANALYST))
    proja = Project(project_id="proj_a", workspace_id="ws_a", name="Proj A", slug="proj-a")
    ws_repo.save_project(proja)

    # 2. Setup User B in WS B with confidential assets
    ub = User(user_id="usr_analyst_b", email="b@co.com", email_normalized="b@co.com", password_hash="dummy", display_name="Analyst B")
    auth_repo.save_user(ub)
    wsb = Workspace(workspace_id="ws_b", name="WS B", slug="ws-b")
    ws_repo.save_workspace(wsb)
    auth_repo.save_workspace_member(WorkspaceMember(workspace_id="ws_b", user_id="usr_analyst_b", role=RoleName.OWNER))
    projb = Project(project_id="proj_b", workspace_id="ws_b", name="Proj B", slug="proj-b")
    ws_repo.save_project(projb)

    # Assets in Project B: Dataset, Query, Export
    ds_b = Asset(
        asset_id="asset_ds_b",
        workspace_id="ws_b",
        project_id="proj_b",
        name="Confidential Salaries",
        asset_type=AssetType.DATASET,
        source_entity_id="ds_salaries_b",
    )
    ws_repo.save_asset(ds_b)

    export_b = Asset(
        asset_id="asset_exp_b",
        workspace_id="ws_b",
        project_id="proj_b",
        name="Q3 Financial Export",
        asset_type=AssetType.EXPORT,
        source_entity_id="job_exp_b",
    )
    ws_repo.save_asset(export_b)

    # 3. SQL Authorization: User A attempts to query Dataset B
    # Must fail authorization before query execution!
    can_query_b = authz.can(
        user_id="usr_analyst_a",
        permission=Permissions.QUERY_CREATE,
        resource="ds_salaries_b",
    )
    assert can_query_b is False, "User A must not be authorized to execute SQL against Dataset B"

    # 4. AI Analyst Tool Authorization: AI tool executing on behalf of User A checks access to Dataset B
    can_ai_read_b = authz.can(
        user_id="usr_analyst_a",
        permission=Permissions.DATASET_READ,
        resource="asset_ds_b",
    )
    assert can_ai_read_b is False, "AI Analyst must not retrieve datasets across workspace boundaries"

    # 5. Export Authorization: User A attempts to download Export B
    can_download_exp_b = authz.can(
        user_id="usr_analyst_a",
        permission=Permissions.EXPORT_READ,
        resource="job_exp_b",
    )
    assert can_download_exp_b is False, "User A must not be authorized to download Export B"

    # 6. User B CAN query their own dataset and download their own export
    assert authz.can("usr_analyst_b", Permissions.QUERY_CREATE, resource="ds_salaries_b") is True
    assert authz.can("usr_analyst_b", Permissions.EXPORT_READ, resource="job_exp_b") is True
