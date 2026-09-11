"""
Authentication Application Service for Phase 17.
Coordinates user registration, secure login, session lifecycle, password changes,
single-use cryptographic password resets, and session management.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.auth.crypto import (
    generate_secure_token,
    hash_password,
    hash_token,
    verify_password,
)
from backend.app.engines.auth.mfa import (
    MFAChallengeEngine,
    RecoveryCodeEngine,
    TOTPEngine,
)
from backend.app.engines.auth.models import (
    MFAFactor,
    MFAFactorStatus,
    MFASetupResponse,
    MembershipStatus,
    PasswordResetToken,
    RoleName,
    SafeSession,
    SafeUser,
    SecurityEventType,
    Session,
    User,
    UserLoginRequest,
    UserRegisterRequest,
    UserStatus,
    WorkspaceMember,
    normalize_email,
)
from backend.app.engines.auth.rate_limiter import login_rate_limiter
from backend.app.engines.auth.repository import AuthRepository, auth_repo
from backend.app.engines.workspace.models import Project, Workspace, slugify
from backend.app.engines.workspace.repository import WorkspaceRepository, workspace_repo
from backend.app.services.auth.security_audit_service import SecurityAuditService, security_audit_service


class AuthService:
    """
    Coordinates identity verification, session management, and credential lifecycles.
    """

    def __init__(
        self,
        repository: Optional[AuthRepository] = None,
        workspace_repository: Optional[WorkspaceRepository] = None,
        audit_service: Optional[SecurityAuditService] = None,
    ):
        self._repo = repository or auth_repo
        self._ws_repo = workspace_repository or workspace_repo
        self._audit = audit_service or security_audit_service

    def register_user(
        self,
        req: UserRegisterRequest,
        request_ip: Optional[str] = None,
    ) -> Tuple[SafeUser, Session, str, str, str]:
        """
        Registers a new user, creates their private workspace & default project,
        assigns OWNER membership, and establishes an active session.
        Returns: (SafeUser, Session, raw_token, workspace_id, project_id)
        """
        email_norm = normalize_email(req.email)
        if not email_norm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valid email is required",
            )

        # Check existing account
        existing = self._repo.get_user_by_email(email_norm)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists",
            )

        # Password length policy
        if len(req.password) < settings.AUTH_PASSWORD_MIN_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password must be at least {settings.AUTH_PASSWORD_MIN_LENGTH} characters long",
            )
        if len(req.password) > settings.AUTH_PASSWORD_MAX_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password must not exceed {settings.AUTH_PASSWORD_MAX_LENGTH} characters",
            )

        # Hash password securely
        pwd_hash = hash_password(req.password)

        user = User(
            email=req.email,
            email_normalized=email_norm,
            password_hash=pwd_hash,
            display_name=req.display_name.strip(),
            status=UserStatus.ACTIVE,
        )
        self._repo.save_user(user)

        # Create user's initial workspace
        ws_name = f"{user.display_name}'s Workspace"
        ws_slug = slugify(f"{user.display_name}-workspace")
        workspace = Workspace(
            name=ws_name,
            slug=ws_slug,
            description="Default personal workspace",
        )
        self._ws_repo.save_workspace(workspace)

        # Assign user as OWNER of their workspace
        ws_member = WorkspaceMember(
            workspace_id=workspace.workspace_id,
            user_id=user.user_id,
            role=RoleName.OWNER,
            status=MembershipStatus.ACTIVE,
        )
        self._repo.save_workspace_member(ws_member)

        # Create default project inside the workspace
        project = Project(
            workspace_id=workspace.workspace_id,
            name="General Project",
            slug="general-project",
            description="Default project for analytical assets",
        )
        self._ws_repo.save_project(project)

        # Establish session
        raw_token, session = self._create_session(user.user_id, request_ip=request_ip)

        # Record security audit
        self._audit.record_event(
            event_type=SecurityEventType.ACCOUNT_CREATED,
            user_id=user.user_id,
            workspace_id=workspace.workspace_id,
            project_id=project.project_id,
            request_ip=request_ip,
        )
        self._audit.record_event(
            event_type=SecurityEventType.SESSION_CREATED,
            user_id=user.user_id,
            request_ip=request_ip,
        )

        safe_user = SafeUser(
            user_id=user.user_id,
            email=user.email,
            display_name=user.display_name,
            status=user.status,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
            email_verified_at=user.email_verified_at,
        )
        return safe_user, session, raw_token, workspace.workspace_id, project.project_id

    def login(
        self,
        req: UserLoginRequest,
        request_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[SafeUser, Session, str, str, str]:
        """
        Authenticates user with rate limiting and generic error responses to prevent enumeration.
        Returns: (SafeUser, Session, raw_token, workspace_id, project_id)
        """
        email_norm = normalize_email(req.email)
        rate_key = f"{email_norm}:{request_ip or 'unknown'}"

        is_locked, remaining = login_rate_limiter.is_locked(rate_key)
        if is_locked:
            self._audit.record_event(
                event_type=SecurityEventType.LOGIN_FAILURE,
                result="LOCKED_OUT",
                metadata={"reason": "rate_limit_exceeded"},
                request_ip=request_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Please try again in {remaining} seconds.",
            )

        user = self._repo.get_user_by_email(email_norm)
        if not user:
            login_rate_limiter.record_failure(rate_key)
            self._audit.record_event(
                event_type=SecurityEventType.LOGIN_FAILURE,
                result="FAILURE",
                metadata={"reason": "user_not_found"},
                request_ip=request_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(req.password, user.password_hash):
            login_rate_limiter.record_failure(rate_key)
            self._audit.record_event(
                event_type=SecurityEventType.LOGIN_FAILURE,
                user_id=user.user_id,
                result="FAILURE",
                metadata={"reason": "invalid_password"},
                request_ip=request_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if user.status != UserStatus.ACTIVE:
            self._audit.record_event(
                event_type=SecurityEventType.LOGIN_FAILURE,
                user_id=user.user_id,
                result="BLOCKED",
                metadata={"status": user.status.value},
                request_ip=request_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {user.status.value.lower()}. Please contact an administrator.",
            )

        # Successful authentication: clear rate limiter
        login_rate_limiter.record_success(rate_key)

        now_iso = datetime.now(timezone.utc).isoformat()
        user.last_login_at = now_iso
        user.updated_at = now_iso
        self._repo.save_user(user)

        # Check if user has active MFA enabled
        if user.mfa_enabled:
            factor = self._repo.get_mfa_factor(user.user_id)
            if factor and factor.status == MFAFactorStatus.ACTIVE:
                challenge_token = MFAChallengeEngine.create_challenge_token(user.user_id)
                self._audit.record_event(
                    event_type=SecurityEventType.LOGIN_SUCCESS,
                    user_id=user.user_id,
                    result="MFA_CHALLENGE",
                    request_ip=request_ip,
                )
                safe_user = SafeUser(
                    user_id=user.user_id,
                    email=user.email,
                    display_name=user.display_name,
                    status=user.status,
                    mfa_enabled=True,
                    created_at=user.created_at,
                    last_login_at=user.last_login_at,
                    email_verified_at=user.email_verified_at,
                )
                return safe_user, None, None, None, None, True, challenge_token

        # Create session
        raw_token, session = self._create_session(
            user.user_id,
            request_ip=request_ip,
            user_agent=user_agent,
        )

        workspace_id, project_id = self._resolve_primary_scope(user.user_id, user.display_name)

        self._audit.record_event(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            user_id=user.user_id,
            workspace_id=workspace_id,
            project_id=project_id,
            request_ip=request_ip,
        )

        safe_user = SafeUser(
            user_id=user.user_id,
            email=user.email,
            display_name=user.display_name,
            status=user.status,
            mfa_enabled=user.mfa_enabled,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
            email_verified_at=user.email_verified_at,
        )
        return safe_user, session, raw_token, workspace_id, project_id, False, None

    def _resolve_primary_scope(self, user_id: str, display_name: str = "User") -> Tuple[str, str]:
        """Resolves default workspace and project for a user, creating defaults if missing."""
        memberships = self._repo.list_user_workspaces(user_id)
        if memberships:
            workspace_id = memberships[0].workspace_id
        else:
            ws = Workspace(
                name=f"{display_name}'s Workspace",
                slug=slugify(f"{display_name}-workspace"),
            )
            self._ws_repo.save_workspace(ws)
            self._repo.save_workspace_member(
                WorkspaceMember(
                    workspace_id=ws.workspace_id,
                    user_id=user_id,
                    role=RoleName.OWNER,
                )
            )
            workspace_id = ws.workspace_id

        projects = self._ws_repo.list_projects(workspace_id=workspace_id)
        if projects:
            project_id = projects[0].project_id
        else:
            proj = Project(
                workspace_id=workspace_id,
                name="General Project",
                slug="general-project",
            )
            self._ws_repo.save_project(proj)
            project_id = proj.project_id

        return workspace_id, project_id

    def verify_mfa_login(
        self,
        mfa_token: str,
        code: str,
        request_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[SafeUser, Session, str, str, str]:
        """Verifies TOTP code or recovery code during MFA login challenge."""
        user_id = MFAChallengeEngine.verify_challenge_token(mfa_token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA challenge token is invalid or expired. Please sign in again.",
            )

        user = self._repo.get_user(user_id)
        if not user or user.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user account")

        factor = self._repo.get_mfa_factor(user_id)
        if not factor or factor.status != MFAFactorStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not active for this account")

        # 1. Check TOTP code
        totp_valid = TOTPEngine.verify_totp(factor.secret, code)
        used_recovery = False

        if not totp_valid:
            # 2. Check recovery codes
            recovery_valid, remaining = RecoveryCodeEngine.verify_and_consume(code, factor.recovery_codes_hashes)
            if recovery_valid:
                used_recovery = True
                factor.recovery_codes_hashes = remaining
                self._repo.save_mfa_factor(factor)
                self._audit.record_event(
                    event_type=SecurityEventType.MFA_RECOVERY_USED,
                    user_id=user_id,
                    request_ip=request_ip,
                )
            else:
                self._audit.record_event(
                    event_type=SecurityEventType.MFA_CHALLENGE_FAILED,
                    user_id=user_id,
                    request_ip=request_ip,
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid MFA verification code or recovery code",
                )

        factor.last_used_at = datetime.now(timezone.utc).isoformat()
        self._repo.save_mfa_factor(factor)

        # Create authenticated session
        raw_token, session = self._create_session(user.user_id, request_ip=request_ip, user_agent=user_agent)
        workspace_id, project_id = self._resolve_primary_scope(user.user_id, user.display_name)

        self._audit.record_event(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            user_id=user.user_id,
            workspace_id=workspace_id,
            project_id=project_id,
            metadata={"mfa_verified": True, "used_recovery": used_recovery},
            request_ip=request_ip,
        )

        safe_user = SafeUser(
            user_id=user.user_id,
            email=user.email,
            display_name=user.display_name,
            status=user.status,
            mfa_enabled=True,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
            email_verified_at=user.email_verified_at,
        )
        return safe_user, session, raw_token, workspace_id, project_id

    def setup_mfa(self, user_id: str) -> MFASetupResponse:
        """Generates a new TOTP secret and recovery codes in PENDING state."""
        user = self._repo.get_user(user_id)
        if not user or user.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        secret = TOTPEngine.generate_secret()
        raw_codes, hashed_codes = RecoveryCodeEngine.generate_codes(8)
        uri = TOTPEngine.get_provisioning_uri(secret, user.email)

        factor = MFAFactor(
            user_id=user_id,
            type="totp",
            secret=secret,
            recovery_codes_hashes=hashed_codes,
            status=MFAFactorStatus.PENDING,
        )
        self._repo.save_mfa_factor(factor)

        self._audit.record_event(
            event_type=SecurityEventType.MFA_SETUP_INITIATED,
            user_id=user_id,
        )

        return MFASetupResponse(
            factor_id=factor.factor_id,
            secret=secret,
            provisioning_uri=uri,
            recovery_codes=raw_codes,
        )

    def enable_mfa(self, user_id: str, code: str, request_ip: Optional[str] = None) -> bool:
        """Verifies code from authenticator app to confirm setup and activates MFA."""
        user = self._repo.get_user(user_id)
        if not user or user.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        factor = self._repo.get_mfa_factor(user_id)
        if not factor:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No pending MFA setup found")

        if not TOTPEngine.verify_totp(factor.secret, code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code. Please check your authenticator app.",
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        factor.status = MFAFactorStatus.ACTIVE
        factor.verified_at = now_iso
        factor.last_used_at = now_iso
        self._repo.save_mfa_factor(factor)

        user.mfa_enabled = True
        user.updated_at = now_iso
        self._repo.save_user(user)

        self._audit.record_event(
            event_type=SecurityEventType.MFA_ENABLED,
            user_id=user_id,
            request_ip=request_ip,
        )
        return True

    def disable_mfa(self, user_id: str, code: str, request_ip: Optional[str] = None) -> bool:
        """Disables MFA after verifying active TOTP code or recovery code."""
        user = self._repo.get_user(user_id)
        if not user or user.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        factor = self._repo.get_mfa_factor(user_id)
        if not factor or factor.status != MFAFactorStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not active")

        # Verify code
        totp_valid = TOTPEngine.verify_totp(factor.secret, code)
        if not totp_valid:
            recovery_valid, _ = RecoveryCodeEngine.verify_and_consume(code, factor.recovery_codes_hashes)
            if not recovery_valid:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification or recovery code")

        self._repo.delete_mfa_factor(user_id)
        user.mfa_enabled = False
        user.updated_at = datetime.now(timezone.utc).isoformat()
        self._repo.save_user(user)

        self._audit.record_event(
            event_type=SecurityEventType.MFA_DISABLED,
            user_id=user_id,
            request_ip=request_ip,
        )
        return True

    def verify_step_up(
        self,
        user_id: str,
        code: Optional[str],
        session: Session,
        request_ip: Optional[str] = None,
    ) -> bool:
        """
        Step-Up Authentication for sensitive operations (Phase 24 / Req 16 & 24).
        If MFA is enabled, requires valid TOTP code.
        If MFA is not enabled, verifies session was active/seen within 15 minutes.
        """
        user = self._repo.get_user(user_id)
        if not user or user.status != UserStatus.ACTIVE:
            return False

        if user.mfa_enabled:
            if not code:
                return False
            factor = self._repo.get_mfa_factor(user_id)
            if not factor or factor.status != MFAFactorStatus.ACTIVE:
                return False
            if not TOTPEngine.verify_totp(factor.secret, code):
                return False
        else:
            # Check session recency (< 15 minutes)
            try:
                last_seen = datetime.fromisoformat(session.last_seen_at)
                now = datetime.now(timezone.utc)
                if (now - last_seen).total_seconds() > 900:  # 15 mins
                    return False
            except Exception:
                return False

        self._audit.record_event(
            event_type=SecurityEventType.STEP_UP_VERIFIED,
            user_id=user_id,
            request_ip=request_ip,
        )
        return True


    def _create_session(
        self,
        user_id: str,
        request_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[str, Session]:
        raw_token = generate_secure_token(32)
        token_hashed = hash_token(raw_token)

        expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=settings.AUTH_SESSION_TTL_SECONDS)
        ).isoformat()

        session = Session(
            user_id=user_id,
            token_hash=token_hashed,
            expires_at=expires_at,
            ip_address=request_ip,
            user_agent=user_agent,
        )
        self._repo.save_session(session)
        return raw_token, session

    def logout(self, session_id: str, user_id: str) -> bool:
        """Invalidates the authenticated session."""
        success = self._repo.revoke_session(session_id)
        if success:
            self._audit.record_event(
                event_type=SecurityEventType.LOGOUT,
                user_id=user_id,
                metadata={"session_id": session_id},
            )
        return success

    def get_current_user_from_token(self, raw_token: str) -> Optional[Tuple[User, Session]]:
        """
        Validates a raw bearer/cookie token and returns the active (User, Session) pair.
        Returns None if token is invalid, expired, or revoked.
        """
        if not raw_token:
            return None

        t_hash = hash_token(raw_token)
        session = self._repo.get_session_by_token_hash(t_hash)
        if not session or session.revoked_at is not None:
            return None

        # Check expiration
        now = datetime.now(timezone.utc)
        try:
            expires = datetime.fromisoformat(session.expires_at)
            if now > expires:
                return None
        except Exception:
            return None

        user = self._repo.get_user(session.user_id)
        if not user or user.status != UserStatus.ACTIVE:
            return None

        # Update last seen timestamp
        session.last_seen_at = now.isoformat()
        self._repo.save_session(session)

        return user, session

    def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
        current_session_id: Optional[str] = None,
        request_ip: Optional[str] = None,
    ) -> bool:
        """Changes user password and invalidates other sessions."""
        user = self._repo.get_user(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        if len(new_password) < settings.AUTH_PASSWORD_MIN_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"New password must be at least {settings.AUTH_PASSWORD_MIN_LENGTH} characters long",
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        user.password_hash = hash_password(new_password)
        user.password_changed_at = now_iso
        user.updated_at = now_iso
        self._repo.save_user(user)

        # Invalidate all OTHER sessions for security
        self._repo.revoke_all_user_sessions(user_id, except_session_id=current_session_id)

        self._audit.record_event(
            event_type=SecurityEventType.PASSWORD_CHANGED,
            user_id=user_id,
            request_ip=request_ip,
        )
        return True

    def request_password_reset(
        self,
        email: str,
        request_ip: Optional[str] = None,
    ) -> Optional[str]:
        """
        Creates a single-use password reset token.
        Always returns generic confirmation to caller to prevent email enumeration.
        Returns the raw token string (for testing/development environment).
        """
        email_norm = normalize_email(email)
        user = self._repo.get_user_by_email(email_norm)

        raw_token: Optional[str] = None
        if user and user.status == UserStatus.ACTIVE:
            raw_token = generate_secure_token(32)
            token_hashed = hash_token(raw_token)
            expires_at = (
                datetime.now(timezone.utc) + timedelta(seconds=settings.AUTH_RESET_TOKEN_TTL_SECONDS)
            ).isoformat()

            reset_token = PasswordResetToken(
                token_hash=token_hashed,
                user_id=user.user_id,
                expires_at=expires_at,
            )
            self._repo.save_reset_token(reset_token)

            self._audit.record_event(
                event_type=SecurityEventType.PASSWORD_RESET_REQUESTED,
                user_id=user.user_id,
                request_ip=request_ip,
            )

        return raw_token

    def confirm_password_reset(
        self,
        raw_token: str,
        new_password: str,
        request_ip: Optional[str] = None,
    ) -> bool:
        """Confirms a password reset using a single-use secure token."""
        if not raw_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token is required",
            )

        t_hash = hash_token(raw_token)
        token_obj = self._repo.get_reset_token_by_hash(t_hash)
        if not token_obj or token_obj.used_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        now = datetime.now(timezone.utc)
        try:
            expires = datetime.fromisoformat(token_obj.expires_at)
            if now > expires:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reset token has expired",
                )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token expiration",
            )

        user = self._repo.get_user(token_obj.user_id)
        if not user or user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is inactive",
            )

        if len(new_password) < settings.AUTH_PASSWORD_MIN_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"New password must be at least {settings.AUTH_PASSWORD_MIN_LENGTH} characters long",
            )

        now_iso = now.isoformat()
        user.password_hash = hash_password(new_password)
        user.password_changed_at = now_iso
        user.updated_at = now_iso
        self._repo.save_user(user)

        # Mark token as used (single-use constraint)
        self._repo.mark_reset_token_used(token_obj.token_id)

        # Invalidate all existing sessions
        self._repo.revoke_all_user_sessions(user.user_id)

        self._audit.record_event(
            event_type=SecurityEventType.PASSWORD_RESET_COMPLETED,
            user_id=user.user_id,
            request_ip=request_ip,
        )
        return True

    def list_sessions(
        self,
        user_id: str,
        current_session_id: Optional[str] = None,
    ) -> List[SafeSession]:
        """Lists active sessions for the user without exposing token hashes."""
        sessions = self._repo.list_user_sessions(user_id)
        safe = []
        for s in sessions:
            if s.revoked_at is None:
                safe.append(
                    SafeSession(
                        session_id=s.session_id,
                        created_at=s.created_at,
                        expires_at=s.expires_at,
                        last_seen_at=s.last_seen_at,
                        is_current=(s.session_id == current_session_id),
                        ip_address=s.ip_address,
                        user_agent=s.user_agent,
                    )
                )
        return sorted(safe, key=lambda s: s.last_seen_at, reverse=True)

    def revoke_session(
        self,
        session_id: str,
        user_id: str,
    ) -> bool:
        """Revokes a specific session belonging to the user."""
        session = self._repo.get_session(session_id)
        if not session or session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        success = self._repo.revoke_session(session_id)
        if success:
            self._audit.record_event(
                event_type=SecurityEventType.SESSION_REVOKED,
                user_id=user_id,
                metadata={"revoked_session_id": session_id},
            )
        return success


# Global instance
auth_service = AuthService()
