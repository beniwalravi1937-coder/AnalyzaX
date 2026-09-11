"""
Unit tests for Phase 17 Session Lifecycle & Rate Limiting.
"""

from datetime import datetime, timedelta, timezone
import time
import pytest

from backend.app.engines.auth.crypto import generate_secure_token, hash_token
from backend.app.engines.auth.models import Session, User, UserStatus
from backend.app.engines.auth.rate_limiter import LoginRateLimiter
from backend.app.engines.auth.repository import AuthRepository
from backend.app.services.auth.auth_service import AuthService


def test_session_lifecycle(tmp_path):
    repo = AuthRepository(storage_dir=str(tmp_path))
    auth_srv = AuthService(repository=repo)

    # Setup test user
    user = User(
        user_id="usr_session_test",
        email="sess@example.com",
        email_normalized="sess@example.com",
        password_hash="dummy",
        display_name="Session Test",
        status=UserStatus.ACTIVE,
    )
    repo.save_user(user)

    # 1. Create session
    raw_token, session = auth_srv._create_session(user.user_id)
    assert session.session_id.startswith("sess_")
    assert session.revoked_at is None

    # 2. Validate session from token
    resolved = auth_srv.get_current_user_from_token(raw_token)
    assert resolved is not None
    resolved_user, resolved_sess = resolved
    assert resolved_user.user_id == user.user_id
    assert resolved_sess.session_id == session.session_id

    # 3. List sessions
    active_sessions = auth_srv.list_sessions(user.user_id, current_session_id=session.session_id)
    assert len(active_sessions) == 1
    assert active_sessions[0].is_current is True

    # 4. Revoke session
    revoked = auth_srv.revoke_session(session.session_id, user.user_id)
    assert revoked is True
    # Once revoked, token resolution must fail
    assert auth_srv.get_current_user_from_token(raw_token) is None


def test_expired_session_fails(tmp_path):
    repo = AuthRepository(storage_dir=str(tmp_path))
    auth_srv = AuthService(repository=repo)

    user = User(
        user_id="usr_exp_test",
        email="exp@example.com",
        email_normalized="exp@example.com",
        password_hash="dummy",
        display_name="Exp User",
        status=UserStatus.ACTIVE,
    )
    repo.save_user(user)

    raw_token = generate_secure_token(32)
    t_hash = hash_token(raw_token)
    # Expired 1 hour ago
    expired_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    session = Session(
        user_id=user.user_id,
        token_hash=t_hash,
        expires_at=expired_at,
    )
    repo.save_session(session)

    assert auth_srv.get_current_user_from_token(raw_token) is None


def test_login_rate_limiter():
    limiter = LoginRateLimiter(max_attempts=3, window_seconds=10, lockout_seconds=5)
    key = "test@domain.com:127.0.0.1"

    assert limiter.is_locked(key)[0] is False

    limiter.record_failure(key)
    limiter.record_failure(key)
    assert limiter.is_locked(key)[0] is False

    # Third failure triggers lockout
    limiter.record_failure(key)
    is_locked, remaining = limiter.is_locked(key)
    assert is_locked is True
    assert remaining > 0

    # Successful login clears rate limiter
    limiter.record_success(key)
    assert limiter.is_locked(key)[0] is False
