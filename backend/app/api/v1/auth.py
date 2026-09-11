"""
Authentication API Router for Phase 17.
Provides endpoints for registration, login, logout, identity inspection (/me),
profile updates, password change, single-use password reset, and session management.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from backend.app.core.config import settings
from backend.app.engines.auth.models import (
    AuthResponse,
    CurrentUserResponse,
    MFADisableRequest,
    MFAEnableRequest,
    MFASetupResponse,
    MFAVerifyLoginRequest,
    PasswordChangeRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    SafeSession,
    SafeUser,
    Session,
    StepUpVerifyRequest,
    User,
    UserLoginRequest,
    UserProfileUpdateRequest,
    UserRegisterRequest,
)
from backend.app.engines.auth.permissions import get_role_permissions
from backend.app.engines.auth.repository import auth_repo
from backend.app.engines.workspace.repository import workspace_repo
from backend.app.api.deps import get_current_session, get_current_user
from backend.app.services.auth.auth_service import AuthService, auth_service


router = APIRouter(prefix="/auth", tags=["Authentication"])


def _set_auth_cookie(response: Response, token: str, max_age: int) -> None:
    """Sets a secure HttpOnly session cookie."""
    is_production = settings.APP_ENV.lower() == "production"
    response.set_cookie(
        key=settings.AUTH_SESSION_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=is_production,
        samesite="lax",
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    """Clears the session cookie."""
    response.delete_cookie(
        key=settings.AUTH_SESSION_COOKIE_NAME,
        path="/",
        samesite="lax",
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    req: UserRegisterRequest,
    request: Request,
    response: Response,
) -> AuthResponse:
    """Registers a new user, sets session cookie, and returns initial auth context."""
    client_ip = request.client.host if request.client else None
    safe_user, session, raw_token, ws_id, proj_id = auth_service.register_user(
        req=req,
        request_ip=client_ip,
    )
    _set_auth_cookie(response, raw_token, settings.AUTH_SESSION_TTL_SECONDS)

    return AuthResponse(
        user=safe_user,
        token=raw_token,
        expires_at=session.expires_at,
        workspace_id=ws_id,
        project_id=proj_id,
    )


@router.post("/login", response_model=AuthResponse)
def login(
    req: UserLoginRequest,
    request: Request,
    response: Response,
) -> AuthResponse:
    """Authenticates user credentials, sets session cookie, or returns MFA challenge."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    safe_user, session, raw_token, ws_id, proj_id, mfa_required, mfa_token = auth_service.login(
        req=req,
        request_ip=client_ip,
        user_agent=user_agent,
    )
    if mfa_required:
        return AuthResponse(
            user=safe_user,
            mfa_required=True,
            mfa_token=mfa_token,
        )

    _set_auth_cookie(response, raw_token, settings.AUTH_SESSION_TTL_SECONDS)

    return AuthResponse(
        user=safe_user,
        token=raw_token,
        expires_at=session.expires_at,
        workspace_id=ws_id,
        project_id=proj_id,
        mfa_required=False,
    )



@router.post("/logout")
def logout(
    response: Response,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_current_session),
) -> Dict[str, str]:
    """Invalidates active server session and clears session cookie."""
    auth_service.logout(session.session_id, user.user_id)
    _clear_auth_cookie(response)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=CurrentUserResponse)
def get_me(
    user: User = Depends(get_current_user),
) -> CurrentUserResponse:
    """Returns profile and workspace context for the currently authenticated user."""
    memberships = auth_repo.list_user_workspaces(user.user_id)
    ws_list = []
    all_perms = set()

    for m in memberships:
        ws = workspace_repo.get_workspace(m.workspace_id)
        ws_list.append({
            "workspace_id": m.workspace_id,
            "workspace_name": ws.name if ws else "Workspace",
            "workspace_slug": ws.slug if ws else "",
            "role": m.role.value,
            "status": m.status.value,
        })
        all_perms.update(get_role_permissions(m.role))

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

    return CurrentUserResponse(
        user=safe_user,
        workspace_memberships=ws_list,
        permissions_summary=sorted(list(all_perms)),
    )


@router.patch("/profile", response_model=SafeUser)
def update_profile(
    req: UserProfileUpdateRequest,
    user: User = Depends(get_current_user),
) -> SafeUser:
    """Updates user display name."""
    if req.display_name:
        user.display_name = req.display_name.strip()
        auth_repo.save_user(user)

    return SafeUser(
        user_id=user.user_id,
        email=user.email,
        display_name=user.display_name,
        status=user.status,
        mfa_enabled=user.mfa_enabled,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        email_verified_at=user.email_verified_at,
    )


@router.post("/password/change")
def change_password(
    req: PasswordChangeRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_current_session),
) -> Dict[str, str]:
    """Changes password for authenticated user and invalidates other sessions."""
    client_ip = request.client.host if request.client else None
    auth_service.change_password(
        user_id=user.user_id,
        current_password=req.current_password,
        new_password=req.new_password,
        current_session_id=session.session_id,
        request_ip=client_ip,
    )
    return {"message": "Password changed successfully"}


@router.post("/password/reset/request")
def request_password_reset(
    req: PasswordResetRequest,
    request: Request,
) -> Dict[str, Any]:
    """
    Initiates single-use password reset.
    Returns generic confirmation to prevent user enumeration.
    """
    client_ip = request.client.host if request.client else None
    raw_token = auth_service.request_password_reset(req.email, request_ip=client_ip)

    res: Dict[str, Any] = {
        "message": "If the email is registered, a password reset link has been generated."
    }
    # In development mode, expose reset token to facilitate local testing
    if settings.APP_ENV.lower() == "development" and raw_token:
        res["dev_reset_token"] = raw_token

    return res


@router.post("/password/reset/confirm")
def confirm_password_reset(
    req: PasswordResetConfirmRequest,
    request: Request,
) -> Dict[str, str]:
    """Confirms password reset using a single-use token and invalidates all prior sessions."""
    client_ip = request.client.host if request.client else None
    auth_service.confirm_password_reset(
        raw_token=req.token,
        new_password=req.new_password,
        request_ip=client_ip,
    )
    return {"message": "Password has been successfully reset. Please sign in."}


@router.get("/sessions", response_model=List[SafeSession])
def list_sessions(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_current_session),
) -> List[SafeSession]:
    """Lists all active sessions for the current user."""
    return auth_service.list_sessions(user.user_id, current_session_id=session.session_id)


@router.post("/sessions/{session_id}/revoke")
def revoke_session(
    session_id: str,
    user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Revokes a specific session belonging to the user."""
    auth_service.revoke_session(session_id, user.user_id)
    return {"message": "Session revoked successfully"}


# ─────────────────────────────────────────────────────────────
# Multi-Factor Authentication (MFA) & Step-Up Endpoints (Phase 24)
# ─────────────────────────────────────────────────────────────

@router.post("/mfa/setup", response_model=MFASetupResponse)
def setup_mfa(
    user: User = Depends(get_current_user),
) -> MFASetupResponse:
    """Initiates TOTP MFA enrollment and returns secret, QR URI, and backup recovery codes."""
    return auth_service.setup_mfa(user.user_id)


@router.post("/mfa/enable")
def enable_mfa(
    req: MFAEnableRequest,
    request: Request,
    user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Confirms TOTP setup by verifying authenticator code and activates MFA on the account."""
    client_ip = request.client.host if request.client else None
    auth_service.enable_mfa(user.user_id, req.code, request_ip=client_ip)
    return {"message": "Multi-factor authentication enabled successfully"}


@router.post("/mfa/verify", response_model=AuthResponse)
def verify_mfa_login(
    req: MFAVerifyLoginRequest,
    request: Request,
    response: Response,
) -> AuthResponse:
    """Verifies TOTP or recovery code against an active MFA challenge to establish session."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    safe_user, session, raw_token, ws_id, proj_id = auth_service.verify_mfa_login(
        mfa_token=req.mfa_token,
        code=req.code,
        request_ip=client_ip,
        user_agent=user_agent,
    )
    _set_auth_cookie(response, raw_token, settings.AUTH_SESSION_TTL_SECONDS)

    return AuthResponse(
        user=safe_user,
        token=raw_token,
        expires_at=session.expires_at,
        workspace_id=ws_id,
        project_id=proj_id,
        mfa_required=False,
    )


@router.post("/mfa/disable")
def disable_mfa(
    req: MFADisableRequest,
    request: Request,
    user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Disables MFA after verifying active TOTP code or recovery code."""
    client_ip = request.client.host if request.client else None
    auth_service.disable_mfa(user.user_id, req.code, request_ip=client_ip)
    return {"message": "Multi-factor authentication disabled successfully"}


@router.post("/step-up")
def verify_step_up(
    req: StepUpVerifyRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_current_session),
) -> Dict[str, Any]:
    """Verifies recent identity re-authentication for high-privilege operations."""
    client_ip = request.client.host if request.client else None
    is_valid = auth_service.verify_step_up(
        user_id=user.user_id,
        code=req.code,
        session=session,
        request_ip=client_ip,
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Step-up authentication failed: invalid code or session expired",
        )
    return {"success": True, "message": "Step-up authentication verified"}

