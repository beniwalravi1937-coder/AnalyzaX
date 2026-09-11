"""
Thread-safe repository for Phase 17 Authentication, Authorization, Memberships,
Sessions, Password Reset Tokens, and Security Audit Events.
Maintains atomic JSON file storage under data/auth/ with in-memory indexing.
"""

from datetime import datetime, timezone
import json
import os
import shutil
import threading
import time
from typing import Any, Dict, List, Optional

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.auth.models import (
    MembershipStatus,
    MFAFactor,
    PasswordResetToken,
    ProjectMember,
    RoleName,
    SecurityAuditEvent,
    Session,
    User,
    UserStatus,
    WorkspaceMember,
)


class AuthRepository:
    """
    Thread-safe repository coordinating atomic JSON persistence and multi-index lookups
    for users, sessions, memberships, password reset tokens, and security audit logs.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self._lock = threading.RLock()
        self._storage_dir = os.path.abspath(storage_dir or settings.DATA_AUTH_DIR)
        self._users_file = os.path.join(self._storage_dir, "users.json")
        self._sessions_file = os.path.join(self._storage_dir, "sessions.json")
        self._ws_members_file = os.path.join(self._storage_dir, "workspace_members.json")
        self._proj_members_file = os.path.join(self._storage_dir, "project_members.json")
        self._reset_tokens_file = os.path.join(self._storage_dir, "reset_tokens.json")
        self._mfa_file = os.path.join(self._storage_dir, "mfa_factors.json")
        self._audit_file = os.path.join(self._storage_dir, "security_audit.json")

        self._ensure_dirs()
        self._load_all()

    def _ensure_dirs(self) -> None:
        os.makedirs(self._storage_dir, exist_ok=True)

    def _load_json(self, file_path: str, default: Any) -> Any:
        if not os.path.exists(file_path):
            return default
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read {file_path}, falling back to default: {e}")
            return default

    def _atomic_save(self, file_path: str, data: Any) -> None:
        temp_path = f"{file_path}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)

            # Windows atomic replace with retry & fallback
            for attempt in range(5):
                try:
                    os.replace(temp_path, file_path)
                    return
                except (PermissionError, OSError):
                    if attempt < 4:
                        time.sleep(0.02)
                    else:
                        try:
                            shutil.copyfile(temp_path, file_path)
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                            return
                        except Exception:
                            raise
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def _load_all(self) -> None:
        with self._lock:
            # Users: user_id -> User
            users_raw = self._load_json(self._users_file, {})
            self._users: Dict[str, User] = {}
            self._users_by_email: Dict[str, str] = {}  # email_normalized -> user_id
            for u_id, u_data in users_raw.items():
                try:
                    user = User(**u_data)
                    self._users[user.user_id] = user
                    self._users_by_email[user.email_normalized] = user.user_id
                except Exception as e:
                    logger.warning(f"Failed to parse user {u_id}: {e}")

            # Sessions: session_id -> Session
            sessions_raw = self._load_json(self._sessions_file, {})
            self._sessions: Dict[str, Session] = {}
            self._sessions_by_token_hash: Dict[str, str] = {}  # token_hash -> session_id
            for s_id, s_data in sessions_raw.items():
                try:
                    session = Session(**s_data)
                    self._sessions[session.session_id] = session
                    self._sessions_by_token_hash[session.token_hash] = session.session_id
                except Exception as e:
                    logger.warning(f"Failed to parse session {s_id}: {e}")

            # Workspace Members: membership_id -> WorkspaceMember
            ws_raw = self._load_json(self._ws_members_file, {})
            self._ws_members: Dict[str, WorkspaceMember] = {}
            for m_id, m_data in ws_raw.items():
                try:
                    member = WorkspaceMember(**m_data)
                    self._ws_members[member.membership_id] = member
                except Exception as e:
                    logger.warning(f"Failed to parse workspace member {m_id}: {e}")

            # Project Members: membership_id -> ProjectMember
            proj_raw = self._load_json(self._proj_members_file, {})
            self._proj_members: Dict[str, ProjectMember] = {}
            for m_id, m_data in proj_raw.items():
                try:
                    member = ProjectMember(**m_data)
                    self._proj_members[member.membership_id] = member
                except Exception as e:
                    logger.warning(f"Failed to parse project member {m_id}: {e}")

            # Reset Tokens: token_id -> PasswordResetToken
            tokens_raw = self._load_json(self._reset_tokens_file, {})
            self._reset_tokens: Dict[str, PasswordResetToken] = {}
            self._tokens_by_hash: Dict[str, str] = {}  # token_hash -> token_id
            for t_id, t_data in tokens_raw.items():
                try:
                    token = PasswordResetToken(**t_data)
                    self._reset_tokens[token.token_id] = token
                    self._tokens_by_hash[token.token_hash] = token.token_id
                except Exception as e:
                    logger.warning(f"Failed to parse reset token {t_id}: {e}")

            # MFA Factors: user_id -> MFAFactor
            mfa_raw = self._load_json(self._mfa_file, {})
            self._mfa_factors: Dict[str, MFAFactor] = {}
            for u_id, m_data in mfa_raw.items():
                try:
                    self._mfa_factors[u_id] = MFAFactor(**m_data)
                except Exception as e:
                    logger.warning(f"Failed to parse MFA factor for user {u_id}: {e}")

            # Security Audit: list of SecurityAuditEvent dicts
            audit_raw = self._load_json(self._audit_file, [])
            self._audit_events: List[SecurityAuditEvent] = []
            for a_data in audit_raw:
                try:
                    self._audit_events.append(SecurityAuditEvent(**a_data))
                except Exception as e:
                    logger.warning(f"Failed to parse audit event: {e}")

    # ─────────────────────────────────────────────────────────
    # User Operations
    # ─────────────────────────────────────────────────────────

    def save_user(self, user: User) -> None:
        with self._lock:
            self._users[user.user_id] = user
            self._users_by_email[user.email_normalized] = user.user_id
            self._save_users()

    def get_user(self, user_id: str) -> Optional[User]:
        with self._lock:
            return self._users.get(user_id)

    def get_user_by_email(self, email_normalized: str) -> Optional[User]:
        with self._lock:
            uid = self._users_by_email.get(email_normalized)
            if uid:
                return self._users.get(uid)
            return None

    def list_users(self) -> List[User]:
        with self._lock:
            return list(self._users.values())

    def _save_users(self) -> None:
        data = {u_id: u.model_dump() for u_id, u in self._users.items()}
        self._atomic_save(self._users_file, data)

    # ─────────────────────────────────────────────────────────
    # Session Operations
    # ─────────────────────────────────────────────────────────

    def save_session(self, session: Session) -> None:
        with self._lock:
            self._sessions[session.session_id] = session
            self._sessions_by_token_hash[session.token_hash] = session.session_id
            self._save_sessions()

    def get_session(self, session_id: str) -> Optional[Session]:
        with self._lock:
            return self._sessions.get(session_id)

    def get_session_by_token_hash(self, token_hash: str) -> Optional[Session]:
        with self._lock:
            s_id = self._sessions_by_token_hash.get(token_hash)
            if s_id:
                return self._sessions.get(s_id)
            return None

    def list_user_sessions(self, user_id: str) -> List[Session]:
        with self._lock:
            return [s for s in self._sessions.values() if s.user_id == user_id]

    def revoke_session(self, session_id: str) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.revoked_at = datetime.now(timezone.utc).isoformat()
                self._save_sessions()
                return True
            return False

    def revoke_all_user_sessions(self, user_id: str, except_session_id: Optional[str] = None) -> int:
        with self._lock:
            count = 0
            now = datetime.now(timezone.utc).isoformat()
            for s in self._sessions.values():
                if s.user_id == user_id and s.session_id != except_session_id and s.revoked_at is None:
                    s.revoked_at = now
                    count += 1
            if count > 0:
                self._save_sessions()
            return count

    def _save_sessions(self) -> None:
        data = {s_id: s.model_dump() for s_id, s in self._sessions.items()}
        self._atomic_save(self._sessions_file, data)

    # ─────────────────────────────────────────────────────────
    # Workspace Member Operations
    # ─────────────────────────────────────────────────────────

    def save_workspace_member(self, member: WorkspaceMember) -> None:
        with self._lock:
            # Check if membership already exists for (workspace_id, user_id)
            existing = self.get_workspace_member(member.workspace_id, member.user_id)
            if existing:
                existing.role = member.role
                existing.status = member.status
                existing.updated_at = datetime.now(timezone.utc).isoformat()
                self._ws_members[existing.membership_id] = existing
            else:
                self._ws_members[member.membership_id] = member
            self._save_ws_members()

    def get_workspace_member(self, workspace_id: str, user_id: str) -> Optional[WorkspaceMember]:
        with self._lock:
            for m in self._ws_members.values():
                if m.workspace_id == workspace_id and m.user_id == user_id:
                    return m
            return None

    def list_workspace_members(self, workspace_id: str) -> List[WorkspaceMember]:
        with self._lock:
            return [
                m for m in self._ws_members.values()
                if m.workspace_id == workspace_id and m.status != MembershipStatus.REMOVED
            ]

    def list_user_workspaces(self, user_id: str) -> List[WorkspaceMember]:
        with self._lock:
            return [
                m for m in self._ws_members.values()
                if m.user_id == user_id and m.status == MembershipStatus.ACTIVE
            ]

    def count_active_workspace_owners(self, workspace_id: str) -> int:
        with self._lock:
            return sum(
                1 for m in self._ws_members.values()
                if m.workspace_id == workspace_id and m.role == RoleName.OWNER and m.status == MembershipStatus.ACTIVE
            )

    def delete_workspace_member(self, workspace_id: str, user_id: str) -> bool:
        with self._lock:
            member = self.get_workspace_member(workspace_id, user_id)
            if member:
                member.status = MembershipStatus.REMOVED
                member.updated_at = datetime.now(timezone.utc).isoformat()
                self._save_ws_members()
                return True
            return False

    def _save_ws_members(self) -> None:
        data = {m_id: m.model_dump() for m_id, m in self._ws_members.items()}
        self._atomic_save(self._ws_members_file, data)

    # ─────────────────────────────────────────────────────────
    # Project Member Operations
    # ─────────────────────────────────────────────────────────

    def save_project_member(self, member: ProjectMember) -> None:
        with self._lock:
            existing = self.get_project_member(member.project_id, member.user_id)
            if existing:
                existing.role = member.role
                existing.status = member.status
                existing.updated_at = datetime.now(timezone.utc).isoformat()
                self._proj_members[existing.membership_id] = existing
            else:
                self._proj_members[member.membership_id] = member
            self._save_proj_members()

    def get_project_member(self, project_id: str, user_id: str) -> Optional[ProjectMember]:
        with self._lock:
            for m in self._proj_members.values():
                if m.project_id == project_id and m.user_id == user_id:
                    return m
            return None

    def list_project_members(self, project_id: str) -> List[ProjectMember]:
        with self._lock:
            return [
                m for m in self._proj_members.values()
                if m.project_id == project_id and m.status != MembershipStatus.REMOVED
            ]

    def delete_project_member(self, project_id: str, user_id: str) -> bool:
        with self._lock:
            member = self.get_project_member(project_id, user_id)
            if member:
                member.status = MembershipStatus.REMOVED
                member.updated_at = datetime.now(timezone.utc).isoformat()
                self._save_proj_members()
                return True
            return False

    def _save_proj_members(self) -> None:
        data = {m_id: m.model_dump() for m_id, m in self._proj_members.items()}
        self._atomic_save(self._proj_members_file, data)

    # ─────────────────────────────────────────────────────────
    # Password Reset Operations
    # ─────────────────────────────────────────────────────────

    def save_reset_token(self, token: PasswordResetToken) -> None:
        with self._lock:
            self._reset_tokens[token.token_id] = token
            self._tokens_by_hash[token.token_hash] = token.token_id
            self._save_reset_tokens()

    def get_reset_token_by_hash(self, token_hash: str) -> Optional[PasswordResetToken]:
        with self._lock:
            t_id = self._tokens_by_hash.get(token_hash)
            if t_id:
                return self._reset_tokens.get(t_id)
            return None

    def mark_reset_token_used(self, token_id: str) -> None:
        with self._lock:
            token = self._reset_tokens.get(token_id)
            if token:
                token.used_at = datetime.now(timezone.utc).isoformat()
                self._save_reset_tokens()

    def _save_reset_tokens(self) -> None:
        data = {t_id: t.model_dump() for t_id, t in self._reset_tokens.items()}
        self._atomic_save(self._reset_tokens_file, data)

    # ─────────────────────────────────────────────────────────
    # MFA Factor Operations
    # ─────────────────────────────────────────────────────────

    def save_mfa_factor(self, factor: MFAFactor) -> MFAFactor:
        with self._lock:
            self._mfa_factors[factor.user_id] = factor
            self._save_mfa_factors()
            return factor

    def get_mfa_factor(self, user_id: str) -> Optional[MFAFactor]:
        with self._lock:
            return self._mfa_factors.get(user_id)

    def delete_mfa_factor(self, user_id: str) -> bool:
        with self._lock:
            if user_id in self._mfa_factors:
                del self._mfa_factors[user_id]
                self._save_mfa_factors()
                return True
            return False

    def _save_mfa_factors(self) -> None:
        data = {u_id: f.model_dump() for u_id, f in self._mfa_factors.items()}
        self._atomic_save(self._mfa_file, data)

    # ─────────────────────────────────────────────────────────
    # Security Audit Operations
    # ─────────────────────────────────────────────────────────

    def record_audit_event(self, event: SecurityAuditEvent) -> None:
        with self._lock:
            self._audit_events.append(event)
            # Limit audit events stored in single file to last 5000 events
            if len(self._audit_events) > 5000:
                self._audit_events = self._audit_events[-5000:]
            data = [e.model_dump() for e in self._audit_events]
            self._atomic_save(self._audit_file, data)

    def query_audit_events(
        self,
        user_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[SecurityAuditEvent]:
        with self._lock:
            events = self._audit_events
            if user_id:
                events = [e for e in events if e.user_id == user_id]
            if workspace_id:
                events = [e for e in events if e.workspace_id == workspace_id]
            # Return most recent first
            return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]


# Global repository instance
auth_repo = AuthRepository()
