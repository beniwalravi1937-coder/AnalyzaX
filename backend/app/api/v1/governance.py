"""
AnalyzaX — Phase 24: Enterprise Governance, Privacy & Data Lifecycle API.
Provides auditable endpoints for cascading workspace deletion, GDPR/CCPA user pseudonymization,
and Data Subject Access Request (DSAR / DSR) packaging.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from pydantic import BaseModel, Field

from backend.app.api.deps import get_current_user, require_permission
from backend.app.engines.auth.models import User
from backend.app.engines.auth.permissions import Permissions
from backend.app.services.governance.deletion_service import deletion_service

router = APIRouter(prefix="/governance", tags=["Governance & Privacy"])


class UserDeleteAccountRequest(BaseModel):
    target_user_id: Optional[str] = Field(None, description="Target user ID to delete/pseudonymize (defaults to caller)")
    confirmation: str = Field(..., description="Must explicitly type 'DELETE' to confirm destructive action")


class DSRRequest(BaseModel):
    confirmation: bool = Field(True, description="Confirmation flag to request personal data export")


@router.post("/workspaces/{workspace_id}/delete")
def delete_workspace_endpoint(
    request: Request,
    workspace_id: str = Path(..., description="ID of the workspace to delete"),
    current_user: User = Depends(require_permission(Permissions.WORKSPACE_DELETE)),
) -> Dict[str, Any]:
    """
    Executes a cascading, safe workspace deletion (Req 62 & 99).
    Restricted to Workspace OWNER.
    Purges projects, dataset uploads, parquet files, exports, and cache keys
    while preserving immutable audit logs.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    return deletion_service.delete_workspace(
        workspace_id=workspace_id,
        actor_user_id=current_user.user_id,
        request_ip=client_ip,
    )


@router.post("/users/delete-account")
def delete_user_account_endpoint(
    req: UserDeleteAccountRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Executes user account deletion and pseudonymization (Req 61 & 64).
    Enforces GDPR/CCPA right-to-be-forgotten without breaking system audit trail integrity.
    """
    if req.confirmation.strip().upper() != "DELETE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action requires confirmation string 'DELETE'.",
        )

    target_id = req.target_user_id or current_user.user_id
    client_ip = request.client.host if request.client else "127.0.0.1"

    return deletion_service.delete_user_account(
        target_user_id=target_id,
        actor_user_id=current_user.user_id,
        request_ip=client_ip,
    )


@router.post("/users/dsr-export")
def generate_dsr_export_endpoint(
    req: DSRRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Generates a GDPR/CCPA Data Subject Request (DSR) export package (Req 63).
    Returns a signed, short-lived download link containing profile, memberships,
    sessions, and activity records.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    return deletion_service.generate_dsr_export(
        user_id=current_user.user_id,
        actor_user_id=current_user.user_id,
        request_ip=client_ip,
    )
