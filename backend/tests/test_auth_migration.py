"""
Unit tests for Phase 17 Auth Migration Service (AUTH-53 to AUTH-60).
Verifies idempotent bootstrap and association of Phase 1–16 assets.
"""

from backend.app.engines.auth.models import RoleName
from backend.app.engines.auth.repository import AuthRepository
from backend.app.engines.workspace.models import Asset, AssetType, Project, Workspace
from backend.app.engines.workspace.repository import WorkspaceRepository
from backend.app.services.auth.auth_migration_service import AuthMigrationService


def test_auth_migration_idempotent_and_non_destructive(tmp_path):
    auth_dir = str(tmp_path / "auth")
    ws_dir = str(tmp_path / "workspace")
    auth_repo = AuthRepository(storage_dir=auth_dir)
    ws_repo = WorkspaceRepository(storage_dir=ws_dir)

    # Simulate existing Phase 16 data
    ws = Workspace(workspace_id="ws_default", name="Default Workspace", slug="default-workspace")
    ws_repo.save_workspace(ws)

    proj = Project(project_id="proj_default", workspace_id="ws_default", name="Default Project", slug="default-project")
    ws_repo.save_project(proj)

    asset = Asset(
        asset_id="asset_hist_1",
        workspace_id="ws_default",
        project_id="proj_default",
        name="Historical Dataset",
        asset_type=AssetType.DATASET,
        source_entity_id="ds_hist_1",
    )
    ws_repo.save_asset(asset)

    migration_srv = AuthMigrationService(auth_repository=auth_repo, workspace_repository=ws_repo)

    # 1. First run
    res1 = migration_srv.bootstrap_admin_and_migrate()
    assert res1["status"] == "COMPLETED"
    assert res1["created_user"] is True
    assert res1["created_membership"] is True
    assert res1["admin_email"] == "admin@analyzax.local"
    assert res1["associated_assets_count"] == 1

    # Verify admin in repo
    admin = auth_repo.get_user(res1["admin_user_id"])
    assert admin is not None
    assert admin.email == "admin@analyzax.local"

    # Verify membership
    member = auth_repo.get_workspace_member("ws_default", admin.user_id)
    assert member is not None
    assert member.role == RoleName.OWNER

    # Verify asset was NOT mutated
    preserved_asset = ws_repo.get_asset("asset_hist_1")
    assert preserved_asset is not None
    assert preserved_asset.name == "Historical Dataset"

    # 2. Second run (Idempotency)
    res2 = migration_srv.bootstrap_admin_and_migrate()
    assert res2["status"] == "COMPLETED"
    assert res2["created_user"] is False
    assert res2["created_membership"] is False
    # No duplicate users
    users = auth_repo.list_users()
    assert len(users) == 1
