"""
AnalyzaX — Phase 24 Tests: Comprehensive Cross-Tenant Isolation, Universal IDOR Prevention & RBAC.
Verifies strict logical and physical isolation across all resource domains (AUTH-26, REQ-14, REQ-37).
"""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.engines.auth.models import RoleName, User, WorkspaceMember
from backend.app.engines.auth.permissions import Permissions
from backend.app.engines.auth.repository import AuthRepository
from backend.app.engines.workspace.models import Asset, AssetType, Project, Workspace
from backend.app.engines.workspace.repository import WorkspaceRepository
from backend.app.services.auth.authorization_service import AuthorizationService
from backend.app.main import app


def test_tenant_isolation_across_all_resource_domains(tmp_path):
    """
    Validates that Tenant A's resources are completely inaccessible to Tenant B
    across every supported resource type.
    """
    auth_dir = str(tmp_path / "auth")
    ws_dir = str(tmp_path / "workspace")
    auth_repo = AuthRepository(storage_dir=auth_dir)
    ws_repo = WorkspaceRepository(storage_dir=ws_dir)
    authz = AuthorizationService(auth_repository=auth_repo, workspace_repository=ws_repo)

    # Tenant Alpha (Victim / Target)
    user_alpha = User(
        user_id="usr_alpha",
        email="alpha@corp.local",
        email_normalized="alpha@corp.local",
        password_hash="hash_a",
        display_name="User Alpha",
    )
    auth_repo.save_user(user_alpha)
    ws_alpha = Workspace(workspace_id="ws_alpha", name="Alpha Corp", slug="alpha-corp")
    ws_repo.save_workspace(ws_alpha)
    auth_repo.save_workspace_member(WorkspaceMember(workspace_id="ws_alpha", user_id="usr_alpha", role=RoleName.OWNER))
    proj_alpha = Project(project_id="proj_alpha", workspace_id="ws_alpha", name="Alpha Secret Project", slug="alpha-proj")
    ws_repo.save_project(proj_alpha)

    # Populate assets for all resource domains
    resource_types = [
        (AssetType.DATASET, "ds_alpha_01"),
        (AssetType.QUERY, "sql_alpha_01"),
        (AssetType.STATISTICAL_ANALYSIS, "stat_alpha_01"),
        (AssetType.ML_EXPERIMENT, "ml_alpha_01"),
        (AssetType.FORECAST_EXPERIMENT, "fc_alpha_01"),
        (AssetType.DASHBOARD, "dash_alpha_01"),
        (AssetType.REPORT, "rep_alpha_01"),
        (AssetType.EXPORT, "exp_alpha_01"),
    ]

    for asset_type, entity_id in resource_types:
        asset = Asset(
            asset_id=f"ast_{entity_id}",
            workspace_id="ws_alpha",
            project_id="proj_alpha",
            name=f"Alpha {asset_type.value}",
            asset_type=asset_type,
            source_entity_id=entity_id,
        )
        ws_repo.save_asset(asset)

    # Tenant Beta (Adversary / External)
    user_beta = User(
        user_id="usr_beta",
        email="beta@rival.local",
        email_normalized="beta@rival.local",
        password_hash="hash_b",
        display_name="User Beta",
    )
    auth_repo.save_user(user_beta)
    ws_beta = Workspace(workspace_id="ws_beta", name="Beta LLC", slug="beta-llc")
    ws_repo.save_workspace(ws_beta)
    auth_repo.save_workspace_member(WorkspaceMember(workspace_id="ws_beta", user_id="usr_beta", role=RoleName.OWNER))
    proj_beta = Project(project_id="proj_beta", workspace_id="ws_beta", name="Beta Project", slug="beta-proj")
    ws_repo.save_project(proj_beta)

    # Verify Beta CANNOT perform any operations on Alpha's workspace or project
    assert authz.can("usr_beta", Permissions.WORKSPACE_READ, workspace_id="ws_alpha") is False
    assert authz.can("usr_beta", Permissions.WORKSPACE_UPDATE, workspace_id="ws_alpha") is False
    assert authz.can("usr_beta", Permissions.WORKSPACE_DELETE, workspace_id="ws_alpha") is False
    assert authz.can("usr_beta", Permissions.PROJECT_READ, workspace_id="ws_alpha", project_id="proj_alpha") is False
    assert authz.can("usr_beta", Permissions.PROJECT_DELETE, workspace_id="ws_alpha", project_id="proj_alpha") is False

    # Verify Beta CANNOT access any Alpha assets through IDOR reference
    for asset_type, entity_id in resource_types:
        ast_id = f"ast_{entity_id}"
        assert authz.can("usr_beta", Permissions.DATASET_READ, resource=entity_id) is False
        assert authz.can("usr_beta", Permissions.DATASET_READ, resource=ast_id) is False
        assert authz.can("usr_beta", Permissions.DATASET_DELETE, resource=ast_id) is False
        assert authz.can("usr_beta", Permissions.DASHBOARD_READ, resource=ast_id) is False
        assert authz.can("usr_beta", Permissions.EXPORT_READ, resource=ast_id) is False

    # Verify Cross-Workspace Context Injection (Spoofing Workspace Beta with Alpha Project)
    assert authz.can("usr_beta", Permissions.PROJECT_READ, workspace_id="ws_beta", project_id="proj_alpha") is False


def test_rbac_boundary_admin_cannot_delete_workspace(tmp_path):
    """Verifies that even an ADMIN member cannot execute destructive workspace deletion (OWNER only)."""
    auth_dir = str(tmp_path / "auth")
    ws_dir = str(tmp_path / "workspace")
    auth_repo = AuthRepository(storage_dir=auth_dir)
    ws_repo = WorkspaceRepository(storage_dir=ws_dir)
    authz = AuthorizationService(auth_repository=auth_repo, workspace_repository=ws_repo)

    ws = Workspace(workspace_id="ws_prod", name="Production WS", slug="prod-ws")
    ws_repo.save_workspace(ws)

    auth_repo.save_user(User(user_id="usr_owner", email="owner@prod.local", email_normalized="owner@prod.local", password_hash="h", display_name="Owner"))
    auth_repo.save_user(User(user_id="usr_admin", email="admin@prod.local", email_normalized="admin@prod.local", password_hash="h", display_name="Admin"))
    auth_repo.save_user(User(user_id="usr_editor", email="editor@prod.local", email_normalized="editor@prod.local", password_hash="h", display_name="Editor"))

    auth_repo.save_workspace_member(WorkspaceMember(workspace_id="ws_prod", user_id="usr_owner", role=RoleName.OWNER))
    auth_repo.save_workspace_member(WorkspaceMember(workspace_id="ws_prod", user_id="usr_admin", role=RoleName.ADMIN))
    auth_repo.save_workspace_member(WorkspaceMember(workspace_id="ws_prod", user_id="usr_editor", role=RoleName.EDITOR))

    # OWNER has delete permission
    assert authz.can("usr_owner", Permissions.WORKSPACE_DELETE, workspace_id="ws_prod") is True

    # ADMIN and EDITOR do NOT have delete permission
    assert authz.can("usr_admin", Permissions.WORKSPACE_DELETE, workspace_id="ws_prod") is False
    assert authz.can("usr_editor", Permissions.WORKSPACE_DELETE, workspace_id="ws_prod") is False


@pytest.mark.anyio
async def test_api_idor_attack_vectors():
    """Simulates direct HTTP IDOR attacks against project, workspace and asset endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register User 1
        u1_email = f"user1_{uuid.uuid4().hex[:6]}@domain.local"
        res1 = await client.post(
            "/api/v1/auth/register",
            json={"email": u1_email, "password": "Password123!", "display_name": "User 1"},
        )
        assert res1.status_code == 201
        token_1 = res1.json()["token"]
        ws_id_1 = res1.json()["workspace_id"]
        proj_id_1 = res1.json()["project_id"]
        headers_1 = {"Authorization": f"Bearer {token_1}"}

        # Register User 2 (Attacker)
        u2_email = f"user2_{uuid.uuid4().hex[:6]}@domain.local"
        res2 = await client.post(
            "/api/v1/auth/register",
            json={"email": u2_email, "password": "Password123!", "display_name": "Attacker"},
        )
        assert res2.status_code == 201
        token_2 = res2.json()["token"]
        headers_2 = {"Authorization": f"Bearer {token_2}"}

        # Vector 1: User 2 tries to GET User 1's workspace details
        ws_attack = await client.get(f"/api/v1/workspaces/{ws_id_1}", headers=headers_2)
        assert ws_attack.status_code in (403, 404)

        # Vector 2: User 2 tries to GET User 1's project details
        proj_attack = await client.get(f"/api/v1/projects/{proj_id_1}", headers=headers_2)
        assert proj_attack.status_code in (403, 404)

        # Vector 3: User 2 tries to DELETE User 1's project
        del_attack = await client.delete(f"/api/v1/projects/{proj_id_1}", headers=headers_2)
        assert del_attack.status_code in (403, 404)

        # Vector 4: User 2 tries to trigger cascading workspace deletion on User 1's workspace
        ws_del_attack = await client.post(
            f"/api/v1/governance/workspaces/{ws_id_1}/delete",
            headers=headers_2,
        )
        assert ws_del_attack.status_code in (403, 404)
