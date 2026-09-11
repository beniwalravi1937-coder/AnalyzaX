"""
Integration tests for Phase 17 Authentication Endpoints (/api/v1/auth/*).
"""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app


@pytest.mark.anyio
async def test_auth_api_full_workflow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register new user
        import uuid
        unique_email = f"test_api_user_{uuid.uuid4().hex[:6]}@analyzax.local"
        reg_payload = {
            "email": unique_email,
            "password": "ValidPassword123!",
            "display_name": "API Tester",
        }
        res = await client.post("/api/v1/auth/register", json=reg_payload)
        assert res.status_code == 201
        data = res.json()
        assert data["user"]["email"] == reg_payload["email"]
        assert "token" in data
        token = data["token"]

        headers = {"Authorization": f"Bearer {token}"}

        # 2. Inspect /me with Bearer header
        me_res = await client.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["user"]["email"] == reg_payload["email"]
        assert len(me_data["workspace_memberships"]) >= 1

        # 3. Invalid credentials fail
        bad_login = await client.post(
            "/api/v1/auth/login",
            json={"email": reg_payload["email"], "password": "WrongPassword!"},
        )
        assert bad_login.status_code == 401
        assert "password" not in bad_login.text.lower() or "invalid" in bad_login.text.lower()

        # 4. List sessions
        sess_res = await client.get("/api/v1/auth/sessions", headers=headers)
        assert sess_res.status_code == 200
        sessions = sess_res.json()
        assert len(sessions) >= 1
        assert "token_hash" not in sessions[0]

        # 5. Password Reset Flow
        reset_req = await client.post(
            "/api/v1/auth/password/reset/request",
            json={"email": reg_payload["email"]},
        )
        assert reset_req.status_code == 200
        reset_data = reset_req.json()
        dev_token = reset_data.get("dev_reset_token")

        if dev_token:
            # Confirm reset
            confirm_res = await client.post(
                "/api/v1/auth/password/reset/confirm",
                json={"token": dev_token, "new_password": "NewResetPassword123!"},
            )
            assert confirm_res.status_code == 200

            # Reusing reset token must FAIL
            reuse_res = await client.post(
                "/api/v1/auth/password/reset/confirm",
                json={"token": dev_token, "new_password": "AnotherPassword123!"},
            )
            assert reuse_res.status_code == 400

            # Login with new password
            new_login = await client.post(
                "/api/v1/auth/login",
                json={"email": reg_payload["email"], "password": "NewResetPassword123!"},
            )
            assert new_login.status_code == 200
            token = new_login.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}

        # 6. Logout
        logout_res = await client.post("/api/v1/auth/logout", headers=headers)
        assert logout_res.status_code == 200

        # Subsequent /me with logged out token must FAIL
        me_after = await client.get("/api/v1/auth/me", headers=headers)
        assert me_after.status_code == 401
