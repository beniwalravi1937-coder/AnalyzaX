"""
AnalyzaX — Phase 24 Tests: Multi-Factor Authentication (MFA), TOTP, Recovery Codes & Step-Up Auth.
"""

import time
import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.core.middleware.security import rate_limiter
from backend.app.engines.auth.mfa import TOTPEngine, RecoveryCodeEngine, MFAChallengeEngine
from backend.app.main import app


def test_mfa_engine_totp_and_recovery_codes():
    # 1. Secret generation
    secret = TOTPEngine.generate_secret()
    assert len(secret) == 32
    assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for c in secret)

    # 2. Current code generation & verification
    code = TOTPEngine.generate_totp(secret)
    assert len(code) == 6
    assert code.isdigit()
    assert TOTPEngine.verify_totp(secret, code) is True

    # 3. Invalid code rejection
    assert TOTPEngine.verify_totp(secret, "000000" if code != "000000" else "111111") is False

    # 4. Drift verification (+- 1 step / 30s window)
    now = int(time.time())
    past_code = TOTPEngine.generate_totp(secret, timestamp=now - 30)
    assert TOTPEngine.verify_totp(secret, past_code, timestamp=now) is True

    far_past_code = TOTPEngine.generate_totp(secret, timestamp=now - 90)
    assert TOTPEngine.verify_totp(secret, far_past_code, timestamp=now) is False

    # 5. Recovery codes hashing & single-use verification
    plain_codes, hashed_codes = RecoveryCodeEngine.generate_codes(count=5)
    assert len(plain_codes) == 5
    assert len(hashed_codes) == 5

    # Match first plain code
    matched, remaining = RecoveryCodeEngine.verify_and_consume(plain_codes[0], hashed_codes)
    assert matched is True
    assert len(remaining) == 4

    # Reusing consumed code fails against remaining
    matched_again, _ = RecoveryCodeEngine.verify_and_consume(plain_codes[0], remaining)
    assert matched_again is False

    # Unknown code fails
    matched_invalid, _ = RecoveryCodeEngine.verify_and_consume("INVALID-CODE-XXXX", remaining)
    assert matched_invalid is False


@pytest.mark.anyio
async def test_mfa_api_full_lifecycle_and_step_up():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register a fresh user
        email = f"mfa_test_{uuid.uuid4().hex[:8]}@analyzax.local"
        password = "SecurePassword123!"
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "display_name": "MFA Test User"},
        )
        assert reg_res.status_code == 201
        token = reg_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Verify MFA is initially disabled
        me_res = await client.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["user"]["mfa_enabled"] is False

        # 2. Initiate MFA Setup
        setup_res = await client.post("/api/v1/auth/mfa/setup", headers=headers)
        assert setup_res.status_code == 200
        setup_data = setup_res.json()
        assert "secret" in setup_data
        assert "provisioning_uri" in setup_data
        assert "recovery_codes" in setup_data
        secret = setup_data["secret"]
        recovery_codes = setup_data["recovery_codes"]
        assert len(recovery_codes) == 8

        # 3. Enable MFA using valid TOTP code
        valid_totp = TOTPEngine.generate_totp(secret)
        enable_res = await client.post(
            "/api/v1/auth/mfa/enable",
            headers=headers,
            json={"code": valid_totp},
        )
        assert enable_res.status_code == 200

        # User profile should now show mfa_enabled = True
        me_res2 = await client.get("/api/v1/auth/me", headers=headers)
        assert me_res2.json()["user"]["mfa_enabled"] is True

        # 4. Test Login with MFA Required
        rate_limiter._windows.clear()
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_res.status_code == 200
        login_data = login_res.json()
        assert login_data.get("mfa_required") is True
        assert "mfa_token" in login_data
        assert login_data.get("token") is None  # No session token issued yet!
        mfa_challenge = login_data["mfa_token"]

        # 5. Invalid MFA code fails login
        bad_verify = await client.post(
            "/api/v1/auth/mfa/verify",
            json={"mfa_token": mfa_challenge, "code": "000000"},
        )
        assert bad_verify.status_code == 401

        # 6. Valid TOTP code completes login
        current_code = TOTPEngine.generate_totp(secret)
        good_verify = await client.post(
            "/api/v1/auth/mfa/verify",
            json={"mfa_token": mfa_challenge, "code": current_code},
        )
        assert good_verify.status_code == 200
        verified_data = good_verify.json()
        assert "token" in verified_data
        new_token = verified_data["token"]
        new_headers = {"Authorization": f"Bearer {new_token}"}

        # 7. Single-use recovery code login
        rate_limiter._windows.clear()
        login_res2 = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        challenge_2 = login_res2.json()["mfa_token"]
        recovery_to_use = recovery_codes[0]

        rec_verify = await client.post(
            "/api/v1/auth/mfa/verify",
            json={"mfa_token": challenge_2, "code": recovery_to_use},
        )
        assert rec_verify.status_code == 200
        assert "token" in rec_verify.json()

        # Reusing the consumed recovery code must be rejected
        rate_limiter._windows.clear()
        login_res3 = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        challenge_3 = login_res3.json()["mfa_token"]
        reuse_verify = await client.post(
            "/api/v1/auth/mfa/verify",
            json={"mfa_token": challenge_3, "code": recovery_to_use},
        )
        assert reuse_verify.status_code == 401

        # 8. Step-Up Authentication
        rate_limiter._windows.clear()
        step_up_code = TOTPEngine.generate_totp(secret)
        step_up_res = await client.post(
            "/api/v1/auth/step-up",
            headers=new_headers,
            json={"code": step_up_code},
        )
        assert step_up_res.status_code == 200
        assert step_up_res.json()["success"] is True

        # 9. Disable MFA
        disable_code = TOTPEngine.generate_totp(secret)
        disable_res = await client.post(
            "/api/v1/auth/mfa/disable",
            headers=new_headers,
            json={"code": disable_code},
        )
        assert disable_res.status_code == 200

        # Login is now direct without MFA challenge
        rate_limiter._windows.clear()
        direct_login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert direct_login.status_code == 200
        assert direct_login.json().get("mfa_required") is False
        assert "token" in direct_login.json()
