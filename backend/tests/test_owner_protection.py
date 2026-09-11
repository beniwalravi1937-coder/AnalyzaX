"""
Unit tests for Phase 17 Owner Protection (AUTH-37).
Enforces that a workspace must maintain at least one active owner.
"""

from fastapi import HTTPException
import pytest

from backend.app.engines.auth.models import RoleName, User, WorkspaceMember
from backend.app.engines.auth.repository import AuthRepository
from backend.app.engines.workspace.models import Workspace
from backend.app.engines.workspace.repository import WorkspaceRepository
from backend.app.services.auth.authorization_service import AuthorizationService
from backend.app.services.auth.membership_service import MembershipService


def test_owner_protection_guard(tmp_path):
    auth_dir = str(tmp_path / "auth")
    ws_dir = str(tmp_path / "workspace")
    auth_repo = AuthRepository(storage_dir=auth_dir)
    ws_repo = WorkspaceRepository(storage_dir=ws_dir)
    authz = AuthorizationService(auth_repository=auth_repo, workspace_repository=ws_repo)
    membership_srv = MembershipService(repository=auth_repo, authz_service=authz)

    # Setup 2 users and 1 workspace
    u1 = User(user_id="usr_owner1", email="o1@test.com", email_normalized="o1@test.com", password_hash="dummy", display_name="Owner 1")
    u2 = User(user_id="usr_member2", email="m2@test.com", email_normalized="m2@test.com", password_hash="dummy", display_name="Member 2")
    auth_repo.save_user(u1)
    auth_repo.save_user(u2)

    ws = Workspace(workspace_id="ws_prot", name="Protected WS", slug="protected-ws")
    ws_repo.save_workspace(ws)

    # User 1 is sole OWNER
    auth_repo.save_workspace_member(WorkspaceMember(workspace_id="ws_prot", user_id="usr_owner1", role=RoleName.OWNER))
    # User 2 is MEMBER
    auth_repo.save_workspace_member(WorkspaceMember(workspace_id="ws_prot", user_id="usr_member2", role=RoleName.EDITOR))

    # 1. Attempt to remove sole OWNER must FAIL
    with pytest.raises(HTTPException) as exc_info:
        membership_srv.remove_workspace_member("ws_prot", "usr_owner1", actor_user_id="usr_owner1")
    assert exc_info.value.status_code == 400
    assert "Cannot remove the last active workspace owner" in exc_info.value.detail

    # 2. Attempt to downgrade sole OWNER must FAIL
    with pytest.raises(HTTPException) as exc_info:
        membership_srv.update_workspace_member_role("ws_prot", "usr_owner1", new_role=RoleName.ADMIN, actor_user_id="usr_owner1")
    assert exc_info.value.status_code == 400
    assert "Cannot downgrade the last active workspace owner" in exc_info.value.detail

    # 3. Promote User 2 to second OWNER
    membership_srv.update_workspace_member_role("ws_prot", "usr_member2", new_role=RoleName.OWNER, actor_user_id="usr_owner1")

    # Now there are 2 active owners: downgrading User 1 succeeds
    updated = membership_srv.update_workspace_member_role("ws_prot", "usr_owner1", new_role=RoleName.ADMIN, actor_user_id="usr_member2")
    assert updated.role == RoleName.ADMIN

    # Now User 2 is the sole owner; attempting to remove User 2 must fail again
    with pytest.raises(HTTPException):
        membership_srv.remove_workspace_member("ws_prot", "usr_member2", actor_user_id="usr_member2")
