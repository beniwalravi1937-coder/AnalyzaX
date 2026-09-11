import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_mandatory_lineage_traversal(client):
    """
    Mandatory Golden Lineage Test (WORKSPACE-10, WORKSPACE-48, WORKSPACE-53, WORKSPACE-56):
    Build DAG:
    Dataset Version -> Visualization -> Dashboard -> Report -> Export
    Verify upstream and downstream dependency traversal and graph construction.
    """
    # 1. Setup Workspace and Project
    ws_res = client.post("/api/v1/workspaces", json={"name": "Lineage Test WS"})
    ws_id = ws_res.json()["workspace_id"]
    p_res = client.post(f"/api/v1/workspaces/{ws_id}/projects", json={"name": "Lineage Project"})
    proj_id = p_res.json()["project_id"]

    # 2. Register Assets
    # Dataset Version
    res_v = client.post(
        "/api/v1/assets",
        json={
            "asset_type": "DATASET_VERSION",
            "project_id": proj_id,
            "workspace_id": ws_id,
            "source_entity_id": "ds_lineage:v1",
            "name": "Lineage Data (v1)",
        },
    )
    v_id = res_v.json()["asset_id"]

    # Visualization
    res_viz = client.post(
        "/api/v1/assets",
        json={
            "asset_type": "VISUALIZATION",
            "project_id": proj_id,
            "workspace_id": ws_id,
            "source_entity_id": "viz_101",
            "name": "Revenue Trend Chart",
        },
    )
    viz_id = res_viz.json()["asset_id"]

    # Dashboard
    res_dash = client.post(
        "/api/v1/assets",
        json={
            "asset_type": "DASHBOARD",
            "project_id": proj_id,
            "workspace_id": ws_id,
            "source_entity_id": "dash_202",
            "name": "Quarterly Operations Dashboard",
        },
    )
    dash_id = res_dash.json()["asset_id"]

    # Report
    res_rep = client.post(
        "/api/v1/assets",
        json={
            "asset_type": "REPORT",
            "project_id": proj_id,
            "workspace_id": ws_id,
            "source_entity_id": "rep_303",
            "name": "Executive Summary Report",
        },
    )
    rep_id = res_rep.json()["asset_id"]

    # Export
    res_exp = client.post(
        "/api/v1/assets",
        json={
            "asset_type": "EXPORT",
            "project_id": proj_id,
            "workspace_id": ws_id,
            "source_entity_id": "exp_404",
            "name": "Executive PDF Export",
        },
    )
    exp_id = res_exp.json()["asset_id"]

    # 3. Create Directed Relationships:
    # Dataset Version -> (VISUALIZES) -> Visualization
    client.post(
        "/api/v1/assets/relationships",
        json={"source_asset_id": v_id, "target_asset_id": viz_id, "relationship_type": "VISUALIZES"},
    )
    # Visualization -> (CONTAINS) -> Dashboard
    client.post(
        "/api/v1/assets/relationships",
        json={"source_asset_id": viz_id, "target_asset_id": dash_id, "relationship_type": "CONTAINS"},
    )
    # Dashboard -> (SUMMARIZES) -> Report
    client.post(
        "/api/v1/assets/relationships",
        json={"source_asset_id": dash_id, "target_asset_id": rep_id, "relationship_type": "SUMMARIZES"},
    )
    # Report -> (EXPORTED_FROM) -> Export
    client.post(
        "/api/v1/assets/relationships",
        json={"source_asset_id": rep_id, "target_asset_id": exp_id, "relationship_type": "EXPORTED_FROM"},
    )

    # 4. DOWNSTREAM TRAVERSAL from Dataset Version (v_id)
    lineage_down = client.get(f"/api/v1/assets/{v_id}/lineage")
    assert lineage_down.status_code == 200
    down_data = lineage_down.json()
    down_node_ids = [n["id"] for n in down_data["nodes"]]

    assert v_id in down_node_ids
    assert viz_id in down_node_ids
    assert dash_id in down_node_ids
    assert rep_id in down_node_ids
    assert exp_id in down_node_ids

    # 5. UPSTREAM TRAVERSAL from Export (exp_id)
    lineage_up = client.get(f"/api/v1/assets/{exp_id}/lineage")
    assert lineage_up.status_code == 200
    up_data = lineage_up.json()
    up_node_ids = [n["id"] for n in up_data["nodes"]]

    assert exp_id in up_node_ids
    assert rep_id in up_node_ids
    assert dash_id in up_node_ids
    assert viz_id in up_node_ids
    assert v_id in up_node_ids

    # 6. DEPENDENCY ANALYSIS: Attempting to delete Version must warn about downstream dependents
    dep_summary = client.get(f"/api/v1/assets/{v_id}/dependencies")
    assert dep_summary.status_code == 200
    dep_data = dep_summary.json()
    assert dep_data["can_safely_delete"] is False
    assert len(dep_data["downstream_dependencies"]) >= 4
    assert len(dep_data["warnings"]) > 0
