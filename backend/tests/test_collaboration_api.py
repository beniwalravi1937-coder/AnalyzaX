"""
End-to-End REST API Integration Tests for Phase 18 Collaboration Routers.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.engines.auth.models import RoleName
from backend.app.engines.collaboration.models import (
    ResourceType,
    ShareLinkMode,
    SharePermission,
    ShareRecipientType,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_collaboration_api_e2e(client):
    import uuid
    test_email = f"collab_analyst_{uuid.uuid4().hex[:6]}@analyzax.local"

    # 1. Login as admin
    r_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@analyzax.local", "password": "AdminPassword123!"},
    )
    assert r_login.status_code == 200
    token = r_login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Workspace Invitation
    r_inv = client.post(
        "/api/v1/workspaces/ws_default/invitations",
        headers=headers,
        json={
            "email": test_email,
            "intended_role": "ANALYST",
            "expires_in_days": 7,
        },
    )
    assert r_inv.status_code == 201
    inv_data = r_inv.json()
    assert inv_data["email"] == test_email
    assert inv_data["intended_role"] == "ANALYST"
    preview_token = inv_data["preview_token"]
    assert preview_token is not None

    # 3. Verify Invitation Token
    r_verify = client.get(f"/api/v1/invitations/verify/{preview_token}")
    assert r_verify.status_code == 200
    verify_data = r_verify.json()
    assert verify_data["email"] == test_email
    assert verify_data["is_expired"] is False

    # 4. Register new user for the invitee
    r_reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": test_email,
            "password": "Password12345!",
            "display_name": "Collab Analyst",
        },
    )
    assert r_reg.status_code == 201
    invitee_token = r_reg.json()["token"]
    invitee_headers = {"Authorization": f"Bearer {invitee_token}"}

    # 5. Accept Invitation
    r_accept = client.post(
        f"/api/v1/invitations/{inv_data['invitation_id']}/accept",
        headers=invitee_headers,
        json={"token": preview_token},
    )
    assert r_accept.status_code == 200
    assert r_accept.json()["role"] == "ANALYST"

    # 6. Add to Project
    r_pm = client.post(
        "/api/v1/projects/proj_default/members",
        headers=headers,
        json={
            "user_id": r_reg.json()["user"]["user_id"],
            "role": "ANALYST",
        },
    )
    assert r_pm.status_code == 201

    # 7. Create Dashboard Asset and Share Link
    from backend.app.engines.workspace.repository import workspace_repo
    from backend.app.engines.workspace.models import Asset, AssetType
    test_dash = Asset(
        asset_id="dash_api_test",
        source_entity_id="dash_api_test",
        project_id="proj_default",
        workspace_id="ws_default",
        asset_type=AssetType.DASHBOARD,
        name="API Test Dashboard",
        created_by="usr_admin",
    )
    workspace_repo.save_asset(test_dash)

    r_link = client.post(
        "/api/v1/resources/DASHBOARD/dash_api_test/share-links",
        headers=headers,
        json={
            "resource_type": "DASHBOARD",
            "resource_id": "dash_api_test",
            "link_mode": "PUBLIC_READ_ONLY",
            "permission": "VIEW",
        },
    )
    assert r_link.status_code == 201
    link_data = r_link.json()
    assert link_data["share_url"] is not None
    link_token = link_data["share_url"].split("/")[-1]

    # 8. Resolve Shared View via Public Link (no auth header)
    r_shared = client.get(f"/api/v1/shared/{link_token}")
    assert r_shared.status_code == 200
    shared_data = r_shared.json()
    assert shared_data["is_public"] is True
    assert shared_data["permission"] == "VIEW"

    # 9. List Notifications for invitee
    r_notifs = client.get("/api/v1/notifications", headers=invitee_headers)
    assert r_notifs.status_code == 200
    notifs = r_notifs.json()
    assert len(notifs) >= 1

    # 10. Mark all read
    r_read_all = client.post("/api/v1/notifications/read-all", headers=invitee_headers)
    assert r_read_all.status_code == 200
