"""
REST API Router for Workspace Invitations (Phase 18).
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.app.api.deps import get_current_user
from backend.app.engines.auth.models import User
from backend.app.engines.collaboration.models import (
    CreateInvitationRequest,
    InvitationResponse,
    InvitationStatus,
    InvitationVerifyResponse,
)
from backend.app.services.collaboration.invitation_service import invitation_service

router = APIRouter(tags=["Workspace Invitations"])


class AcceptInvitationRequest(BaseModel):
    token: str


@router.post("/workspaces/{workspace_id}/invitations", response_model=InvitationResponse, status_code=201)
def create_workspace_invitation(
    workspace_id: str,
    req: CreateInvitationRequest,
    user: User = Depends(get_current_user),
) -> InvitationResponse:
    """Creates a workspace invitation with a single-use cryptographic token."""
    invitation, raw_token = invitation_service.create_invitation(
        workspace_id=workspace_id,
        invited_by_user_id=user.user_id,
        req=req,
    )
    return InvitationResponse(
        invitation_id=invitation.invitation_id,
        workspace_id=invitation.workspace_id,
        email=invitation.email,
        intended_role=invitation.intended_role,
        status=invitation.status,
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
        invited_by_user_id=invitation.invited_by_user_id,
        invited_by_name=user.display_name,
        preview_token=raw_token,
    )


@router.get("/workspaces/{workspace_id}/invitations", response_model=List[InvitationResponse])
def list_workspace_invitations(
    workspace_id: str,
    status: Optional[InvitationStatus] = Query(None, description="Filter by status"),
    user: User = Depends(get_current_user),
) -> List[InvitationResponse]:
    """Lists invitations for a workspace."""
    return invitation_service.list_invitations(
        workspace_id=workspace_id,
        requesting_user_id=user.user_id,
        status=status,
    )


@router.get("/invitations/verify/{token}", response_model=InvitationVerifyResponse)
def verify_invitation_token(token: str) -> InvitationVerifyResponse:
    """Public token verification returning invitation context."""
    return invitation_service.verify_invitation(token)


@router.post("/invitations/{invitation_id}/accept")
def accept_invitation(
    invitation_id: str,
    req: AcceptInvitationRequest,
    user: User = Depends(get_current_user),
):
    """Accepts an outstanding invitation, granting workspace membership."""
    member = invitation_service.accept_invitation(
        raw_token=req.token,
        accepting_user_id=user.user_id,
    )
    return {
        "message": "Invitation accepted successfully",
        "membership_id": member.membership_id,
        "workspace_id": member.workspace_id,
        "role": member.role.value,
    }


@router.post("/invitations/{invitation_id}/revoke")
def revoke_invitation(
    invitation_id: str,
    user: User = Depends(get_current_user),
):
    """Revokes a pending workspace invitation."""
    inv = invitation_service.revoke_invitation(
        invitation_id=invitation_id,
        revoker_user_id=user.user_id,
    )
    return {"message": "Invitation revoked", "invitation_id": inv.invitation_id, "status": inv.status.value}


@router.post("/invitations/{invitation_id}/resend")
def resend_invitation(
    invitation_id: str,
    user: User = Depends(get_current_user),
):
    """Resets expiration and issues a fresh token for an existing invitation."""
    inv, raw_token = invitation_service.resend_invitation(
        invitation_id=invitation_id,
        resender_user_id=user.user_id,
    )
    return {
        "message": "Invitation resent successfully",
        "invitation_id": inv.invitation_id,
        "expires_at": inv.expires_at,
        "preview_token": raw_token,
    }
