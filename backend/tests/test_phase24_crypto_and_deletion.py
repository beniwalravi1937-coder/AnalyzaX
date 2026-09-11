"""
AnalyzaX — Phase 24 Tests: AES-256-GCM Cryptography, Key Rotation & Safe Cascading Deletion / DSR.
"""

import json
import pytest

from backend.app.engines.auth.models import RoleName, User, WorkspaceMember
from backend.app.engines.auth.permissions import Permissions
from backend.app.engines.auth.repository import AuthRepository
from backend.app.engines.security.crypto import KeyManager
from backend.app.engines.workspace.models import Asset, AssetType, Project, Workspace
from backend.app.engines.workspace.repository import WorkspaceRepository
from backend.app.services.auth.authorization_service import AuthorizationService
from backend.app.services.auth.security_audit_service import SecurityAuditService
from backend.app.services.governance.deletion_service import DeletionService


def test_crypto_key_manager_aes256_gcm_and_rotation():
    # 1. Initialize KeyManager with test master secret
    km = KeyManager(master_secret="test_master_secret_with_sufficient_entropy_123")

    plaintext = "SECRET_API_KEY_OR_CREDENTIAL_DATA"
    envelope = km.encrypt(plaintext)
    assert envelope.startswith("v1:")

    # 2. Decrypt envelope
    decrypted = km.decrypt(envelope)
    assert decrypted == plaintext

    # 3. Tamper resistance: altering ciphertext raises ValueError
    parts = envelope.split(":")
    tampered_ct = parts[2][:-2] + ("aa" if not parts[2].endswith("aa") else "bb")
    tampered_envelope = f"{parts[0]}:{parts[1]}:{tampered_ct}"
    with pytest.raises(ValueError):
        km.decrypt(tampered_envelope)

    # 4. Key rotation to v2
    # Old envelope encrypted with v1 can still be decrypted using keyring
    assert km.decrypt(envelope) == plaintext

    # Re-encrypt to latest key (v2)
    new_envelope = km.rotate(envelope, target_version="v2")
    assert new_envelope.startswith("v2:")
    assert km.decrypt(new_envelope) == plaintext


def test_governance_safe_cascading_workspace_deletion(tmp_path):
    auth_dir = str(tmp_path / "auth")
    ws_dir = str(tmp_path / "workspace")
    auth_repo = AuthRepository(storage_dir=auth_dir)
    ws_repo = WorkspaceRepository(storage_dir=ws_dir)
    authz = AuthorizationService(auth_repository=auth_repo, workspace_repository=ws_repo)
    audit = SecurityAuditService()
    deletion_svc = DeletionService(
        auth_repository=auth_repo,
        workspace_repository=ws_repo,
        authz_svc=authz,
        audit_svc=audit,
    )

    # Create workspace with owner and admin
    ws = Workspace(workspace_id="ws_cascade", name="Cascade WS", slug="cascade-ws")
    ws_repo.save_workspace(ws)

    auth_repo.save_user(User(user_id="usr_owner", email="owner@ws.local", email_normalized="owner@ws.local", password_hash="hash", display_name="Owner"))
    auth_repo.save_user(User(user_id="usr_admin", email="admin@ws.local", email_normalized="admin@ws.local", password_hash="hash", display_name="Admin"))

    auth_repo.save_workspace_member(WorkspaceMember(workspace_id="ws_cascade", user_id="usr_owner", role=RoleName.OWNER))
    auth_repo.save_workspace_member(WorkspaceMember(workspace_id="ws_cascade", user_id="usr_admin", role=RoleName.ADMIN))

    # Add project and assets
    proj = Project(project_id="proj_cascade", workspace_id="ws_cascade", name="Project Cascade", slug="proj-cascade")
    ws_repo.save_project(proj)
    asset = Asset(
        asset_id="ast_cascade",
        workspace_id="ws_cascade",
        project_id="proj_cascade",
        name="Dataset Cascade",
        asset_type=AssetType.DATASET,
        source_entity_id="ds_cascade",
    )
    ws_repo.save_asset(asset)

    # 1. Non-owner (Admin) deletion attempt is blocked
    with pytest.raises(Exception) as exc:
        deletion_svc.delete_workspace("ws_cascade", actor_user_id="usr_admin")
    assert "only an active workspace owner" in str(exc.value).lower() or "forbidden" in str(exc.value).lower()

    # 2. Owner deletion succeeds
    result = deletion_svc.delete_workspace("ws_cascade", actor_user_id="usr_owner")
    assert result["success"] is True
    assert result["projects_deleted"] == 1
    assert result["assets_deleted"] == 1

    # Verify project and asset are purged
    assert ws_repo.get_project("proj_cascade") is None
    assert ws_repo.get_asset("ast_cascade") is None

    # Workspace is archived
    ws_after = ws_repo.get_workspace("ws_cascade")
    assert ws_after.status.value == "ARCHIVED"


def test_governance_user_pseudonymization_and_dsr_export(tmp_path):
    auth_dir = str(tmp_path / "auth")
    ws_dir = str(tmp_path / "workspace")
    auth_repo = AuthRepository(storage_dir=auth_dir)
    ws_repo = WorkspaceRepository(storage_dir=ws_dir)
    authz = AuthorizationService(auth_repository=auth_repo, workspace_repository=ws_repo)
    audit = SecurityAuditService()
    deletion_svc = DeletionService(
        auth_repository=auth_repo,
        workspace_repository=ws_repo,
        authz_svc=authz,
        audit_svc=audit,
    )

    user = User(
        user_id="usr_dsr_test",
        email="personal@privacy.local",
        email_normalized="personal@privacy.local",
        password_hash="secret_hash",
        display_name="Private Citizen",
    )
    auth_repo.save_user(user)

    # 1. Generate DSR export
    dsr_res = deletion_svc.generate_dsr_export(user_id="usr_dsr_test", actor_user_id="usr_dsr_test")
    assert dsr_res["success"] is True
    assert "download_url" in dsr_res

    # 2. Delete and pseudonymize user account
    del_res = deletion_svc.delete_user_account(target_user_id="usr_dsr_test", actor_user_id="usr_dsr_test")
    assert del_res["success"] is True

    # User record is pseudonymized
    pseudonymized = auth_repo.get_user("usr_dsr_test")
    assert pseudonymized.display_name == "[Deleted User]"
    assert "anonymized" in pseudonymized.email
    assert pseudonymized.password_hash == "DELETED_USER_NO_PASSWORD"
    assert pseudonymized.status.value == "DISABLED"
