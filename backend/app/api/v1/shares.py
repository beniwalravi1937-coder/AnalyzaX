"""
REST API Router for Resource Sharing & Access Management (Phase 18).
"""

from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.deps import get_current_user
from backend.app.engines.auth.models import User
from backend.app.engines.collaboration.models import (
    CreateShareRequest,
    ResourceAccessSummary,
    ResourceShareResponse,
    ResourceType,
    UpdateShareRequest,
)
from backend.app.services.collaboration.share_service import share_service

router = APIRouter(tags=["Resource Sharing"])


@router.post("/shares", response_model=ResourceShareResponse, status_code=201)
def create_resource_share(
    req: CreateShareRequest,
    user: User = Depends(get_current_user),
) -> ResourceShareResponse:
    """Shares an analytical asset directly with a user or project."""
    share = share_service.create_share(
        shared_by_user_id=user.user_id,
        req=req,
    )
    return ResourceShareResponse(
        share_id=share.share_id,
        resource_type=share.resource_type,
        resource_id=share.resource_id,
        workspace_id=share.workspace_id,
        project_id=share.project_id,
        shared_by_user_id=share.shared_by_user_id,
        shared_by_name=user.display_name,
        recipient_type=share.recipient_type,
        recipient_id=share.recipient_id,
        permission=share.permission,
        status=share.status,
        created_at=share.created_at,
        expires_at=share.expires_at,
    )


@router.patch("/shares/{share_id}")
def update_resource_share(
    share_id: str,
    req: UpdateShareRequest,
    user: User = Depends(get_current_user),
):
    """Updates an existing resource share."""
    updated = share_service.update_share(
        share_id=share_id,
        updater_user_id=user.user_id,
        req=req,
    )
    return {
        "message": "Share updated successfully",
        "share_id": updated.share_id,
        "permission": updated.permission.value,
        "expires_at": updated.expires_at,
    }


@router.post("/shares/{share_id}/revoke")
def revoke_resource_share(
    share_id: str,
    user: User = Depends(get_current_user),
):
    """Revokes a direct resource share."""
    revoked = share_service.revoke_share(
        share_id=share_id,
        revoker_user_id=user.user_id,
    )
    return {
        "message": "Share revoked successfully",
        "share_id": revoked.share_id,
        "status": revoked.status.value,
    }


@router.get("/resources/{resource_type}/{resource_id}/access", response_model=ResourceAccessSummary)
def get_resource_access(
    resource_type: ResourceType,
    resource_id: str,
    user: User = Depends(get_current_user),
) -> ResourceAccessSummary:
    """Returns the complete access summary for the 'Manage Access' dialog."""
    return share_service.list_resource_access(
        resource_type=resource_type,
        resource_id=resource_id,
        requesting_user_id=user.user_id,
    )
