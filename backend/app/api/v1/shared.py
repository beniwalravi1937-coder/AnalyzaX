"""
REST API Router for Shared Resource Resolution (Phase 18).
Provides the presentation endpoint (/api/v1/shared/{token}) for internal and public share links.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.deps import get_current_user_optional
from backend.app.engines.auth.models import User
from backend.app.engines.collaboration.models import SharedResourceView
from backend.app.services.collaboration.shared_resource_service import shared_resource_service

router = APIRouter(prefix="/shared", tags=["Shared Presentation"])


@router.get("/{token}", response_model=SharedResourceView)
def get_shared_resource_view(
    token: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> SharedResourceView:
    """Resolves and projects an internally or publicly shared resource."""
    user_id = current_user.user_id if current_user else None
    return shared_resource_service.get_shared_resource(
        raw_token=token,
        current_user_id=user_id,
    )
