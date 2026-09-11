import os
import shutil
import pytest
from backend.app.engines.workspace.models import (
    Workspace,
    Project,
    Asset,
    AssetRelationship,
    ActivityRecord,
    WorkspaceStatus,
    ProjectStatus,
    AssetType,
    AssetStatus,
    RelationshipType,
    ActivityType,
)
from backend.app.engines.workspace.repository import WorkspaceRepository


@pytest.fixture
def temp_repo(tmp_path):
    storage_dir = str(tmp_path / "workspace_data")
    repo = WorkspaceRepository(storage_dir=storage_dir)
    return repo


def test_workspace_crud(temp_repo):
    ws = Workspace(
        workspace_id="ws_001",
        name="Main Workspace",
        slug="main-workspace",
        status=WorkspaceStatus.ACTIVE,
    )
    temp_repo.save_workspace(ws)

    fetched = temp_repo.get_workspace("ws_001")
    assert fetched is not None
    assert fetched.name == "Main Workspace"

    by_slug = temp_repo.get_workspace_by_slug("main-workspace")
    assert by_slug is not None
    assert by_slug.workspace_id == "ws_001"

    all_ws = temp_repo.list_workspaces()
    assert len(all_ws) == 1


def test_project_crud(temp_repo):
    proj = Project(
        project_id="proj_001",
        workspace_id="ws_001",
        name="Project Alpha",
        slug="project-alpha",
        status=ProjectStatus.ACTIVE,
    )
    temp_repo.save_project(proj)

    fetched = temp_repo.get_project("proj_001")
    assert fetched is not None
    assert fetched.name == "Project Alpha"

    by_slug = temp_repo.get_project_by_slug("ws_001", "project-alpha")
    assert by_slug is not None
    assert by_slug.project_id == "proj_001"

    projects = temp_repo.list_projects(workspace_id="ws_001")
    assert len(projects) == 1

    temp_repo.delete_project("proj_001")
    assert temp_repo.get_project("proj_001") is None


def test_asset_crud_and_relationships(temp_repo):
    asset_ds = Asset(
        asset_id="ast_ds",
        asset_type=AssetType.DATASET,
        project_id="proj_001",
        workspace_id="ws_001",
        source_entity_id="ds_123",
        name="Sales Data",
    )
    asset_dash = Asset(
        asset_id="ast_dash",
        asset_type=AssetType.DASHBOARD,
        project_id="proj_001",
        workspace_id="ws_001",
        source_entity_id="dash_456",
        name="Sales Dashboard",
    )
    temp_repo.save_asset(asset_ds)
    temp_repo.save_asset(asset_dash)

    # Relationship: dataset VISUALIZES dashboard
    rel = AssetRelationship(
        relationship_id="rel_001",
        source_asset_id="ast_ds",
        target_asset_id="ast_dash",
        relationship_type=RelationshipType.VISUALIZES,
    )
    temp_repo.save_relationship(rel)

    downstream = temp_repo.list_relationships(source_asset_id="ast_ds")
    assert len(downstream) == 1
    assert downstream[0].target_asset_id == "ast_dash"

    upstream = temp_repo.list_relationships(target_asset_id="ast_dash")
    assert len(upstream) == 1
    assert upstream[0].source_asset_id == "ast_ds"


def test_activity_recording(temp_repo):
    act = ActivityRecord(
        workspace_id="ws_001",
        project_id="proj_001",
        asset_id="ast_ds",
        activity_type=ActivityType.ASSET_CREATED,
        metadata={"action": "test"},
    )
    temp_repo.record_activity(act)

    acts = temp_repo.list_activity(project_id="proj_001")
    assert len(acts) == 1
    assert acts[0].activity_type == ActivityType.ASSET_CREATED
