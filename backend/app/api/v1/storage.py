"""
AnalyzaX — Phase 24: Object Storage & Secure Download API.
Provides cryptographically verified, expiring, authorized file download endpoints (/api/v1/storage/download).
Enforces path traversal defenses, HMAC-SHA256 signature verification, and download-time authorization re-checking.
"""

import os
import time
from typing import Optional
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse

from backend.app.api.deps import get_current_user_optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.auth.models import User
from backend.app.engines.auth.permissions import Permissions
from backend.app.engines.storage.local_provider import LocalStorageProvider
from backend.app.services.auth.authorization_service import authorization_service
from backend.app.services.workspace.workspace_service import workspace_service

router = APIRouter(prefix="/storage", tags=["Storage & Downloads"])
storage_provider = LocalStorageProvider()


@router.get("/download")
def download_storage_file(
    path: str = Query(..., description="Relative storage path of target asset"),
    expires: int = Query(..., description="Unix epoch timestamp when signature expires"),
    sig: str = Query(..., description="Cryptographic HMAC-SHA256 signature"),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> FileResponse:
    """
    Downloads an asset via cryptographically verified signed URL.
    Enforces:
    1. Signature validity (HMAC-SHA256) and expiration window.
    2. Path traversal rejection (cannot escape data storage root).
    3. Download-time authorization re-verification.
    """
    decoded_path = unquote(path).replace("\\", "/")

    # 1. Verify cryptographic signature & expiration
    if not storage_provider.verify_signed_url(decoded_path, expires, sig):
        logger.warning(f"Download rejected: invalid or expired signature for path '{decoded_path}'")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired download signature.",
        )

    # 2. Resolve safe absolute path and test file existence
    try:
        abs_path = storage_provider._resolve_safe_path(decoded_path)
    except ValueError as e:
        logger.warning(f"Directory traversal attack blocked: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid storage path.",
        )

    if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested file not found in storage.",
        )

    # 3. Download-Time Authorization Re-Verification (Requirement 36 & 40)
    # Check workspace context if path indicates a tenant asset
    parts = decoded_path.strip("/").split("/")
    # Check if this is an export, dataset, or report
    if parts and parts[0] in ("exports", "reports", "datasets", "uploads"):
        # For authenticated user, verify active membership
        if current_user:
            # If user has an active session, verify they can access the workspace
            # If path contains workspace_id or asset_id, resolve ownership
            target_ws_id = None
            if len(parts) > 1 and parts[1].startswith("ws_"):
                target_ws_id = parts[1]

            if target_ws_id:
                if not authorization_service.can(current_user.user_id, Permissions.WORKSPACE_READ, workspace_id=target_ws_id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied: you no longer have access to this workspace resource.",
                    )

    # Sanitize filename for Content-Disposition header
    filename = os.path.basename(abs_path)
    safe_filename = "".join(c for c in filename if c.isalnum() or c in (".", "-", "_"))

    return FileResponse(
        path=abs_path,
        filename=safe_filename,
        headers={
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-cache, no-store, must-revalidate",
        },
    )
