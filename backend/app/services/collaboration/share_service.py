"""
Application Service for Resource Sharing & Share Links (Phase 18).
Handles direct resource sharing, share-link generation, revocation,
permission elevation / boundary checks, and access summaries.
"""

from datetime import datetime, timedelta, timezone
import secrets
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.auth.crypto import hash_session_token
from backend.app.engines.auth.models import (
    MembershipStatus,
    RoleName,
    SecurityAuditEvent,
    SecurityEventType,
    User,
)
from backend.app.engines.auth.permissions import Permission
from backend.app.engines.auth.repository import AuthRepository, auth_repo
from backend.app.engines.collaboration.models import (
    CollaborationActivityEvent,
    CollaborationEventType,
    CreateShareLinkRequest,
    CreateShareRequest,
    Notification,
    NotificationType,
    ResourceAccessSummary,
    ResourceShare,
    ResourceShareResponse,
    ResourceType,
    ShareLink,
    ShareLinkMode,
    ShareLinkResponse,
    SharePermission,
    ShareRecipientType,
    ShareStatus,
    UpdateShareRequest,
)
from backend.app.engines.collaboration.repository import CollaborationRepository, collaboration_repo
from backend.app.engines.workspace.repository import WorkspaceRepository, workspace_repo
from backend.app.engines.notifications.models import ApplicationEventType
from backend.app.services.notifications.event_dispatcher import event_dispatcher
from backend.app.services.auth.authorization_service import AuthorizationService
from backend.app.services.collaboration.access_service import AccessService, access_service


class ShareService:
    """Coordinates asset-level sharing, link generation, and revocation."""

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
        self._authz = AuthorizationService(self._auth_repo, self._ws_repo)

    def _resolve_resource_context(self, resource_type: ResourceType, resource_id: str) -> Tuple[str, Optional[str], str]:
        """Resolves (workspace_id, project_id, resource_name)."""
        asset = self._ws_repo.get_asset(resource_id) or self._ws_repo.find_asset_by_source_id(resource_id)
        if asset:
            return asset.workspace_id, asset.project_id, asset.name

        proj = self._ws_repo.get_project(resource_id)
        if proj:
            return proj.workspace_id, proj.project_id, proj.name

        ws = self._ws_repo.get_workspace(resource_id)
        if ws:
            return ws.workspace_id, None, ws.name

        raise HTTPException(status_code=404, detail=f"Resource '{resource_id}' not found")

    def create_share(
        self,
        shared_by_user_id: str,
        req: CreateShareRequest,
    ) -> ResourceShare:
        """Shares an analytical asset with a user or principal."""
        ws_id, proj_id, res_name = self._resolve_resource_context(req.resource_type, req.resource_id)

        # 1. Verify sharer has permission to share (can EDIT or is ADMIN/OWNER)
        eff = self._access.resolve_effective_access(shared_by_user_id, req.resource_type, req.resource_id)
        if not eff.can_edit:
            # Also check if user is workspace admin/owner
            ws_member = self._auth_repo.get_workspace_member(ws_id, shared_by_user_id)
            if not ws_member or ws_member.role not in (RoleName.OWNER, RoleName.ADMIN):
                raise HTTPException(
                    status_code=403,
                    detail="You do not have permission to share this resource",
                )

        # 2. Validate recipient
        recipient_name = "Recipient"
        if req.recipient_type == ShareRecipientType.USER:
            recip_user = self._auth_repo.get_user(req.recipient_id)
            if not recip_user:
                raise HTTPException(status_code=404, detail="Recipient user not found")
            recipient_name = recip_user.display_name
            if recip_user.user_id == shared_by_user_id:
                raise HTTPException(status_code=400, detail="Cannot share a resource with yourself")
        elif req.recipient_type == ShareRecipientType.PROJECT:
            recip_proj = self._ws_repo.get_project(req.recipient_id)
            if not recip_proj:
                raise HTTPException(status_code=404, detail="Recipient project not found")
            recipient_name = recip_proj.name

        # 3. Create or update share
        expires_at = None
        if req.expires_in_days:
            expires_at = (datetime.now(timezone.utc) + timedelta(days=req.expires_in_days)).isoformat()

        existing = self._collab_repo.find_direct_share(
            req.resource_id,
            req.recipient_id,
            req.recipient_type,
        )
        if existing:
            existing.permission = req.permission
            existing.expires_at = expires_at
            existing.status = ShareStatus.ACTIVE
            existing.updated_at = datetime.now(timezone.utc).isoformat()
            share = existing
        else:
            share = ResourceShare(
                resource_type=req.resource_type,
                resource_id=req.resource_id,
                workspace_id=ws_id,
                project_id=proj_id,
                shared_by_user_id=shared_by_user_id,
                recipient_type=req.recipient_type,
                recipient_id=req.recipient_id,
                permission=req.permission,
                status=ShareStatus.ACTIVE,
                expires_at=expires_at,
            )

        self._collab_repo.save_share(share)
        self._access.invalidate_cache(user_id=req.recipient_id, resource_id=req.resource_id)

        # 4. Security Audit & Activity Logging
        sharer = self._auth_repo.get_user(shared_by_user_id)
        sharer_name = sharer.display_name if sharer else "User"

        self._auth_repo.record_audit_event(
            SecurityAuditEvent(
                user_id=shared_by_user_id,
                workspace_id=ws_id,
                project_id=proj_id,
                event_type=SecurityEventType.MEMBERSHIP_ROLE_CHANGED,
                result="SUCCESS",
                metadata={
                    "action": "RESOURCE_SHARED",
                    "resource_type": req.resource_type.value,
                    "resource_id": req.resource_id,
                    "recipient_type": req.recipient_type.value,
                    "recipient_id": req.recipient_id,
                    "permission": req.permission.value,
                },
            )
        )

        self._collab_repo.record_activity(
            CollaborationActivityEvent(
                workspace_id=ws_id,
                project_id=proj_id,
                actor_user_id=shared_by_user_id,
                event_type=CollaborationEventType.RESOURCE_SHARED,
                resource_type=req.resource_type,
                resource_id=req.resource_id,
                details={
                    "share_id": share.share_id,
                    "recipient_id": req.recipient_id,
                    "permission": req.permission.value,
                },
            )
        )

        # 5. In-app notification for recipient user
        if req.recipient_type == ShareRecipientType.USER:
            self._collab_repo.save_notification(
                Notification(
                    recipient_user_id=req.recipient_id,
                    type=NotificationType.SHARE_RECEIVED,
                    title=f"New {req.resource_type.value} shared with you",
                    message=f"{sharer_name} shared '{res_name}' with you with {req.permission.value} access.",
                    related_resource_type=req.resource_type,
                    related_resource_id=req.resource_id,
                    action_url=f"/dataset/{req.resource_id}" if req.resource_type == ResourceType.DATASET else f"/dashboard",
                    metadata={"share_id": share.share_id},
                )
            )
            # Phase 19 Enterprise Event Dispatch
            event_dispatcher.create_and_dispatch(
                event_type=ApplicationEventType.RESOURCE_SHARED,
                actor_user_id=shared_by_user_id,
                workspace_id=share.workspace_id,
                project_id=share.project_id,
                resource_type=req.resource_type.value,
                resource_id=req.resource_id,
                metadata={
                    "recipient_user_id": req.recipient_id,
                    "resource_name": res_name,
                    "permission": req.permission.value,
                    "share_id": share.share_id,
                },
            )

        logger.info(
            f"User {shared_by_user_id} shared {req.resource_type.value} '{req.resource_id}' "
            f"with {req.recipient_type.value} {req.recipient_id} ({req.permission.value})"
        )
        return share

    def update_share(
        self,
        share_id: str,
        updater_user_id: str,
        req: UpdateShareRequest,
    ) -> ResourceShare:
        """Updates share permission or expiration window."""
        share = self._collab_repo.get_share(share_id)
        if not share:
            raise HTTPException(status_code=404, detail="Share record not found")

        eff = self._access.resolve_effective_access(updater_user_id, share.resource_type, share.resource_id)
        if not eff.can_edit:
            raise HTTPException(status_code=403, detail="Permission denied to modify share")

        if req.permission:
            share.permission = req.permission
        if req.expires_at is not None:
            share.expires_at = req.expires_at

        share.updated_at = datetime.now(timezone.utc).isoformat()
        self._collab_repo.save_share(share)
        self._access.invalidate_cache(user_id=share.recipient_id, resource_id=share.resource_id)

        self._collab_repo.record_activity(
            CollaborationActivityEvent(
                workspace_id=share.workspace_id,
                project_id=share.project_id,
                actor_user_id=updater_user_id,
                event_type=CollaborationEventType.RESOURCE_SHARE_UPDATED,
                resource_type=share.resource_type,
                resource_id=share.resource_id,
                details={"share_id": share.share_id, "permission": share.permission.value},
            )
        )
        return share

    def revoke_share(self, share_id: str, revoker_user_id: str) -> ResourceShare:
        """Revokes a direct resource share, immediately terminating recipient access."""
        share = self._collab_repo.get_share(share_id)
        if not share:
            raise HTTPException(status_code=404, detail="Share record not found")

        eff = self._access.resolve_effective_access(revoker_user_id, share.resource_type, share.resource_id)
        if not eff.can_edit:
            raise HTTPException(status_code=403, detail="Permission denied to revoke share")

        share.status = ShareStatus.REVOKED
        share.revoked_at = datetime.now(timezone.utc).isoformat()
        self._collab_repo.save_share(share)
        self._access.invalidate_cache(user_id=share.recipient_id, resource_id=share.resource_id)

        # Notify recipient that access was revoked
        if share.recipient_type == ShareRecipientType.USER:
            self._collab_repo.save_notification(
                Notification(
                    recipient_user_id=share.recipient_id,
                    type=NotificationType.ACCESS_REVOKED,
                    title="Access Revoked",
                    message=f"Your {share.permission.value} access to {share.resource_type.value} has been revoked.",
                    related_resource_type=share.resource_type,
                    related_resource_id=share.resource_id,
                )
            )
            # Phase 19 Enterprise Event Dispatch
            event_dispatcher.create_and_dispatch(
                event_type=ApplicationEventType.RESOURCE_SHARE_REVOKED,
                actor_user_id=revoker_user_id,
                workspace_id=share.workspace_id,
                project_id=share.project_id,
                resource_type=share.resource_type.value,
                resource_id=share.resource_id,
                metadata={
                    "recipient_user_id": share.recipient_id,
                    "resource_name": share.resource_id,
                    "share_id": share.share_id,
                },
            )

        self._collab_repo.record_activity(
            CollaborationActivityEvent(
                workspace_id=share.workspace_id,
                project_id=share.project_id,
                actor_user_id=revoker_user_id,
                event_type=CollaborationEventType.RESOURCE_SHARE_REVOKED,
                resource_type=share.resource_type,
                resource_id=share.resource_id,
                details={"share_id": share.share_id, "recipient_id": share.recipient_id},
            )
        )
        return share

    def create_share_link(
        self,
        created_by_user_id: str,
        req: CreateShareLinkRequest,
    ) -> Tuple[ShareLink, str]:
        """
        Creates an internal or public share link with a cryptographically secure token.
        Returns the link and full share URL.
        """
        ws_id, proj_id, _ = self._resolve_resource_context(req.resource_type, req.resource_id)

        eff = self._access.resolve_effective_access(created_by_user_id, req.resource_type, req.resource_id)
        if not eff.can_edit:
            raise HTTPException(status_code=403, detail="Permission denied to generate share links for this resource")

        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_session_token(raw_token)

        expires_at = None
        if req.expires_in_days:
            expires_at = (datetime.now(timezone.utc) + timedelta(days=req.expires_in_days)).isoformat()

        link = ShareLink(
            token_hash=token_hash,
            resource_type=req.resource_type,
            resource_id=req.resource_id,
            workspace_id=ws_id,
            project_id=proj_id,
            created_by_user_id=created_by_user_id,
            link_mode=req.link_mode,
            permission=req.permission,
            status=ShareStatus.ACTIVE,
            expires_at=expires_at,
        )
        self._collab_repo.save_share_link(link)
        self._access.invalidate_cache(resource_id=req.resource_id)

        share_url = f"/shared/{raw_token}"

        self._collab_repo.record_activity(
            CollaborationActivityEvent(
                workspace_id=ws_id,
                project_id=proj_id,
                actor_user_id=created_by_user_id,
                event_type=CollaborationEventType.SHARE_LINK_CREATED,
                resource_type=req.resource_type,
                resource_id=req.resource_id,
                details={
                    "share_link_id": link.share_link_id,
                    "link_mode": req.link_mode.value,
                    "permission": req.permission.value,
                },
            )
        )

        return link, share_url

    def revoke_share_link(self, share_link_id: str, revoker_user_id: str) -> ShareLink:
        """Revokes a share link immediately."""
        link = self._collab_repo.get_share_link(share_link_id)
        if not link:
            raise HTTPException(status_code=404, detail="Share link not found")

        eff = self._access.resolve_effective_access(revoker_user_id, link.resource_type, link.resource_id)
        if not eff.can_edit:
            raise HTTPException(status_code=403, detail="Permission denied to revoke share link")

        link.status = ShareStatus.REVOKED
        link.revoked_at = datetime.now(timezone.utc).isoformat()
        self._collab_repo.save_share_link(link)
        self._access.invalidate_cache(resource_id=link.resource_id)

        self._collab_repo.record_activity(
            CollaborationActivityEvent(
                workspace_id=link.workspace_id,
                project_id=link.project_id,
                actor_user_id=revoker_user_id,
                event_type=CollaborationEventType.SHARE_LINK_REVOKED,
                resource_type=link.resource_type,
                resource_id=link.resource_id,
                details={"share_link_id": link.share_link_id},
            )
        )
        return link

    def list_resource_access(
        self,
        resource_type: ResourceType,
        resource_id: str,
        requesting_user_id: str,
    ) -> ResourceAccessSummary:
        """Compiles complete access summary for the 'Manage Access' dialog."""
        ws_id, proj_id, _ = self._resolve_resource_context(resource_type, resource_id)

        # 1. Caller must have at least VIEW access to view access list
        eff_caller = self._access.resolve_effective_access(requesting_user_id, resource_type, resource_id)
        if not eff_caller.can_view:
            raise HTTPException(status_code=403, detail="Permission denied to inspect resource access")

        # 2. Direct Shares
        direct_shares = self._collab_repo.list_shares_for_resource(resource_id)
        direct_responses = []
        for s in direct_shares:
            sharer = self._auth_repo.get_user(s.shared_by_user_id)
            recip_name = s.recipient_id
            if s.recipient_type == ShareRecipientType.USER:
                u = self._auth_repo.get_user(s.recipient_id)
                if u:
                    recip_name = u.display_name
            elif s.recipient_type == ShareRecipientType.PROJECT:
                p = self._ws_repo.get_project(s.recipient_id)
                if p:
                    recip_name = p.name

            direct_responses.append(
                ResourceShareResponse(
                    share_id=s.share_id,
                    resource_type=s.resource_type,
                    resource_id=s.resource_id,
                    workspace_id=s.workspace_id,
                    project_id=s.project_id,
                    shared_by_user_id=s.shared_by_user_id,
                    shared_by_name=sharer.display_name if sharer else "User",
                    recipient_type=s.recipient_type,
                    recipient_id=s.recipient_id,
                    recipient_name=recip_name,
                    permission=s.permission,
                    status=s.status,
                    created_at=s.created_at,
                    expires_at=s.expires_at,
                )
            )

        # 3. Inherited Workspace Members
        ws_members = self._auth_repo.list_workspace_members(ws_id)
        inherited_ws = []
        for m in ws_members:
            u = self._auth_repo.get_user(m.user_id)
            if u:
                inherited_ws.append({
                    "user_id": u.user_id,
                    "display_name": u.display_name,
                    "email": u.email,
                    "role": m.role.value,
                    "source": "WORKSPACE_MEMBERSHIP",
                })

        # 4. Inherited Project Members
        inherited_proj = []
        if proj_id:
            p_members = self._auth_repo.list_project_members(proj_id)
            for pm in p_members:
                u = self._auth_repo.get_user(pm.user_id)
                if u:
                    inherited_proj.append({
                        "user_id": u.user_id,
                        "display_name": u.display_name,
                        "email": u.email,
                        "role": pm.role.value,
                        "source": "PROJECT_MEMBERSHIP",
                    })

        # 5. Active Share Links
        links = self._collab_repo.list_share_links_for_resource(resource_id)
        link_responses = [
            ShareLinkResponse(
                share_link_id=l.share_link_id,
                resource_type=l.resource_type,
                resource_id=l.resource_id,
                link_mode=l.link_mode,
                permission=l.permission,
                status=l.status,
                created_at=l.created_at,
                expires_at=l.expires_at,
                access_count=l.access_count,
            )
            for l in links
        ]

        return ResourceAccessSummary(
            resource_type=resource_type,
            resource_id=resource_id,
            workspace_id=ws_id,
            project_id=proj_id,
            direct_shares=direct_responses,
            inherited_workspace_access=inherited_ws,
            inherited_project_access=inherited_proj,
            active_share_links=link_responses,
            effective_access=eff_caller,
        )


# Global singleton instance
share_service = ShareService()
