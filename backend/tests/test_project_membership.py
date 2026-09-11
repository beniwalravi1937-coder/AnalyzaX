"""
Tests for Project Memberships & Boundaries (Phase 18).
Validates explicit project role overrides and enforces the core workspace boundary invariant.
"""

import pytest
from fastapi import HTTPException

from backend.app.engines.auth.models import MembershipStatus, RoleName
from backend.app.engines.auth.permissions import Permission
from backend.tests.test_collaboration_fixtures import CollabTestContext


def test_add_workspace_member_to_project():
    ctx = CollabTestContext()
    try:
        # User B is in Workspace A, adding to Project A as EDITOR
        member = ctx.project_access.add_project_member(
            project_id=ctx.proj_a.project_id,
            target_user_id=ctx.user_b.user_id,
            role=RoleName.EDITOR,
            requesting_user_id=ctx.user_a.user_id,
        )
        assert member.project_id == ctx.proj_a.project_id
        assert member.user_id == ctx.user_b.user_id
        assert member.role == RoleName.EDITOR
        assert member.status == MembershipStatus.ACTIVE
    finally:
        ctx.cleanup()


def test_project_membership_invariant_rejects_non_workspace_user():
    ctx = CollabTestContext()
    try:
        # user_external is NOT a member of Workspace A!
        # Attempting to add directly to Project A must be blocked with 400
        with pytest.raises(HTTPException) as exc:
            ctx.project_access.add_project_member(
                project_id=ctx.proj_a.project_id,
                target_user_id=ctx.user_external.user_id,
                role=RoleName.VIEWER,
                requesting_user_id=ctx.user_a.user_id,
            )
        assert exc.value.status_code == 400
        assert "active member of the workspace" in exc.value.detail.lower()
    finally:
        ctx.cleanup()


def test_project_role_override_and_project_isolation():
    ctx = CollabTestContext()
    try:
        # User C is VIEWER in Workspace A (cannot edit datasets)
        assert ctx.authz.can(ctx.user_c.user_id, Permission.DATASET_UPDATE, workspace_id=ctx.ws_a.workspace_id, project_id=ctx.proj_a.project_id) is False

        # Explicitly grant User C role of EDITOR in Project A
        ctx.project_access.add_project_member(
            project_id=ctx.proj_a.project_id,
            target_user_id=ctx.user_c.user_id,
            role=RoleName.EDITOR,
            requesting_user_id=ctx.user_a.user_id,
        )

        # In Project A: User C can now edit!
        assert ctx.authz.can(ctx.user_c.user_id, Permission.DATASET_UPDATE, workspace_id=ctx.ws_a.workspace_id, project_id=ctx.proj_a.project_id) is True

        # In Project B: User C is NOT a project editor, still inherited VIEWER!
        assert ctx.authz.can(ctx.user_c.user_id, Permission.DATASET_UPDATE, workspace_id=ctx.ws_a.workspace_id, project_id=ctx.proj_b.project_id) is False
    finally:
        ctx.cleanup()


def test_remove_project_member_reverts_to_workspace_role():
    ctx = CollabTestContext()
    try:
        # Grant User C EDITOR in Project A
        ctx.project_access.add_project_member(
            project_id=ctx.proj_a.project_id,
            target_user_id=ctx.user_c.user_id,
            role=RoleName.EDITOR,
            requesting_user_id=ctx.user_a.user_id,
        )
        assert ctx.authz.can(ctx.user_c.user_id, Permission.DATASET_UPDATE, workspace_id=ctx.ws_a.workspace_id, project_id=ctx.proj_a.project_id) is True

        # Remove User C from Project A
        ctx.project_access.remove_project_member(
            project_id=ctx.proj_a.project_id,
            target_user_id=ctx.user_c.user_id,
            requesting_user_id=ctx.user_a.user_id,
        )

        # Permission reverts to inherited workspace role (VIEWER) -> cannot edit
        assert ctx.authz.can(ctx.user_c.user_id, Permission.DATASET_UPDATE, workspace_id=ctx.ws_a.workspace_id, project_id=ctx.proj_a.project_id) is False
    finally:
        ctx.cleanup()
