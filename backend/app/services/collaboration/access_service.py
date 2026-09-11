"""
Centralized Effective Access Policy & Resolution Service for Phase 18.
Evaluates multi-source access inheritance:
Workspace Role -> Project Role -> Direct Resource Share -> Share Links.
Ensures security ceilings, version boundaries, and strict server-side enforcement.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend.app.core.logging import logger
from backend.app.engines.auth.crypto import hash_session_token
from backend.app.engines.auth.models import MembershipStatus, RoleName, UserStatus
from backend.app.engines.auth.permissions import Permission, get_role_permissions
from backend.app.engines.auth.repository import AuthRepository, auth_repo
from backend.app.engines.collaboration.models import (
    EffectiveAccess,
    ResourceType,
    ShareLinkMode,
    SharePermission,
    ShareRecipientType,
    ShareStatus,
)
from backend.app.engines.collaboration.repository import CollaborationRepository, collaboration_repo
from backend.app.engines.workspace.repository import WorkspaceRepository, workspace_repo


class AccessService:
    """
    Central authority for resolving effective permissions on any analytical resource.
    Rule: Never compute permissions on the frontend; evaluate centrally.
    """

    def __init__(
        self,
        collab_repository: Optional[CollaborationRepository] = None,
        auth_repository: Optional[AuthRepository] = None,
        workspace_repository: Optional[WorkspaceRepository] = None,
    ):
        self._collab_repo = collab_repository or collaboration_repo
        self._auth_repo = auth_repository or auth_repo
        self._ws_repo = workspace_repository or workspace_repo
        self._cache: Dict[str, Tuple[EffectiveAccess, float]] = {}

    def _cache_key(
        self,
        user_id: Optional[str],
        resource_type: ResourceType,
        resource_id: str,
        token_hash: Optional[str],
    ) -> str:
        return f"{user_id or 'anon'}:{resource_type.value}:{resource_id}:{token_hash or 'none'}"

    def invalidate_cache(self, user_id: Optional[str] = None, resource_id: Optional[str] = None) -> None:
        """Clears cached effective access entries matching criteria."""
        if not user_id and not resource_id:
            self._cache.clear()
            return

        keys_to_remove = []
        for k in self._cache.keys():
            parts = k.split(":")
            k_user = parts[0]
            k_res = parts[2]
            if user_id and k_user == user_id:
                keys_to_remove.append(k)
            elif resource_id and k_res == resource_id:
                keys_to_remove.append(k)

        for k in keys_to_remove:
            self._cache.pop(k, None)

    def resolve_effective_access(
        self,
        user_id: Optional[str],
        resource_type: ResourceType,
        resource_id: str,
        raw_share_token: Optional[str] = None,
    ) -> EffectiveAccess:
        """
        Calculates whether a user (or public link bearer) has VIEW, EDIT, or EXPORT
        authority over resource_id.
        """
        token_hash = hash_session_token(raw_share_token) if raw_share_token else None
        cache_k = self._cache_key(user_id, resource_type, resource_id, token_hash)
        cached = self._cache.get(cache_k)
        now_ts = datetime.now(timezone.utc).timestamp()
        if cached and cached[1] > now_ts:
            return cached[0]

        can_view = False
        can_edit = False
        can_export = False
        sources: List[str] = []
        restrictions: List[str] = []
        earliest_expiry: Optional[str] = None

        # ─────────────────────────────────────────────────────────────
        # 1. Evaluate Share Link (if token provided)
        # ─────────────────────────────────────────────────────────────
        if token_hash:
            link = self._collab_repo.get_share_link_by_token_hash(token_hash)
            if link and link.status == ShareStatus.ACTIVE:
                # Check link applies to this resource
                if link.resource_id == resource_id or (
                    resource_type == ResourceType.DATASET_VERSION and link.resource_id in resource_id
                ):
                    if link.link_mode == ShareLinkMode.PUBLIC_READ_ONLY:
                        can_view = True
                        if link.permission == SharePermission.EXPORT:
                            can_export = True
                        sources.append(f"PUBLIC_SHARE_LINK ({link.permission.value})")
                        if link.expires_at:
                            earliest_expiry = link.expires_at

                        result = EffectiveAccess(
                            can_view=can_view,
                            can_edit=False,  # Public links NEVER grant EDIT
                            can_export=can_export,
                            access_sources=sources,
                            effective_permission=link.permission,
                            expires_at=earliest_expiry,
                            restrictions=["RESTRICTED_PUBLIC_VIEW"],
                        )
                        self._cache[cache_k] = (result, now_ts + 60.0)
                        return result

                    elif link.link_mode == ShareLinkMode.INTERNAL_AUTHENTICATED:
                        if user_id:
                            user = self._auth_repo.get_user(user_id)
                            if user and user.status == UserStatus.ACTIVE:
                                can_view = True
                                if link.permission in (SharePermission.EDIT,):
                                    can_edit = True
                                if link.permission in (SharePermission.EXPORT, SharePermission.EDIT):
                                    can_export = True
                                sources.append(f"INTERNAL_SHARE_LINK ({link.permission.value})")
                                if link.expires_at:
                                    earliest_expiry = link.expires_at

        # If no user_id and no valid public link -> Denied
        if not user_id:
            result = EffectiveAccess(can_view=False, can_edit=False, can_export=False, restrictions=["UNAUTHENTICATED"])
            return result

        user = self._auth_repo.get_user(user_id)
        if not user or user.status != UserStatus.ACTIVE:
            result = EffectiveAccess(can_view=False, can_edit=False, can_export=False, restrictions=["USER_INACTIVE"])
            return result

        # ─────────────────────────────────────────────────────────────
        # 2. Resolve Workspace & Project Context from Resource
        # ─────────────────────────────────────────────────────────────
        workspace_id: Optional[str] = None
        project_id: Optional[str] = None

        # Check if resource is a workspace itself
        ws = self._ws_repo.get_workspace(resource_id)
        if ws:
            workspace_id = ws.workspace_id
        else:
            # Check if resource is a project itself
            proj = self._ws_repo.get_project(resource_id)
            if proj:
                workspace_id = proj.workspace_id
                project_id = proj.project_id
            else:
                # Check if resource is an asset (dataset, dashboard, report, etc.)
                asset = self._ws_repo.get_asset(resource_id) or self._ws_repo.find_asset_by_source_id(resource_id)
                if asset:
                    workspace_id = asset.workspace_id
                    project_id = asset.project_id

        # ─────────────────────────────────────────────────────────────
        # 3. Direct Resource Shares for this User
        # ─────────────────────────────────────────────────────────────
        direct_share = self._collab_repo.find_direct_share(
            resource_id=resource_id,
            recipient_id=user_id,
            recipient_type=ShareRecipientType.USER,
        )
        if direct_share and direct_share.status == ShareStatus.ACTIVE:
            can_view = True
            if direct_share.permission in (SharePermission.EDIT,):
                can_edit = True
            if direct_share.permission in (SharePermission.EXPORT, SharePermission.EDIT):
                can_export = True
            sources.append(f"DIRECT_SHARE ({direct_share.permission.value})")
            if direct_share.expires_at:
                earliest_expiry = direct_share.expires_at

        # ─────────────────────────────────────────────────────────────
        # 4. Workspace & Project Role Hierarchy
        # ─────────────────────────────────────────────────────────────
        if workspace_id:
            ws_member = self._auth_repo.get_workspace_member(workspace_id, user_id)
            if ws_member and ws_member.status == MembershipStatus.ACTIVE:
                effective_role = ws_member.role

                # If resource is inside a project, check for explicit project membership override
                if project_id:
                    proj_member = self._auth_repo.get_project_member(project_id, user_id)
                    if proj_member:
                        if proj_member.status == MembershipStatus.ACTIVE:
                            effective_role = proj_member.role
                            sources.append(f"PROJECT_ROLE ({proj_member.role.value})")
                        elif proj_member.status in (MembershipStatus.SUSPENDED, MembershipStatus.REMOVED):
                            effective_role = None
                            restrictions.append("PROJECT_MEMBERSHIP_SUSPENDED")
                    else:
                        sources.append(f"WORKSPACE_INHERITED_ROLE ({ws_member.role.value})")
                else:
                    sources.append(f"WORKSPACE_ROLE ({ws_member.role.value})")

                if effective_role:
                    # Map role to capabilities
                    if effective_role in (RoleName.OWNER, RoleName.ADMIN):
                        can_view = True
                        can_edit = True
                        can_export = True
                    elif effective_role == RoleName.EDITOR:
                        can_view = True
                        can_edit = True
                        can_export = True
                    elif effective_role == RoleName.ANALYST:
                        can_view = True
                        can_edit = False
                        can_export = True
                    elif effective_role == RoleName.VIEWER:
                        can_view = True
                        can_edit = False
                        # VIEWER has export = False by default unless granted by direct share
            else:
                # User is NOT an active member of this workspace!
                if direct_share:
                    # User accessed resource via direct share from outside the workspace
                    restrictions.append("EXTERNAL_USER_SHARE (Limited strictly to shared resource)")
                else:
                    # Cannot access workspace resources without membership or explicit share
                    can_view = False
                    can_edit = False
                    can_export = False
                    restrictions.append("NO_WORKSPACE_MEMBERSHIP")

        # ─────────────────────────────────────────────────────────────
        # 5. Determine Effective Permission
        # ─────────────────────────────────────────────────────────────
        eff_perm: Optional[SharePermission] = None
        if can_edit:
            eff_perm = SharePermission.EDIT
        elif can_export:
            eff_perm = SharePermission.EXPORT
        elif can_view:
            eff_perm = SharePermission.VIEW

        result = EffectiveAccess(
            can_view=can_view,
            can_edit=can_edit,
            can_export=can_export,
            access_sources=sources,
            effective_permission=eff_perm,
            expires_at=earliest_expiry,
            restrictions=restrictions,
        )
        self._cache[cache_k] = (result, now_ts + 60.0)
        return result


# Global singleton instance
access_service = AccessService()
