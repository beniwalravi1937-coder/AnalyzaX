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
    slugify,
)


def test_slugify_normalization():
    assert slugify("My Cool Project!") == "my-cool-project"
    assert slugify("   Special #$% Characters   ") == "special-characters"
    assert slugify("") == "item"


def test_workspace_model_creation():
    ws = Workspace(
        workspace_id="ws_test123",
        name="Test Workspace",
        slug="test-workspace",
        status=WorkspaceStatus.ACTIVE,
    )
    assert ws.workspace_id == "ws_test123"
    assert ws.status == WorkspaceStatus.ACTIVE
    assert ws.configuration_version == 1
    assert ws.archived_at is None


def test_project_model_creation():
    proj = Project(
        project_id="proj_test456",
        workspace_id="ws_test123",
        name="Marketing Analytics",
        slug="marketing-analytics",
        status=ProjectStatus.ACTIVE,
    )
    assert proj.project_id == "proj_test456"
    assert proj.workspace_id == "ws_test123"
    assert proj.status == ProjectStatus.ACTIVE


def test_asset_tag_normalization():
    asset = Asset(
        asset_id="ast_test789",
        asset_type=AssetType.DATASET,
        project_id="proj_test456",
        workspace_id="ws_test123",
        source_entity_id="ds_abc123",
        name="Revenue Dataset",
        tags=["  REVENUE  ", "Q3-Sales!!", "revenue", "important"],
    )
    # Checks lowercasing, stripping special chars, deduplication
    assert "revenue" in asset.tags
    assert "q3-sales" in asset.tags
    assert "important" in asset.tags
    assert len(asset.tags) == 3


def test_asset_relationship_model():
    rel = AssetRelationship(
        relationship_id="rel_test1",
        source_asset_id="ast_ds1",
        target_asset_id="ast_dash1",
        relationship_type=RelationshipType.VISUALIZES,
    )
    assert rel.relationship_type == RelationshipType.VISUALIZES
    assert rel.source_asset_id == "ast_ds1"
    assert rel.target_asset_id == "ast_dash1"
