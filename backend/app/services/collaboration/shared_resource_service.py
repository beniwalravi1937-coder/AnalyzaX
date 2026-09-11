"""
Shared Resource Presentation Service for Phase 18.
Resolves shared resource views (/shared/{token}) with Restricted Presentation Projection.
Masks inaccessible dashboard/report dependencies, conceals private credentials, and prevents data leakage.
"""

from datetime import datetime, timezone
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.auth.crypto import hash_session_token
from backend.app.engines.auth.models import UserStatus
from backend.app.engines.auth.repository import AuthRepository, auth_repo
from backend.app.engines.collaboration.models import (
    CollaborationActivityEvent,
    CollaborationEventType,
    ResourceType,
    ShareLinkMode,
    SharePermission,
    ShareStatus,
    SharedResourceView,
)
from backend.app.engines.collaboration.repository import CollaborationRepository, collaboration_repo
from backend.app.engines.workspace.repository import WorkspaceRepository, workspace_repo
from backend.app.services.collaboration.access_service import AccessService, access_service


class SharedResourceService:
    """Renders restricted presentation projections for shared link visitors."""

    def __init__(
        self,
        collab_repository: Optional[CollaborationRepository] = None,
        auth_repository: Optional[AuthRepository] = None,
        workspace_repository: Optional[WorkspaceRepository] = None,
        access_resolver: Optional[AccessService] = None,
    ):
        self._collab_repo = collab_repository or collaboration_repo
        self._auth_repo = auth_repository or auth_repo
        self._ws_repo = workspace_repository or workspace_repo
        self._access = access_resolver or access_service

    def get_shared_resource(
        self,
        raw_token: str,
        current_user_id: Optional[str] = None,
    ) -> SharedResourceView:
        """Resolves and projects a shared resource securely."""
        if not raw_token or len(raw_token) < 10:
            raise HTTPException(status_code=400, detail="Invalid share token")

        token_hash = hash_session_token(raw_token)
        link = self._collab_repo.get_share_link_by_token_hash(token_hash)
        if not link:
            raise HTTPException(status_code=404, detail="Shared link not found or has been revoked")

        if link.status == ShareStatus.REVOKED:
            raise HTTPException(status_code=410, detail="This share link has been revoked by the owner")

        if link.expires_at:
            exp = datetime.fromisoformat(link.expires_at)
            if exp <= datetime.now(timezone.utc) or link.status == ShareStatus.EXPIRED:
                raise HTTPException(status_code=410, detail="This share link has expired")

        # 1. Internal authenticated validation
        is_public = link.link_mode == ShareLinkMode.PUBLIC_READ_ONLY
        if not is_public:
            if not current_user_id:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required to view this internal workspace link",
                )
            user = self._auth_repo.get_user(current_user_id)
            if not user or user.status != UserStatus.ACTIVE:
                raise HTTPException(status_code=403, detail="Active user account required")

        # 2. Increment access count
        self._collab_repo.increment_share_link_access(link.share_link_id)

        creator = self._auth_repo.get_user(link.created_by_user_id)
        creator_name = creator.display_name if creator else "Team Member"

        # 3. Resolve resource
        asset = self._ws_repo.get_asset(link.resource_id) or self._ws_repo.find_asset_by_source_id(link.resource_id)
        title = asset.name if asset else f"Shared {link.resource_type.value}"
        description = asset.description if asset else None

        warnings: List[str] = []
        content: Dict[str, Any] = {}

        # 4. Restricted Presentation Projection by Resource Type
        if link.resource_type == ResourceType.DASHBOARD:
            # Load dashboard JSON if exists
            dash_path = os.path.join(settings.DATA_DASHBOARDS_DIR, f"{link.resource_id}.json")
            if os.path.exists(dash_path):
                try:
                    with open(dash_path, "r", encoding="utf-8") as f:
                        raw_dash = json.load(f)

                    # Project safe dashboard fields
                    title = raw_dash.get("title", title)
                    description = raw_dash.get("description", description)
                    raw_components = raw_dash.get("components", [])
                    safe_components = []

                    # Dependency Check for Dashboard Components
                    for c in raw_components:
                        source_ds_id = c.get("dataset_id") or c.get("dataset_version_id")
                        if source_ds_id:
                            # Verify if visitor has access to source dataset
                            eff = self._access.resolve_effective_access(
                                current_user_id,
                                ResourceType.DATASET,
                                source_ds_id,
                                raw_share_token=raw_token if is_public else None,
                            )
                            if not eff.can_view:
                                # Mask component with safe notice
                                safe_components.append({
                                    "id": c.get("id"),
                                    "type": "restricted",
                                    "title": c.get("title", "Component"),
                                    "message": "Some dashboard content is unavailable due to access restrictions.",
                                })
                                warnings.append("One or more dashboard components were restricted.")
                                continue

                        # Strip raw server file paths or database credentials if any
                        clean_comp = {k: v for k, v in c.items() if k not in ("file_path", "connection_string", "sql_query")}
                        safe_components.append(clean_comp)

                    content = {
                        "dashboard_id": raw_dash.get("dashboard_id", link.resource_id),
                        "title": title,
                        "description": description,
                        "layout": raw_dash.get("layout", {}),
                        "components": safe_components,
                    }
                except Exception as e:
                    logger.warning(f"Error loading dashboard: {e}")
                    content = {"message": "Dashboard rendered in presentation mode"}
            else:
                content = {"dashboard_id": link.resource_id, "title": title, "components": []}

        elif link.resource_type == ResourceType.REPORT:
            report_path = os.path.join(settings.DATA_EXPORTS_DIR, f"{link.resource_id}.json")
            if os.path.exists(report_path):
                try:
                    with open(report_path, "r", encoding="utf-8") as f:
                        raw_report = json.load(f)
                    content = {
                        "report_id": link.resource_id,
                        "title": raw_report.get("title", title),
                        "sections": raw_report.get("sections", []),
                    }
                except Exception:
                    content = {"report_id": link.resource_id, "title": title}
            else:
                content = {"report_id": link.resource_id, "title": title}

        elif link.resource_type in (ResourceType.DATASET, ResourceType.DATASET_VERSION):
            # Expose schema metadata probe, never raw file paths or database credentials
            content = {
                "dataset_id": link.resource_id,
                "name": title,
                "description": description,
                "asset_type": link.resource_type.value,
                "preview_note": "Dataset presentation preview. Direct filesystem paths are restricted.",
            }
        else:
            content = {
                "resource_id": link.resource_id,
                "resource_type": link.resource_type.value,
                "title": title,
            }

        # 5. Log activity
        self._collab_repo.record_activity(
            CollaborationActivityEvent(
                workspace_id=link.workspace_id,
                project_id=link.project_id,
                actor_user_id=current_user_id or "anonymous",
                event_type=CollaborationEventType.SHARE_LINK_ACCESSED,
                resource_type=link.resource_type,
                resource_id=link.resource_id,
                details={"share_link_id": link.share_link_id, "is_public": is_public},
            )
        )

        return SharedResourceView(
            resource_type=link.resource_type,
            resource_id=link.resource_id,
            title=title,
            description=description,
            permission=link.permission,
            created_at=link.created_at,
            shared_by_name=creator_name,
            is_public=is_public,
            content=content,
            warnings=list(set(warnings)),
        )


# Global singleton instance
shared_resource_service = SharedResourceService()
