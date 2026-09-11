import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_mandatory_search_golden(client):
    """
    Mandatory Golden Search Test (WORKSPACE-18, WORKSPACE-19, WORKSPACE-20, WORKSPACE-45, WORKSPACE-56, WORKSPACE-59):
    Search: 'revenue'
    Verify matching across datasets, dashboards, queries, and reports with real navigable URLs.
    """
    # 1. Setup Workspace and Project
    ws_res = client.post("/api/v1/workspaces", json={"name": "Search Golden WS"})
    ws_id = ws_res.json()["workspace_id"]
    p_res = client.post(f"/api/v1/workspaces/{ws_id}/projects", json={"name": "Search Project"})
    proj_id = p_res.json()["project_id"]

    # 2. Register diverse assets containing 'revenue'
    assets_to_create = [
        {"asset_type": "DATASET", "name": "Annual Revenue Data", "source_entity_id": "ds_rev_1"},
        {"asset_type": "DASHBOARD", "name": "Revenue Overview Dashboard", "source_entity_id": "dash_rev_1"},
        {"asset_type": "REPORT", "name": "Q3 Revenue Performance Report", "source_entity_id": "rep_rev_1"},
        {"asset_type": "QUERY", "name": "Monthly Revenue Aggregation SQL", "source_entity_id": "q_rev_1"},
    ]

    for a in assets_to_create:
        client.post(
            "/api/v1/assets",
            json={
                "asset_type": a["asset_type"],
                "project_id": proj_id,
                "workspace_id": ws_id,
                "source_entity_id": a["source_entity_id"],
                "name": a["name"],
                "tags": ["revenue", "finance"],
            },
        )

    # 3. Perform Global Search for 'revenue'
    search_res = client.get("/api/v1/search?q=revenue")
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total"] >= 4

    matched_types = {r["asset_type"] for r in search_data["results"]}
    assert "DATASET" in matched_types
    assert "DASHBOARD" in matched_types
    assert "REPORT" in matched_types
    assert "QUERY" in matched_types

    # 4. Verify all results have real navigation URLs
    for r in search_data["results"]:
        assert "navigation_url" in r
        assert r["navigation_url"].startswith("/")

    # 5. Verify Filter by Asset Type works
    dash_filter_res = client.get("/api/v1/search?q=revenue&asset_type=DASHBOARD")
    assert dash_filter_res.status_code == 200
    for r in dash_filter_res.json()["results"]:
        assert r["asset_type"] == "DASHBOARD"

    # 6. Verify Sorting Security (arbitrary sort field ignored or rejected safely)
    safe_sort = client.get("/api/v1/search?q=revenue&sort_by=name&sort_desc=true")
    assert safe_sort.status_code == 200
