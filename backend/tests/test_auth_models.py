"""
Unit tests for Phase 17 Auth Models & Email Normalization.
"""

import pytest
from backend.app.engines.auth.models import (
    MembershipStatus,
    PasswordResetToken,
    ProjectMember,
    RoleName,
    SafeSession,
    SafeUser,
    SecurityAuditEvent,
    SecurityEventType,
    Session,
    User,
    UserRegisterRequest,
    UserStatus,
    WorkspaceMember,
    normalize_email,
    validate_email_format,
)


def test_email_normalization():
    assert normalize_email("  User@Example.COM ") == "user@example.com"
    assert normalize_email("ALICE@DOMAIN.CO.UK") == "alice@domain.co.uk"
    assert normalize_email("") == ""


def test_email_validation():
    assert validate_email_format("test@example.com") == "test@example.com"
    with pytest.raises(ValueError):
        validate_email_format("invalid-email")
    with pytest.raises(ValueError):
        validate_email_format("@domain.com")


def test_user_model_defaults():
    user = User(
        email="analyst@domain.com",
        email_normalized="analyst@domain.com",
        password_hash="scrypt$dummy",
        display_name="Test Analyst",
    )
    assert user.user_id.startswith("usr_")
    assert user.status == UserStatus.ACTIVE
    assert user.created_at is not None
    assert user.last_login_at is None


def test_safe_user_omits_secrets():
    user = User(
        email="test@domain.com",
        email_normalized="test@domain.com",
        password_hash="scrypt$super_secret_hash",
        display_name="User",
    )
    safe = SafeUser(**user.model_dump())
    assert hasattr(safe, "password_hash") is False
    assert "password_hash" not in safe.model_dump()


def test_safe_session_omits_token_hash():
    session = Session(
        user_id="usr_123",
        token_hash="sha256_hash_value",
        expires_at="2026-10-01T00:00:00Z",
    )
    safe = SafeSession(
        session_id=session.session_id,
        created_at=session.created_at,
        expires_at=session.expires_at,
        last_seen_at=session.last_seen_at,
        is_current=True,
    )
    assert hasattr(safe, "token_hash") is False
    assert "token_hash" not in safe.model_dump()


def test_membership_models():
    wm = WorkspaceMember(
        workspace_id="ws_test",
        user_id="usr_test",
        role=RoleName.EDITOR,
    )
    assert wm.membership_id.startswith("wsm_")
    assert wm.role == RoleName.EDITOR
    assert wm.status == MembershipStatus.ACTIVE

    pm = ProjectMember(
        project_id="proj_test",
        user_id="usr_test",
        role=RoleName.VIEWER,
    )
    assert pm.membership_id.startswith("pjm_")
    assert pm.role == RoleName.VIEWER


def test_security_audit_event_creation():
    event = SecurityAuditEvent(
        user_id="usr_1",
        workspace_id="ws_1",
        event_type=SecurityEventType.LOGIN_SUCCESS,
        result="SUCCESS",
        metadata={"client": "web"},
    )
    assert event.event_id.startswith("sec_")
    assert event.event_type == SecurityEventType.LOGIN_SUCCESS
