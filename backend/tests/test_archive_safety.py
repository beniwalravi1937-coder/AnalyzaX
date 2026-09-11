import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_mandatory_archive_safety(client):
    """
    Mandatory Golden Archive Safety Test (WORKSPACE-12, WORKSPACE-13, WORKSPACE-14, WORKSPACE-32, WORKSPACE-54, WORKSPACE-57):
    Archive a dataset with dependent assets.
    Verify:
    1. Dataset becomes ARCHIVED.
    2. Dependents remain intact and accessible.
    3. Lineage remains intact.
    4. Restore returns dataset to ACTIVE with identical ID.
    5. No data loss occurs.
    """
    # 1. Create Workspace and Project
    ws_res = client.post("/api/v1/workspaces", json={"name": "Archive Safety WS"})
    ws_id = ws_res.json()["workspace_id"]
    p_res = client.post(f"/api/v1/workspaces/{ws_id}/projects", json={"name": "Archive Safety Project"})
    proj_id = p_res.json()["project_id"]

    # 2. Register Dataset Asset
    ds_res = client.post(
        "/api/v1/assets",
        json={
            "asset_type": "DATASET",
            "project_id": proj_id,
            "workspace_id": ws_id,
            "source_entity_id": "ds_archive_test",
            "name": "Production Customer Records",
        },
    )
    ds_asset_id = ds_res.json()["asset_id"]

    # 3. Register Dependent Dashboard Asset
    dash_res = client.post(
        "/api/v1/assets",
        json={
            "asset_type": "DASHBOARD",
            "project_id": proj_id,
            "workspace_id": ws_id,
            "source_entity_id": "dash_archive_test",
            "name": "Customer Retention Executive Board",
        },
    )
    dash_asset_id = dash_res.json()["asset_id"]

    # Create link
    client.post(
        "/api/v1/assets/relationships",
        json={
            "source_asset_id": ds_asset_id,
            "target_asset_id": dash_asset_id,
            "relationship_type": "VISUALIZES",
        },
    )

    # 4. ARCHIVE DATASET ASSET
    arch_res = client.post(f"/api/v1/assets/{ds_asset_id}/archive")
    assert arch_res.status_code == 200
    arch_data = arch_res.json()
    assert arch_data["status"] == "ARCHIVED"
    assert arch_data["archived_at"] is not None

    # 5. VERIFY DEPENDENTS REMAIN INTACT
    dash_check = client.get(f"/api/v1/assets/{dash_asset_id}")
    assert dash_check.status_code == 200
    assert dash_check.json()["status"] == "ACTIVE"

    # 6. VERIFY LINEAGE REMAINS INTACT
    lineage_check = client.get(f"/api/v1/assets/{ds_asset_id}/lineage")
    assert lineage_check.status_code == 200
    nodes = [n["id"] for n in lineage_check.json()["nodes"]]
    assert ds_asset_id in nodes
    assert dash_asset_id in nodes

    # 7. RESTORE DATASET ASSET
    rest_res = client.post(f"/api/v1/assets/{ds_asset_id}/restore")
    assert rest_res.status_code == 200
    rest_data = rest_res.json()
    assert rest_data["status"] == "ACTIVE"
    assert rest_data["archived_at"] is None
    assert rest_data["asset_id"] == ds_asset_id  # IDENTITY MUST REMAIN EXACTLY UNCHANGED
