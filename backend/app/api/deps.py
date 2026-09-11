"""
FastAPI dependencies for Phase 17 Authentication, Authorization & Scope Resolution.
Extracts session tokens from Authorization Bearer headers or HttpOnly cookies,
resolves current user identity, and enforces RBAC permission requirements server-side.
"""

from typing import Callable, Optional

from fastapi import Depends, Header, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.core.config import settings
from backend.app.engines.auth.models import Session, User, UserStatus
from backend.app.engines.auth.permissions import Permissions
from backend.app.services.auth.auth_service import AuthService, auth_service
from backend.app.services.auth.authorization_service import AuthorizationService, authorization_service


security_bearer = HTTPBearer(auto_error=False)


def get_token_from_request(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = None) -> Optional[str]:
    """
    Extracts raw authentication token from either:
    1. Authorization Bearer header
    2. HttpOnly Cookie (analyzax_session)
    """
    if credentials and credentials.credentials:
        return credentials.credentials.strip()

    # Check Authorization header directly if HTTPBearer didn't catch it
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()

    # Check session cookie
    cookie_token = request.cookies.get(settings.AUTH_SESSION_COOKIE_NAME)
    if cookie_token:
        return cookie_token.strip()

    return None


def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> Optional[User]:
    """
    Resolves the authenticated user if valid token exists, or returns None.
    Does not raise 401. Useful for mixed or public endpoints.
    """
    token = get_token_from_request(request, credentials)
    if not token:
        return None

    result = auth_service.get_current_user_from_token(token)
    if not result:
        return None

    user, session = result
    request.state.session = session
    request.state.raw_token = token
    return user


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> User:
    """
    Strictly requires an authenticated, active user.
    Raises 401 Unauthorized if token is missing, invalid, expired, or revoked.
    """
    user = get_current_user_optional(request, credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_session(request: Request, user: User = Depends(get_current_user)) -> Session:
    """Retrieves the active Session object associated with the authenticated request."""
    session = getattr(request.state, "session", None)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Active session required",
        )
    return session


def require_permission(permission: str) -> Callable:
    """
    Dependency factory that verifies whether the authenticated user holds
    the required permission within the requested workspace and/or project scope.
    Scope is determined from query params, request headers, or path params.
    """
    def dependency(
        request: Request,
        user: User = Depends(get_current_user),
        x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
        x_project_id: Optional[str] = Header(None, alias="X-Project-Id"),
    ) -> User:
        # Resolve target workspace and project IDs from path, header, or query
        target_ws_id = (
            request.path_params.get("workspace_id")
            or x_workspace_id
            or request.query_params.get("workspace_id")
        )
        target_proj_id = (
            request.path_params.get("project_id")
            or x_project_id
            or request.query_params.get("project_id")
        )

        if not authorization_service.can(
            user_id=user.user_id,
            permission=permission,
            workspace_id=target_ws_id,
            project_id=target_proj_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: insufficient permissions for '{permission}'",
            )
        return user

    return dependency
