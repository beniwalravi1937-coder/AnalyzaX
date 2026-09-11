"""
Workspace Membership & Security Audit API Router for Phase 17.
Provides endpoints for member listing, role assignment, member removal,
ownership transfer, and workspace security audit inspection.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from backend.app.api.deps import get_current_user, require_permission
from backend.app.engines.auth.models import (
    MemberAddRequest,
    MemberRoleUpdateRequest,
    SecurityAuditEvent,
    User,
    WorkspaceMember,
)
from backend.app.engines.auth.permissions import Permissions
from backend.app.services.auth.membership_service import MembershipService, membership_service
from backend.app.services.auth.security_audit_service import SecurityAuditService, security_audit_service


router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["Members & Audit"])


@router.get("/members", response_model=List[Dict[str, Any]])
def list_members(
    workspace_id: str,
    user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Lists all members of the specified workspace."""
    return membership_service.list_workspace_members(
        workspace_id=workspace_id,
        actor_user_id=user.user_id,
    )


@router.post("/members", response_model=WorkspaceMember, status_code=status.HTTP_201_CREATED)
def add_member(
    workspace_id: str,
    req: MemberAddRequest,
    user: User = Depends(get_current_user),
) -> WorkspaceMember:
    """Adds an existing user to the workspace with specified role."""
    return membership_service.add_workspace_member(
        workspace_id=workspace_id,
        email=req.email,
        role=req.role,
        actor_user_id=user.user_id,
    )


@router.patch("/members/{member_user_id}", response_model=WorkspaceMember)
def update_member_role(
    workspace_id: str,
    member_user_id: str,
    req: MemberRoleUpdateRequest,
    user: User = Depends(get_current_user),
) -> WorkspaceMember:
    """Updates a member's role within the workspace with Owner Protection."""
    return membership_service.update_workspace_member_role(
        workspace_id=workspace_id,
        target_user_id=member_user_id,
        new_role=req.role,
        actor_user_id=user.user_id,
    )


@router.delete("/members/{member_user_id}")
def remove_member(
    workspace_id: str,
    member_user_id: str,
    user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Removes a member from the workspace with Owner Protection."""
    membership_service.remove_workspace_member(
        workspace_id=workspace_id,
        target_user_id=member_user_id,
        actor_user_id=user.user_id,
    )
    return {"message": "Member removed from workspace"}


@router.post("/transfer-ownership")
def transfer_ownership(
    workspace_id: str,
    target_user_id: str = Body(..., embed=True),
    user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Transfers primary workspace ownership to another member."""
    membership_service.transfer_workspace_ownership(
        workspace_id=workspace_id,
        target_user_id=target_user_id,
        actor_user_id=user.user_id,
    )
    return {"message": "Workspace ownership transferred successfully"}


@router.get("/audit-logs", response_model=List[SecurityAuditEvent])
def get_workspace_audit_logs(
    workspace_id: str,
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(require_permission(Permissions.AUDIT_READ)),
) -> List[SecurityAuditEvent]:
    """Retrieves security audit logs for the workspace (restricted to OWNER and ADMIN)."""
    return security_audit_service.query_events(
        workspace_id=workspace_id,
        limit=limit,
    )
