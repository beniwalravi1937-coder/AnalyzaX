"""
API integration tests for Phase 14 Dashboard REST Router (/api/v1/dashboards).
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_dashboard_api_full_lifecycle():
    """Test creating, getting, updating, duplicating, and deleting a dashboard via REST API."""
    # 1. Create Dashboard
    create_payload = {
        "name": "E2E Test Dashboard",
        "description": "Integration testing dashboard",
        "dataset_id": "ds_test_api",
        "dataset_version_id": "v1",
        "template_id": "executive_overview",
    }
    resp = client.post("/api/v1/dashboards", json=create_payload)
    assert resp.status_code == 201
    data = resp.json()
    dashboard_id = data["dashboard_id"]
    assert data["name"] == "E2E Test Dashboard"
    assert data["version"] == 1
    assert len(data["components"]) > 0  # Template components added

    # 2. Get Dashboard
    resp = client.get(f"/api/v1/dashboards/{dashboard_id}")
    assert resp.status_code == 200
    assert resp.json()["dashboard_id"] == dashboard_id

    # 3. Add Component
    comp_payload = {
        "type": "TEXT",
        "title": "Analyst Comments",
        "configuration": {"content": "#### Performance Highlights\nRevenue increased by 12% YoY."},
        "source": {
            "source_type": "MANUAL",
            "dataset_id": "ds_test_api",
            "dataset_version_id": "v1",
            "engine": "core",
        },
    }
    resp = client.post(f"/api/v1/dashboards/{dashboard_id}/components", json=comp_payload)
    assert resp.status_code == 201
    comp_data = resp.json()
    comp_id = comp_data["component_id"]

    # 4. Duplicate Component
    resp = client.post(f"/api/v1/dashboards/{dashboard_id}/components/{comp_id}/duplicate")
    assert resp.status_code == 201
    dup_comp = resp.json()
    assert dup_comp["component_id"] != comp_id
    assert "(Copy)" in dup_comp["title"]

    # 5. Concurrency Conflict Detection (409)
    # Trying to update with mismatched expected_version (e.g., expected 1 when it's now higher)
    resp = client.put(
        f"/api/v1/dashboards/{dashboard_id}",
        json={"name": "Conflicting Update", "expected_version": 1},
    )
    assert resp.status_code == 409

    # 6. Duplicate Dashboard
    resp = client.post(
        f"/api/v1/dashboards/{dashboard_id}/duplicate",
        json={"new_name": "Cloned Dashboard"},
    )
    assert resp.status_code == 201
    cloned_id = resp.json()["dashboard_id"]
    assert cloned_id != dashboard_id
    assert resp.json()["name"] == "Cloned Dashboard"

    # 7. Check Version History
    resp = client.get(f"/api/v1/dashboards/{dashboard_id}/versions")
    assert resp.status_code == 200
    versions = resp.json()
    assert len(versions) >= 2

    # 8. Restore Version 1
    resp = client.post(f"/api/v1/dashboards/{dashboard_id}/versions/1/restore")
    assert resp.status_code == 200
    restored = resp.json()
    assert restored["version"] > len(versions)  # New version created

    # 9. Delete Dashboard
    resp = client.delete(f"/api/v1/dashboards/{dashboard_id}")
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True

    # 10. Confirm 404 after deletion
    resp = client.get(f"/api/v1/dashboards/{dashboard_id}")
    assert resp.status_code == 404
