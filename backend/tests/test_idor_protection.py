"""
Unit & integration tests for Phase 17 Insecure Direct Object Reference (IDOR) Protection (AUTH-26).
Verifies that foreign valid IDs injected by a caller are strictly blocked server-side.
"""

from backend.app.engines.auth.models import RoleName, User, WorkspaceMember
from backend.app.engines.auth.permissions import Permissions
from backend.app.engines.auth.repository import AuthRepository
from backend.app.engines.workspace.models import Asset, AssetType, Project, Workspace
from backend.app.engines.workspace.repository import WorkspaceRepository
from backend.app.services.auth.authorization_service import AuthorizationService


def test_idor_foreign_id_injection_blocked(tmp_path):
    auth_dir = str(tmp_path / "auth")
    ws_dir = str(tmp_path / "workspace")
    auth_repo = AuthRepository(storage_dir=auth_dir)
    ws_repo = WorkspaceRepository(storage_dir=ws_dir)
    authz = AuthorizationService(auth_repository=auth_repo, workspace_repository=ws_repo)

    # Tenant 1: Attacker User A
    user_a = User(user_id="usr_attacker", email="attacker@evil.com", email_normalized="attacker@evil.com", password_hash="dummy", display_name="Attacker")
    auth_repo.save_user(user_a)
    ws_a = Workspace(workspace_id="ws_attacker", name="Attacker WS", slug="attacker-ws")
    ws_repo.save_workspace(ws_a)
    auth_repo.save_workspace_member(WorkspaceMember(workspace_id="ws_attacker", user_id="usr_attacker", role=RoleName.OWNER))
    proj_a = Project(project_id="proj_attacker", workspace_id="ws_attacker", name="Attacker Proj", slug="attacker-proj")
    ws_repo.save_project(proj_a)

    # Tenant 2: Victim User B
    user_b = User(user_id="usr_victim", email="victim@target.com", email_normalized="victim@target.com", password_hash="dummy", display_name="Victim")
    auth_repo.save_user(user_b)
    ws_b = Workspace(workspace_id="ws_victim", name="Victim WS", slug="victim-ws")
    ws_repo.save_workspace(ws_b)
    auth_repo.save_workspace_member(WorkspaceMember(workspace_id="ws_victim", user_id="usr_victim", role=RoleName.OWNER))
    proj_b = Project(project_id="proj_victim", workspace_id="ws_victim", name="Victim Proj", slug="victim-proj")
    ws_repo.save_project(proj_b)

    # Victim assets
    assets = [
        Asset(asset_id="asset_vic_ds", workspace_id="ws_victim", project_id="proj_victim", name="Victim Dataset", asset_type=AssetType.DATASET, source_entity_id="ds_vic_1"),
        Asset(asset_id="asset_vic_dash", workspace_id="ws_victim", project_id="proj_victim", name="Victim Dashboard", asset_type=AssetType.DASHBOARD, source_entity_id="dash_vic_1"),
        Asset(asset_id="asset_vic_rep", workspace_id="ws_victim", project_id="proj_victim", name="Victim Report", asset_type=AssetType.REPORT, source_entity_id="rep_vic_1"),
        Asset(asset_id="asset_vic_exp", workspace_id="ws_victim", project_id="proj_victim", name="Victim Export", asset_type=AssetType.EXPORT, source_entity_id="exp_vic_1"),
    ]
    for a in assets:
        ws_repo.save_asset(a)

    # Attack Vector 1: Direct workspace ID reference
    assert authz.can("usr_attacker", Permissions.WORKSPACE_READ, workspace_id="ws_victim") is False

    # Attack Vector 2: Direct project ID reference
    assert authz.can("usr_attacker", Permissions.PROJECT_READ, project_id="proj_victim") is False

    # Attack Vector 3: Mismatched project and workspace (spoofing attacker workspace with victim project)
    assert authz.can("usr_attacker", Permissions.PROJECT_READ, workspace_id="ws_attacker", project_id="proj_victim") is False

    # Attack Vector 4: Injected dataset ID
    assert authz.can("usr_attacker", Permissions.DATASET_READ, resource="ds_vic_1") is False
    assert authz.can("usr_attacker", Permissions.DATASET_READ, resource="asset_vic_ds") is False

    # Attack Vector 5: Injected dashboard ID
    assert authz.can("usr_attacker", Permissions.DASHBOARD_READ, resource="dash_vic_1") is False

    # Attack Vector 6: Injected report ID
    assert authz.can("usr_attacker", Permissions.REPORT_READ, resource="rep_vic_1") is False

    # Attack Vector 7: Injected export download ID
    assert authz.can("usr_attacker", Permissions.EXPORT_READ, resource="exp_vic_1") is False
