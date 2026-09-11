import httpx

def test_live_servers():
    print("Testing Backend health & endpoints...")
    client = httpx.Client(base_url="http://127.0.0.1:8000", follow_redirects=True, timeout=30.0)
    fe_client = httpx.Client(base_url="http://localhost:3000", follow_redirects=True, timeout=30.0)

    # 1. Backend docs / OpenAPI
    r_docs = client.get("/docs")
    assert r_docs.status_code == 200, f"Backend docs failed: {r_docs.status_code}"
    print("[PASS] Backend /docs accessible")

    # 2. Login via backend API with bad password
    r_bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@analyzax.local", "password": "WrongPassword999!"}
    )
    assert r_bad_login.status_code == 401, f"Expected 401, got {r_bad_login.status_code}"
    print("[PASS] Backend login rejects bad password with 401")

    # 3. Login via backend API with valid admin credentials
    r_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@analyzax.local", "password": "AdminPassword123!"}
    )
    assert r_login.status_code == 200, f"Backend login failed: {r_login.status_code}: {r_login.text}"
    login_data = r_login.json()
    token = login_data["token"]
    user = login_data["user"]
    assert user["email"] == "admin@analyzax.local"
    assert "analyzax_session" in r_login.cookies, "analyzax_session cookie missing"
    print(f"[PASS] Backend login succeeded. User: {user['display_name']} ({user['user_id']}), Cookie set: {r_login.cookies.get('analyzax_session')[:10]}...")

    # 4. Auth /me check with cookie
    r_me = client.get("/api/v1/auth/me")
    assert r_me.status_code == 200, f"Backend /me failed: {r_me.status_code}"
    me_data = r_me.json()
    assert me_data["user"]["email"] == "admin@analyzax.local"
    assert len(me_data["workspace_memberships"]) >= 1
    assert me_data["workspace_memberships"][0]["role"] == "OWNER"
    print(f"[PASS] Backend /me verified role OWNER on {me_data['workspace_memberships'][0]['workspace_id']}")

    # 5. Check sessions list
    r_sessions = client.get("/api/v1/auth/sessions")
    assert r_sessions.status_code == 200, f"Backend /sessions failed: {r_sessions.status_code}"
    sessions_list = r_sessions.json()
    assert len(sessions_list) >= 1
    assert any(s["is_current"] for s in sessions_list)
    print(f"[PASS] Backend /sessions verified ({len(sessions_list)} active session(s), current marked)")

    # 6. Check workspace members and audit logs
    ws_id = me_data["workspace_memberships"][0]["workspace_id"]
    r_members = client.get(f"/api/v1/workspaces/{ws_id}/members")
    assert r_members.status_code == 200, f"Backend /members failed: {r_members.status_code}"
    members_list = r_members.json()
    assert any(m["email"] == "admin@analyzax.local" and m["role"] == "OWNER" for m in members_list)
    print(f"[PASS] Backend /members verified ({len(members_list)} member(s))")

    r_audit = client.get(f"/api/v1/workspaces/{ws_id}/audit-logs")
    assert r_audit.status_code == 200, f"Backend /audit-logs failed: {r_audit.status_code}"
    audit_logs = r_audit.json()
    print(f"[PASS] Backend /audit-logs verified ({len(audit_logs)} event(s))")

    # 7. Test Next.js Frontend pages
    print("\nTesting Next.js Frontend pages...")
    frontend_pages = [
        ("Login Page", "/login"),
        ("Register Page", "/register"),
        ("Forgot Password Page", "/forgot-password"),
        ("Reset Password Page", "/reset-password"),
        ("Profile Settings Page", "/settings/profile"),
        ("Security Settings Page", "/settings/security"),
        ("Members Settings Page", "/settings/members"),
        ("Settings Index", "/settings"),
    ]

    for name, url in frontend_pages:
        r_fe = fe_client.get(url)
        assert r_fe.status_code == 200, f"Frontend {name} at {url} returned {r_fe.status_code}"
        assert len(r_fe.text) > 500, f"Frontend {name} returned unexpectedly short response"
        print(f"[PASS] Frontend {name} rendered (Status: {r_fe.status_code}, Length: {len(r_fe.text)} bytes)")

    print("\nALL LIVE BACKEND & FRONTEND SERVER CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_live_servers()
