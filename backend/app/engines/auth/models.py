"""
Domain models for Phase 17: Authentication, Authorization & Multi-User Collaboration Foundation.
Defines user identities, sessions, memberships, roles, permissions, security audit events,
and request/response contracts.
"""

from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DISABLED = "DISABLED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class RoleName(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"


class RoleScope(str, Enum):
    WORKSPACE = "WORKSPACE"
    PROJECT = "PROJECT"


class MembershipStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REMOVED = "REMOVED"


class MFAFactorStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class SecurityEventType(str, Enum):
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    LOGOUT = "LOGOUT"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    PASSWORD_RESET_REQUESTED = "PASSWORD_RESET_REQUESTED"
    PASSWORD_RESET_COMPLETED = "PASSWORD_RESET_COMPLETED"
    SESSION_CREATED = "SESSION_CREATED"
    SESSION_REVOKED = "SESSION_REVOKED"
    ACCOUNT_CREATED = "ACCOUNT_CREATED"
    ACCOUNT_SUSPENDED = "ACCOUNT_SUSPENDED"
    MEMBERSHIP_CREATED = "MEMBERSHIP_CREATED"
    MEMBERSHIP_ROLE_CHANGED = "MEMBERSHIP_ROLE_CHANGED"
    MEMBERSHIP_REMOVED = "MEMBERSHIP_REMOVED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    OWNERSHIP_TRANSFERRED = "OWNERSHIP_TRANSFERRED"
    MFA_SETUP_INITIATED = "MFA_SETUP_INITIATED"
    MFA_ENABLED = "MFA_ENABLED"
    MFA_DISABLED = "MFA_DISABLED"
    MFA_CHALLENGE_FAILED = "MFA_CHALLENGE_FAILED"
    MFA_RECOVERY_USED = "MFA_RECOVERY_USED"
    STEP_UP_VERIFIED = "STEP_UP_VERIFIED"
    DATA_EXPORTED = "DATA_EXPORTED"
    DATA_DELETED = "DATA_DELETED"
    WORKSPACE_DELETED = "WORKSPACE_DELETED"
    SSRF_BLOCKED = "SSRF_BLOCKED"
    INJECTION_BLOCKED = "INJECTION_BLOCKED"
    SECURITY_SETTING_CHANGED = "SECURITY_SETTING_CHANGED"



# ─────────────────────────────────────────────────────────────
# Utility Normalizers & Validators
# ─────────────────────────────────────────────────────────────

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(email: str) -> str:
    """Normalizes email address by trimming whitespace and lowercasing."""
    if not email:
        return ""
    return email.strip().lower()


def validate_email_format(email: str) -> str:
    """Validates basic email formatting."""
    email_clean = normalize_email(email)
    if not EMAIL_REGEX.match(email_clean):
        raise ValueError(f"Invalid email address: {email}")
    return email_clean


# ─────────────────────────────────────────────────────────────
# User Entities
# ─────────────────────────────────────────────────────────────

class User(BaseModel):
    user_id: str = Field(default_factory=lambda: f"usr_{uuid.uuid4().hex[:12]}")
    email: str
    email_normalized: str
    password_hash: str
    display_name: str
    status: UserStatus = UserStatus.ACTIVE
    mfa_enabled: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_login_at: Optional[str] = None
    email_verified_at: Optional[str] = None
    password_changed_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SafeUser(BaseModel):
    """Public representation of user identity with zero sensitive secrets."""
    user_id: str
    email: str
    display_name: str
    status: UserStatus
    mfa_enabled: bool = False
    created_at: str
    last_login_at: Optional[str] = None
    email_verified_at: Optional[str] = None


class MFAFactor(BaseModel):
    """MFA factor configuration for user identity."""
    factor_id: str = Field(default_factory=lambda: f"mfa_{uuid.uuid4().hex[:16]}")
    user_id: str
    type: str = "totp"
    secret: str  # Base32 secret key
    recovery_codes_hashes: List[str] = Field(default_factory=list)
    status: MFAFactorStatus = MFAFactorStatus.PENDING
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    verified_at: Optional[str] = None
    last_used_at: Optional[str] = None


# ─────────────────────────────────────────────────────────────
# Session Entities
# ─────────────────────────────────────────────────────────────

class Session(BaseModel):
    session_id: str = Field(default_factory=lambda: f"sess_{uuid.uuid4().hex[:16]}")
    user_id: str
    token_hash: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str
    last_seen_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    revoked_at: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class SafeSession(BaseModel):
    session_id: str
    created_at: str
    expires_at: str
    last_seen_at: str
    is_current: bool = False
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


# ─────────────────────────────────────────────────────────────
# Password Reset Entities
# ─────────────────────────────────────────────────────────────

class PasswordResetToken(BaseModel):
    token_id: str = Field(default_factory=lambda: f"prt_{uuid.uuid4().hex[:16]}")
    token_hash: str
    user_id: str
    expires_at: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    used_at: Optional[str] = None


# ─────────────────────────────────────────────────────────────
# Memberships & Roles
# ─────────────────────────────────────────────────────────────

class WorkspaceMember(BaseModel):
    membership_id: str = Field(default_factory=lambda: f"wsm_{uuid.uuid4().hex[:12]}")
    workspace_id: str
    user_id: str
    role: RoleName = RoleName.VIEWER
    status: MembershipStatus = MembershipStatus.ACTIVE
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ProjectMember(BaseModel):
    membership_id: str = Field(default_factory=lambda: f"pjm_{uuid.uuid4().hex[:12]}")
    project_id: str
    user_id: str
    role: RoleName = RoleName.VIEWER
    status: MembershipStatus = MembershipStatus.ACTIVE
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ─────────────────────────────────────────────────────────────
# Security Audit Event
# ─────────────────────────────────────────────────────────────

class SecurityAuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"sec_{uuid.uuid4().hex[:16]}")
    user_id: Optional[str] = None
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    event_type: SecurityEventType
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    result: str = "SUCCESS"  # SUCCESS or FAILURE
    metadata: Dict[str, Any] = Field(default_factory=dict)
    request_ip: Optional[str] = None


# ─────────────────────────────────────────────────────────────
# API Request / Response Schemas
# ─────────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=100)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_format(v)


class UserLoginRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_format(v)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordResetRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_format(v)


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=256)
    new_password: str = Field(..., min_length=8, max_length=128)


class UserProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)


class MemberAddRequest(BaseModel):
    email: str
    role: RoleName = RoleName.VIEWER

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_format(v)


class MemberRoleUpdateRequest(BaseModel):
    role: RoleName


class CurrentUserResponse(BaseModel):
    user: SafeUser
    workspace_memberships: List[Dict[str, Any]] = Field(default_factory=list)
    permissions_summary: List[str] = Field(default_factory=list)


class AuthResponse(BaseModel):
    user: SafeUser
    token: Optional[str] = None
    expires_at: Optional[str] = None
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    mfa_required: bool = False
    mfa_token: Optional[str] = None


class MFASetupResponse(BaseModel):
    factor_id: str
    secret: str
    provisioning_uri: str
    recovery_codes: List[str]


class MFAEnableRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


class MFAVerifyLoginRequest(BaseModel):
    mfa_token: str = Field(..., min_length=10)
    code: str = Field(..., min_length=4, max_length=32)


class MFADisableRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=32)


class StepUpVerifyRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=32)
