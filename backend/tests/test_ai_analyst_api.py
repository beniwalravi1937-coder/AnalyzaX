"""
REST API Endpoint Tests for AI Analyst (Phase 13)
Verifies /api/v1/ai-analyst/chat, /plan, /sessions, and /tools.
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_list_tools_endpoint():
    response = client.get("/api/v1/ai-analyst/tools")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 16


def test_session_lifecycle_endpoints():
    # 1. Create session
    create_resp = client.post(
        "/api/v1/ai-analyst/sessions",
        json={"title": "Test Chat Session"},
    )
    assert create_resp.status_code == 200
    sess = create_resp.json()
    sess_id = sess["session_id"]
    assert sess_id.startswith("sess_")

    # 2. List sessions
    list_resp = client.get("/api/v1/ai-analyst/sessions")
    assert list_resp.status_code == 200
    sessions = list_resp.json()
    assert any(s["session_id"] == sess_id for s in sessions)

    # 3. Get session
    get_resp = client.get(f"/api/v1/ai-analyst/sessions/{sess_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Test Chat Session"

    # 4. Get messages
    msgs_resp = client.get(f"/api/v1/ai-analyst/sessions/{sess_id}/messages")
    assert msgs_resp.status_code == 200
    assert isinstance(msgs_resp.json(), list)

    # 5. Delete session
    del_resp = client.delete(f"/api/v1/ai-analyst/sessions/{sess_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "deleted"


def test_chat_endpoint():
    resp = client.post(
        "/api/v1/ai-analyst/chat",
        json={"message": "What columns and statistics are in this dataset?"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert data["status"] == "completed"
    assert "message" in data
    assert len(data["follow_up_questions"]) > 0
