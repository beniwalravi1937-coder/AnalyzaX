"""
Tests for Resource Sharing & Permission Elevation (Phase 18).
Validates direct resource sharing, permission scoping, expiration, and revocation.
"""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi import HTTPException

from backend.app.engines.collaboration.models import (
    CreateShareRequest,
    ResourceType,
    SharePermission,
    ShareRecipientType,
    ShareStatus,
    UpdateShareRequest,
)
from backend.tests.test_collaboration_fixtures import CollabTestContext


def test_create_direct_resource_share():
    ctx = CollabTestContext()
    try:
        req = CreateShareRequest(
            resource_type=ResourceType.DASHBOARD,
            resource_id=ctx.dash_a.asset_id,
            recipient_type=ShareRecipientType.USER,
            recipient_id=ctx.user_c.user_id,
            permission=SharePermission.VIEW,
        )
        share = ctx.share_service.create_share(
            shared_by_user_id=ctx.user_a.user_id,
            req=req,
        )
        assert share.resource_id == ctx.dash_a.asset_id
        assert share.recipient_id == ctx.user_c.user_id
        assert share.permission == SharePermission.VIEW
        assert share.status == ShareStatus.ACTIVE

        # Check effective access
        eff = ctx.access.resolve_effective_access(
            user_id=ctx.user_c.user_id,
            resource_type=ResourceType.DASHBOARD,
            resource_id=ctx.dash_a.asset_id,
        )
        assert eff.can_view is True
        assert eff.can_edit is False
        assert eff.can_export is False
    finally:
        ctx.cleanup()


def test_share_permission_upgrade_and_revocation():
    ctx = CollabTestContext()
    try:
        # 1. Share with VIEW
        req = CreateShareRequest(
            resource_type=ResourceType.DASHBOARD,
            resource_id=ctx.dash_a.asset_id,
            recipient_type=ShareRecipientType.USER,
            recipient_id=ctx.user_c.user_id,
            permission=SharePermission.VIEW,
        )
        share = ctx.share_service.create_share(ctx.user_a.user_id, req)

        eff_1 = ctx.access.resolve_effective_access(ctx.user_c.user_id, ResourceType.DASHBOARD, ctx.dash_a.asset_id)
        assert eff_1.can_export is False

        # 2. Upgrade to EXPORT
        ctx.share_service.update_share(
            share.share_id,
            updater_user_id=ctx.user_a.user_id,
            req=UpdateShareRequest(permission=SharePermission.EXPORT),
        )

        eff_2 = ctx.access.resolve_effective_access(ctx.user_c.user_id, ResourceType.DASHBOARD, ctx.dash_a.asset_id)
        assert eff_2.can_view is True
        assert eff_2.can_export is True
        assert eff_2.can_edit is False

        # 3. Revoke share
        ctx.share_service.revoke_share(share.share_id, ctx.user_a.user_id)

        # User C is still a workspace member (VIEWER) so can_view remains, but can_export is gone!
        eff_3 = ctx.access.resolve_effective_access(ctx.user_c.user_id, ResourceType.DASHBOARD, ctx.dash_a.asset_id)
        assert eff_3.can_export is False
    finally:
        ctx.cleanup()


def test_expiring_resource_share():
    ctx = CollabTestContext()
    try:
        # Share with external user with explicit expiration
        req = CreateShareRequest(
            resource_type=ResourceType.REPORT,
            resource_id=ctx.report_a.asset_id,
            recipient_type=ShareRecipientType.USER,
            recipient_id=ctx.user_external.user_id,
            permission=SharePermission.EXPORT,
            expires_in_days=1,
        )
        share = ctx.share_service.create_share(ctx.user_a.user_id, req)

        # Access valid initially
        eff_init = ctx.access.resolve_effective_access(ctx.user_external.user_id, ResourceType.REPORT, ctx.report_a.asset_id)
        assert eff_init.can_view is True
        assert eff_init.can_export is True

        # Advance expiration to past
        share.expires_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        ctx.collab_repo.save_share(share)
        ctx.access.invalidate_cache()

        # Access immediately denied after expiry
        eff_expired = ctx.access.resolve_effective_access(ctx.user_external.user_id, ResourceType.REPORT, ctx.report_a.asset_id)
        assert eff_expired.can_view is False
        assert eff_expired.can_export is False
    finally:
        ctx.cleanup()


def test_unauthorized_user_cannot_create_share():
    ctx = CollabTestContext()
    try:
        # User C is VIEWER and has no edit authority
        req = CreateShareRequest(
            resource_type=ResourceType.DASHBOARD,
            resource_id=ctx.dash_a.asset_id,
            recipient_type=ShareRecipientType.USER,
            recipient_id=ctx.user_external.user_id,
            permission=SharePermission.VIEW,
        )
        with pytest.raises(HTTPException) as exc:
            ctx.share_service.create_share(ctx.user_c.user_id, req)
        assert exc.value.status_code == 403
    finally:
        ctx.cleanup()
