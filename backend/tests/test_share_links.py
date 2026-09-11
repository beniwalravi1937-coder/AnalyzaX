"""
Tests for Internal and Public Share Links (Phase 18).
Validates token generation, SHA-256 hash storage, access counts, and restricted public views.
"""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi import HTTPException

from backend.app.engines.auth.crypto import hash_session_token
from backend.app.engines.collaboration.models import (
    CreateShareLinkRequest,
    ResourceType,
    ShareLinkMode,
    SharePermission,
    ShareStatus,
)
from backend.tests.test_collaboration_fixtures import CollabTestContext


def test_internal_authenticated_share_link():
    ctx = CollabTestContext()
    try:
        req = CreateShareLinkRequest(
            resource_type=ResourceType.DASHBOARD,
            resource_id=ctx.dash_a.asset_id,
            link_mode=ShareLinkMode.INTERNAL_AUTHENTICATED,
            permission=SharePermission.VIEW,
            expires_in_days=7,
        )
        link, share_url = ctx.share_service.create_share_link(ctx.user_a.user_id, req)
        raw_token = share_url.split("/")[-1]

        # Verify token_hash matches SHA-256(raw_token)
        assert link.token_hash == hash_session_token(raw_token)
        assert link.status == ShareStatus.ACTIVE

        # Resolving without authentication must fail for INTERNAL_AUTHENTICATED links
        with pytest.raises(HTTPException) as exc_anon:
            ctx.shared_res.get_shared_resource(raw_token, current_user_id=None)
        assert exc_anon.value.status_code == 401

        # Resolving with authenticated user succeeds
        view = ctx.shared_res.get_shared_resource(raw_token, current_user_id=ctx.user_c.user_id)
        assert view.title == ctx.dash_a.name
        assert view.is_public is False
        assert view.permission == SharePermission.VIEW

        # Verify access count incremented
        updated_link = ctx.collab_repo.get_share_link(link.share_link_id)
        assert updated_link.access_count == 1
    finally:
        ctx.cleanup()


def test_public_read_only_share_link():
    ctx = CollabTestContext()
    try:
        req = CreateShareLinkRequest(
            resource_type=ResourceType.REPORT,
            resource_id=ctx.report_a.asset_id,
            link_mode=ShareLinkMode.PUBLIC_READ_ONLY,
            permission=SharePermission.VIEW,
            expires_in_days=14,
        )
        link, share_url = ctx.share_service.create_share_link(ctx.user_a.user_id, req)
        raw_token = share_url.split("/")[-1]

        # Resolving as anonymous user succeeds for PUBLIC_READ_ONLY links
        view = ctx.shared_res.get_shared_resource(raw_token, current_user_id=None)
        assert view.title == ctx.report_a.name
        assert view.is_public is True
        assert view.permission == SharePermission.VIEW

        # Effective access check for anonymous user via public link
        eff = ctx.access.resolve_effective_access(
            user_id=None,
            resource_type=ResourceType.REPORT,
            resource_id=ctx.report_a.asset_id,
            raw_share_token=raw_token,
        )
        assert eff.can_view is True
        assert eff.can_edit is False  # Public links never grant edit
    finally:
        ctx.cleanup()


def test_share_link_revocation():
    ctx = CollabTestContext()
    try:
        req = CreateShareLinkRequest(
            resource_type=ResourceType.DASHBOARD,
            resource_id=ctx.dash_a.asset_id,
            link_mode=ShareLinkMode.PUBLIC_READ_ONLY,
        )
        link, share_url = ctx.share_service.create_share_link(ctx.user_a.user_id, req)
        raw_token = share_url.split("/")[-1]

        # Revoke the link
        ctx.share_service.revoke_share_link(link.share_link_id, ctx.user_a.user_id)

        # Attempt to access revoked link fails
        with pytest.raises(HTTPException) as exc:
            ctx.shared_res.get_shared_resource(raw_token, current_user_id=None)
        assert exc.value.status_code in (404, 410)
    finally:
        ctx.cleanup()
