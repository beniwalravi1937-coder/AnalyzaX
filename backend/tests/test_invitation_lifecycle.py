"""
Tests for Workspace Invitation Lifecycle (Phase 18).
Validates token entropy, single-use, hash verification, acceptance, resend, and revocation.
"""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi import HTTPException

from backend.app.engines.auth.crypto import hash_session_token
from backend.app.engines.auth.models import MembershipStatus, RoleName
from backend.app.engines.collaboration.models import (
    CreateInvitationRequest,
    InvitationStatus,
)
from backend.tests.test_collaboration_fixtures import CollabTestContext


def test_invitation_creation_and_hash_storage():
    ctx = CollabTestContext()
    try:
        req = CreateInvitationRequest(
            email="new_colleague@analyzax.local",
            intended_role=RoleName.ANALYST,
            expires_in_days=7,
        )
        invitation, raw_token = ctx.inv_service.create_invitation(
            workspace_id=ctx.ws_a.workspace_id,
            invited_by_user_id=ctx.user_a.user_id,
            req=req,
        )

        assert invitation.status == InvitationStatus.PENDING
        assert invitation.intended_role == RoleName.ANALYST
        assert invitation.email == "new_colleague@analyzax.local"
        assert len(raw_token) >= 32

        # Verify token_hash matches SHA-256(raw_token)
        expected_hash = hash_session_token(raw_token)
        assert invitation.token_hash == expected_hash

        # Verify raw token is NOT stored anywhere in the repository
        stored_inv = ctx.collab_repo.get_invitation(invitation.invitation_id)
        assert stored_inv is not None
        assert stored_inv.token_hash == expected_hash
        assert not hasattr(stored_inv, "raw_token")
    finally:
        ctx.cleanup()


def test_invitation_unauthorized_creator_denied():
    ctx = CollabTestContext()
    try:
        req = CreateInvitationRequest(
            email="victim@analyzax.local",
            intended_role=RoleName.ADMIN,
        )
        # User C is VIEWER and has no workspace:members:manage permission
        with pytest.raises(HTTPException) as exc:
            ctx.inv_service.create_invitation(
                workspace_id=ctx.ws_a.workspace_id,
                invited_by_user_id=ctx.user_c.user_id,
                req=req,
            )
        assert exc.value.status_code == 403
    finally:
        ctx.cleanup()


def test_invitation_verification_public_preview():
    ctx = CollabTestContext()
    try:
        req = CreateInvitationRequest(
            email="analyst_jane@analyzax.local",
            intended_role=RoleName.ANALYST,
        )
        invitation, raw_token = ctx.inv_service.create_invitation(
            workspace_id=ctx.ws_a.workspace_id,
            invited_by_user_id=ctx.user_a.user_id,
            req=req,
        )

        preview = ctx.inv_service.verify_invitation(raw_token)
        assert preview.invitation_id == invitation.invitation_id
        assert preview.workspace_name == "Workspace A"
        assert preview.email == "analyst_jane@analyzax.local"
        assert preview.intended_role == RoleName.ANALYST
        assert preview.is_expired is False
    finally:
        ctx.cleanup()


def test_invitation_acceptance_grants_membership():
    ctx = CollabTestContext()
    try:
        req = CreateInvitationRequest(
            email="eve@external.local",
            intended_role=RoleName.EDITOR,
        )
        invitation, raw_token = ctx.inv_service.create_invitation(
            workspace_id=ctx.ws_a.workspace_id,
            invited_by_user_id=ctx.user_a.user_id,
            req=req,
        )

        # Eve has an account (user_external) and accepts
        member = ctx.inv_service.accept_invitation(raw_token, ctx.user_external.user_id)
        assert member.workspace_id == ctx.ws_a.workspace_id
        assert member.user_id == ctx.user_external.user_id
        assert member.role == RoleName.EDITOR
        assert member.status == MembershipStatus.ACTIVE

        # Invitation marked ACCEPTED
        updated_inv = ctx.collab_repo.get_invitation(invitation.invitation_id)
        assert updated_inv.status == InvitationStatus.ACCEPTED
        assert updated_inv.accepted_at is not None

        # Verify Eve now has active membership in auth_repo
        m = ctx.auth_repo.get_workspace_member(ctx.ws_a.workspace_id, ctx.user_external.user_id)
        assert m is not None
        assert m.role == RoleName.EDITOR
    finally:
        ctx.cleanup()


def test_invitation_single_use_enforcement():
    ctx = CollabTestContext()
    try:
        req = CreateInvitationRequest(
            email="eve@external.local",
            intended_role=RoleName.VIEWER,
        )
        _, raw_token = ctx.inv_service.create_invitation(
            workspace_id=ctx.ws_a.workspace_id,
            invited_by_user_id=ctx.user_a.user_id,
            req=req,
        )

        # First acceptance succeeds
        ctx.inv_service.accept_invitation(raw_token, ctx.user_external.user_id)

        # Second acceptance attempt must fail
        with pytest.raises(HTTPException) as exc:
            ctx.inv_service.accept_invitation(raw_token, ctx.user_external.user_id)
        assert exc.value.status_code in (400, 410)
    finally:
        ctx.cleanup()


def test_invitation_expired_rejection():
    ctx = CollabTestContext()
    try:
        req = CreateInvitationRequest(
            email="late_invitee@analyzax.local",
            intended_role=RoleName.VIEWER,
            expires_in_days=1,
        )
        invitation, raw_token = ctx.inv_service.create_invitation(
            workspace_id=ctx.ws_a.workspace_id,
            invited_by_user_id=ctx.user_a.user_id,
            req=req,
        )

        # Force expiration
        invitation.expires_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        ctx.collab_repo.save_invitation(invitation)

        # Verification fails
        with pytest.raises(HTTPException) as exc_v:
            ctx.inv_service.verify_invitation(raw_token)
        assert exc_v.value.status_code == 410

        # Acceptance fails
        with pytest.raises(HTTPException) as exc_a:
            ctx.inv_service.accept_invitation(raw_token, ctx.user_external.user_id)
        assert exc_a.value.status_code == 410
    finally:
        ctx.cleanup()


def test_invitation_revocation_and_resend():
    ctx = CollabTestContext()
    try:
        req = CreateInvitationRequest(
            email="temp_user@analyzax.local",
            intended_role=RoleName.ANALYST,
        )
        invitation, raw_token_1 = ctx.inv_service.create_invitation(
            workspace_id=ctx.ws_a.workspace_id,
            invited_by_user_id=ctx.user_a.user_id,
            req=req,
        )

        # Revoke invitation
        ctx.inv_service.revoke_invitation(invitation.invitation_id, ctx.user_a.user_id)
        revoked_inv = ctx.collab_repo.get_invitation(invitation.invitation_id)
        assert revoked_inv.status == InvitationStatus.REVOKED

        # Attempt to accept revoked token fails
        with pytest.raises(HTTPException) as exc:
            ctx.inv_service.accept_invitation(raw_token_1, ctx.user_external.user_id)
        assert exc.value.status_code in (400, 410)

        # Resend invitation creates a new cryptographic token and reactivates
        resent_inv, raw_token_2 = ctx.inv_service.resend_invitation(
            invitation.invitation_id,
            ctx.user_a.user_id,
        )
        assert resent_inv.status == InvitationStatus.PENDING
        assert raw_token_2 != raw_token_1

        # Old token still fails
        with pytest.raises(HTTPException):
            ctx.inv_service.accept_invitation(raw_token_1, ctx.user_external.user_id)

        # New token succeeds
        member = ctx.inv_service.accept_invitation(raw_token_2, ctx.user_external.user_id)
        assert member.role == RoleName.ANALYST
    finally:
        ctx.cleanup()
