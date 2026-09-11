"""
End-to-End REST API Integration Tests for Phase 19 Notifications & Activity Routers.
Tests HTTP transport, Bearer authentication scoping, preference enforcement,
unread count, mark-as-read, read-all, archive, and activity feed access control.
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.engines.notifications.models import (
    ApplicationEventType,
    NotificationCategory,
    NotificationChannel,
)
from backend.app.main import app
from backend.app.services.notifications.event_dispatcher import event_dispatcher


@pytest.fixture
def client():
    return TestClient(app)


def test_notifications_api_end_to_end(client: TestClient):
    # 1. Login as admin
    r_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@analyzax.local", "password": "AdminPassword123!"},
    )
    assert r_login.status_code == 200
    admin_data = r_login.json()
    admin_token = admin_data["token"]
    admin_user_id = admin_data["user"]["user_id"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Register a second user (Bob)
    bob_email = f"bob_notify_{uuid.uuid4().hex[:6]}@analyzax.local"
    r_bob_reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": bob_email,
            "password": "BobPassword123!",
            "display_name": "Bob Notification User",
        },
    )
    assert r_bob_reg.status_code in (200, 201)
    bob_data = r_bob_reg.json()
    bob_token = bob_data["token"]
    bob_user_id = bob_data["user"]["user_id"]
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    # 3. Initially Bob should have 0 unread notifications
    r_unread = client.get("/api/v1/notifications/unread-count", headers=bob_headers)
    assert r_unread.status_code == 200
    assert r_unread.json()["unread_count"] == 0

    # 4. Dispatch a real event targeting Bob
    test_event = event_dispatcher.create_and_dispatch(
        event_type=ApplicationEventType.RESOURCE_SHARED,
        actor_user_id=admin_user_id,
        workspace_id="ws_default",
        resource_type="DASHBOARD",
        resource_id="dash_revenue_kpi",
        metadata={
            "recipient_user_id": bob_user_id,
            "resource_name": "Revenue KPI Dashboard",
            "permission": "view",
        },
    )
    assert test_event.event_id is not None

    # 5. Check Bob's unread count -> should now be 1
    r_unread2 = client.get("/api/v1/notifications/unread-count", headers=bob_headers)
    assert r_unread2.status_code == 200
    assert r_unread2.json()["unread_count"] == 1

    # 6. List Bob's notifications
    r_list = client.get("/api/v1/notifications", headers=bob_headers)
    assert r_list.status_code == 200
    list_data = r_list.json()
    assert list_data["total_count"] >= 1
    found_item = next(item for item in list_data["items"] if item["resource_id"] == "dash_revenue_kpi")
    notif_id = found_item["notification_id"]
    assert found_item["status"] == "UNREAD"
    assert found_item["deep_link"] == "/dashboard/dash_revenue_kpi"

    # 7. Mark as Read
    r_read = client.post(f"/api/v1/notifications/{notif_id}/read", headers=bob_headers)
    assert r_read.status_code == 200
    assert r_read.json()["status"] == "READ"
    assert r_read.json()["read_at"] is not None

    # Verify unread count is now 0
    r_unread3 = client.get("/api/v1/notifications/unread-count", headers=bob_headers)
    assert r_unread3.json()["unread_count"] == 0

    # 8. Mark as Unread
    r_revert = client.post(f"/api/v1/notifications/{notif_id}/unread", headers=bob_headers)
    assert r_revert.status_code == 200
    assert r_revert.json()["status"] == "UNREAD"

    # 9. Mark All Read
    r_read_all = client.post("/api/v1/notifications/read-all", headers=bob_headers)
    assert r_read_all.status_code == 200
    assert r_read_all.json()["count"] >= 1

    # 10. Archive notification
    r_archive = client.post(f"/api/v1/notifications/{notif_id}/archive", headers=bob_headers)
    assert r_archive.status_code == 200
    assert r_archive.json()["status"] == "ARCHIVED"

    # 11. Cross-User Security (Admin cannot access Bob's notification)
    r_idor = client.get(f"/api/v1/notifications/{notif_id}", headers=admin_headers)
    assert r_idor.status_code == 404

    # 12. Notification Preferences
    r_prefs = client.get("/api/v1/notification-preferences", headers=bob_headers)
    assert r_prefs.status_code == 200
    prefs_list = r_prefs.json()
    assert len(prefs_list) > 0

    # Update preference: disable EXPORT
    r_update_pref = client.patch(
        "/api/v1/notification-preferences",
        headers=bob_headers,
        json={
            "category": "EXPORT",
            "channel": "IN_APP",
            "enabled": False,
        },
    )
    assert r_update_pref.status_code == 200
    assert r_update_pref.json()["enabled"] is False

    # Attempt to disable SECURITY -> MUST fail with 400 Bad Request
    r_bad_pref = client.patch(
        "/api/v1/notification-preferences",
        headers=bob_headers,
        json={
            "category": "SECURITY",
            "channel": "IN_APP",
            "enabled": False,
        },
    )
    assert r_bad_pref.status_code == 400

    # 13. Workspace Activity Feed (Admin has access to default workspace)
    r_activity = client.get(
        "/api/v1/workspaces/ws_default/activity",
        headers=admin_headers,
    )
    assert r_activity.status_code == 200
    act_data = r_activity.json()
    assert "items" in act_data
    assert "total" in act_data
