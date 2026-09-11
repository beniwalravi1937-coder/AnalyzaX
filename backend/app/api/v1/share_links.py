"""
REST API Router for Share Links (Phase 18).
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.deps import get_current_user
from backend.app.engines.auth.models import User
from backend.app.engines.collaboration.models import (
    CreateShareLinkRequest,
    ResourceType,
    ShareLinkResponse,
)
from backend.app.services.collaboration.share_service import share_service

router = APIRouter(tags=["Share Links"])


@router.post("/resources/{resource_type}/{resource_id}/share-links", response_model=ShareLinkResponse, status_code=201)
def create_share_link(
    resource_type: ResourceType,
    resource_id: str,
    req: CreateShareLinkRequest,
    user: User = Depends(get_current_user),
) -> ShareLinkResponse:
    """Creates a cryptographic share link."""
    link, share_url = share_service.create_share_link(
        created_by_user_id=user.user_id,
        req=req,
    )
    return ShareLinkResponse(
        share_link_id=link.share_link_id,
        resource_type=link.resource_type,
        resource_id=link.resource_id,
        link_mode=link.link_mode,
        permission=link.permission,
        status=link.status,
        created_at=link.created_at,
        expires_at=link.expires_at,
        access_count=link.access_count,
        share_url=share_url,
    )


@router.post("/share-links/{share_link_id}/revoke")
def revoke_share_link(
    share_link_id: str,
    user: User = Depends(get_current_user),
):
    """Revokes a share link immediately."""
    revoked = share_service.revoke_share_link(
        share_link_id=share_link_id,
        revoker_user_id=user.user_id,
    )
    return {
        "message": "Share link revoked successfully",
        "share_link_id": revoked.share_link_id,
        "status": revoked.status.value,
    }
