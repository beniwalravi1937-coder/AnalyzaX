"""
Thread-safe repository for Phase 18 Collaboration, Sharing, Invitations, Share Links,
Notifications, and Collaboration Activity logs.
Maintains atomic JSON file storage under data/collaboration/ with in-memory multi-indexing.
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
from backend.app.engines.collaboration.models import (
    CollaborationActivityEvent,
    InvitationStatus,
    Notification,
    NotificationType,
    ResourceShare,
    ResourceType,
    ShareLink,
    SharePermission,
    ShareRecipientType,
    ShareStatus,
    WorkspaceInvitation,
)


class CollaborationRepository:
    """
    Coordinates persistence and lookup indexing for invitations, resource shares,
    share links, notifications, and collaboration activity.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self._lock = threading.RLock()
        self._storage_dir = os.path.abspath(storage_dir or settings.DATA_COLLABORATION_DIR)
        self._invitations_file = os.path.join(self._storage_dir, "invitations.json")
        self._shares_file = os.path.join(self._storage_dir, "shares.json")
        self._share_links_file = os.path.join(self._storage_dir, "share_links.json")
        self._notifications_file = os.path.join(self._storage_dir, "notifications.json")
        self._activity_file = os.path.join(self._storage_dir, "collaboration_activity.json")

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
            logger.warning(f"Failed to read {file_path}, using default: {e}")
            return default

    def _atomic_save(self, file_path: str, data: Any) -> None:
        temp_path = f"{file_path}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)

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
            # 1. Invitations
            inv_raw = self._load_json(self._invitations_file, {})
            self._invitations: Dict[str, WorkspaceInvitation] = {}
            self._invitations_by_hash: Dict[str, str] = {}  # token_hash -> invitation_id
            for inv_id, data in inv_raw.items():
                try:
                    inv = WorkspaceInvitation(**data)
                    self._invitations[inv.invitation_id] = inv
                    self._invitations_by_hash[inv.token_hash] = inv.invitation_id
                except Exception as e:
                    logger.error(f"Error loading invitation {inv_id}: {e}")

            # 2. Shares
            shares_raw = self._load_json(self._shares_file, {})
            self._shares: Dict[str, ResourceShare] = {}
            for s_id, data in shares_raw.items():
                try:
                    share = ResourceShare(**data)
                    self._shares[share.share_id] = share
                except Exception as e:
                    logger.error(f"Error loading share {s_id}: {e}")

            # 3. Share Links
            links_raw = self._load_json(self._share_links_file, {})
            self._share_links: Dict[str, ShareLink] = {}
            self._links_by_hash: Dict[str, str] = {}  # token_hash -> share_link_id
            for l_id, data in links_raw.items():
                try:
                    link = ShareLink(**data)
                    self._share_links[link.share_link_id] = link
                    self._links_by_hash[link.token_hash] = link.share_link_id
                except Exception as e:
                    logger.error(f"Error loading share link {l_id}: {e}")

            # 4. Notifications
            notifs_raw = self._load_json(self._notifications_file, {})
            self._notifications: Dict[str, Notification] = {}
            for n_id, data in notifs_raw.items():
                try:
                    notif = Notification(**data)
                    self._notifications[notif.notification_id] = notif
                except Exception as e:
                    logger.error(f"Error loading notification {n_id}: {e}")

            # 5. Activity Log
            act_raw = self._load_json(self._activity_file, [])
            self._activity: List[CollaborationActivityEvent] = []
            for item in act_raw:
                try:
                    self._activity.append(CollaborationActivityEvent(**item))
                except Exception as e:
                    logger.error(f"Error loading activity event: {e}")

    # ─────────────────────────────────────────────────────────────
    # Workspace Invitation Operations
    # ─────────────────────────────────────────────────────────────

    def save_invitation(self, inv: WorkspaceInvitation) -> None:
        with self._lock:
            # Clear any stale hash mappings pointing to this invitation
            for h, i_id in list(self._invitations_by_hash.items()):
                if i_id == inv.invitation_id and h != inv.token_hash:
                    self._invitations_by_hash.pop(h, None)
            self._invitations[inv.invitation_id] = inv
            self._invitations_by_hash[inv.token_hash] = inv.invitation_id
            self._save_invitations()

    def get_invitation(self, invitation_id: str) -> Optional[WorkspaceInvitation]:
        with self._lock:
            return self._invitations.get(invitation_id)

    def get_invitation_by_token_hash(self, token_hash: str) -> Optional[WorkspaceInvitation]:
        with self._lock:
            inv_id = self._invitations_by_hash.get(token_hash)
            if inv_id:
                inv = self._invitations.get(inv_id)
                # Check expiration dynamically
                if inv and inv.status == InvitationStatus.PENDING:
                    exp = datetime.fromisoformat(inv.expires_at)
                    if exp <= datetime.now(timezone.utc):
                        inv.status = InvitationStatus.EXPIRED
                        self.save_invitation(inv)
                return inv
            return None

    def list_invitations(
        self,
        workspace_id: str,
        status: Optional[InvitationStatus] = None,
    ) -> List[WorkspaceInvitation]:
        with self._lock:
            now = datetime.now(timezone.utc)
            results = []
            dirty = False
            for inv in self._invitations.values():
                if inv.workspace_id == workspace_id:
                    if inv.status == InvitationStatus.PENDING:
                        exp = datetime.fromisoformat(inv.expires_at)
                        if exp <= now:
                            inv.status = InvitationStatus.EXPIRED
                            dirty = True
                    if status is None or inv.status == status:
                        results.append(inv)
            if dirty:
                self._save_invitations()
            return sorted(results, key=lambda i: i.created_at, reverse=True)

    def find_pending_invitation(self, workspace_id: str, normalized_email: str) -> Optional[WorkspaceInvitation]:
        with self._lock:
            now = datetime.now(timezone.utc)
            for inv in self._invitations.values():
                if inv.workspace_id == workspace_id and inv.normalized_email == normalized_email:
                    if inv.status == InvitationStatus.PENDING:
                        exp = datetime.fromisoformat(inv.expires_at)
                        if exp > now:
                            return inv
            return None

    def _save_invitations(self) -> None:
        data = {inv_id: inv.model_dump() for inv_id, inv in self._invitations.items()}
        self._atomic_save(self._invitations_file, data)

    # ─────────────────────────────────────────────────────────────
    # Resource Share Operations
    # ─────────────────────────────────────────────────────────────

    def save_share(self, share: ResourceShare) -> None:
        with self._lock:
            self._shares[share.share_id] = share
            self._save_shares()

    def get_share(self, share_id: str) -> Optional[ResourceShare]:
        with self._lock:
            share = self._shares.get(share_id)
            if share and share.status == ShareStatus.ACTIVE and share.expires_at:
                exp = datetime.fromisoformat(share.expires_at)
                if exp <= datetime.now(timezone.utc):
                    share.status = ShareStatus.EXPIRED
                    self._save_shares()
            return share

    def list_shares_for_resource(
        self,
        resource_id: str,
        status: Optional[ShareStatus] = ShareStatus.ACTIVE,
    ) -> List[ResourceShare]:
        with self._lock:
            now = datetime.now(timezone.utc)
            results = []
            dirty = False
            for s in self._shares.values():
                if s.resource_id == resource_id:
                    if s.status == ShareStatus.ACTIVE and s.expires_at:
                        exp = datetime.fromisoformat(s.expires_at)
                        if exp <= now:
                            s.status = ShareStatus.EXPIRED
                            dirty = True
                    if status is None or s.status == status:
                        results.append(s)
            if dirty:
                self._save_shares()
            return sorted(results, key=lambda s: s.created_at, reverse=True)

    def list_shares_for_recipient(
        self,
        recipient_id: str,
        recipient_type: ShareRecipientType = ShareRecipientType.USER,
        status: Optional[ShareStatus] = ShareStatus.ACTIVE,
    ) -> List[ResourceShare]:
        with self._lock:
            now = datetime.now(timezone.utc)
            results = []
            dirty = False
            for s in self._shares.values():
                if s.recipient_id == recipient_id and s.recipient_type == recipient_type:
                    if s.status == ShareStatus.ACTIVE and s.expires_at:
                        exp = datetime.fromisoformat(s.expires_at)
                        if exp <= now:
                            s.status = ShareStatus.EXPIRED
                            dirty = True
                    if status is None or s.status == status:
                        results.append(s)
            if dirty:
                self._save_shares()
            return results

    def find_direct_share(
        self,
        resource_id: str,
        recipient_id: str,
        recipient_type: ShareRecipientType = ShareRecipientType.USER,
    ) -> Optional[ResourceShare]:
        with self._lock:
            now = datetime.now(timezone.utc)
            for s in self._shares.values():
                if s.resource_id == resource_id and s.recipient_id == recipient_id and s.recipient_type == recipient_type:
                    if s.status == ShareStatus.ACTIVE:
                        if s.expires_at:
                            exp = datetime.fromisoformat(s.expires_at)
                            if exp <= now:
                                s.status = ShareStatus.EXPIRED
                                self._save_shares()
                                return None
                        return s
            return None

    def _save_shares(self) -> None:
        data = {s_id: s.model_dump() for s_id, s in self._shares.items()}
        self._atomic_save(self._shares_file, data)

    # ─────────────────────────────────────────────────────────────
    # Share Link Operations
    # ─────────────────────────────────────────────────────────────

    def save_share_link(self, link: ShareLink) -> None:
        with self._lock:
            for h, l_id in list(self._links_by_hash.items()):
                if l_id == link.share_link_id and h != link.token_hash:
                    self._links_by_hash.pop(h, None)
            self._share_links[link.share_link_id] = link
            self._links_by_hash[link.token_hash] = link.share_link_id
            self._save_share_links()

    def get_share_link(self, share_link_id: str) -> Optional[ShareLink]:
        with self._lock:
            link = self._share_links.get(share_link_id)
            if link and link.status == ShareStatus.ACTIVE and link.expires_at:
                exp = datetime.fromisoformat(link.expires_at)
                if exp <= datetime.now(timezone.utc):
                    link.status = ShareStatus.EXPIRED
                    self._save_share_links()
            return link

    def get_share_link_by_token_hash(self, token_hash: str) -> Optional[ShareLink]:
        with self._lock:
            link_id = self._links_by_hash.get(token_hash)
            if link_id:
                link = self._share_links.get(link_id)
                if link and link.status == ShareStatus.ACTIVE and link.expires_at:
                    exp = datetime.fromisoformat(link.expires_at)
                    if exp <= datetime.now(timezone.utc):
                        link.status = ShareStatus.EXPIRED
                        self._save_share_links()
                return link
            return None

    def list_share_links_for_resource(
        self,
        resource_id: str,
        status: Optional[ShareStatus] = ShareStatus.ACTIVE,
    ) -> List[ShareLink]:
        with self._lock:
            now = datetime.now(timezone.utc)
            results = []
            dirty = False
            for l in self._share_links.values():
                if l.resource_id == resource_id:
                    if l.status == ShareStatus.ACTIVE and l.expires_at:
                        exp = datetime.fromisoformat(l.expires_at)
                        if exp <= now:
                            l.status = ShareStatus.EXPIRED
                            dirty = True
                    if status is None or l.status == status:
                        results.append(l)
            if dirty:
                self._save_share_links()
            return sorted(results, key=lambda l: l.created_at, reverse=True)

    def increment_share_link_access(self, share_link_id: str) -> None:
        with self._lock:
            link = self._share_links.get(share_link_id)
            if link:
                link.access_count += 1
                link.last_accessed_at = datetime.now(timezone.utc).isoformat()
                self._save_share_links()

    def _save_share_links(self) -> None:
        data = {l_id: l.model_dump() for l_id, l in self._share_links.items()}
        self._atomic_save(self._share_links_file, data)

    # ─────────────────────────────────────────────────────────────
    # Notification Operations
    # ─────────────────────────────────────────────────────────────

    def save_notification(self, notif: Notification) -> None:
        with self._lock:
            self._notifications[notif.notification_id] = notif
            self._save_notifications()

    def list_notifications(
        self,
        recipient_user_id: str,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[Notification]:
        with self._lock:
            results = [
                n for n in self._notifications.values()
                if n.recipient_user_id == recipient_user_id and (not unread_only or not n.is_read)
            ]
            return sorted(results, key=lambda n: n.created_at, reverse=True)[:limit]

    def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        with self._lock:
            notif = self._notifications.get(notification_id)
            if notif and notif.recipient_user_id == user_id:
                notif.is_read = True
                notif.read_at = datetime.now(timezone.utc).isoformat()
                self._save_notifications()
                return True
            return False

    def mark_all_notifications_read(self, user_id: str) -> int:
        with self._lock:
            count = 0
            now = datetime.now(timezone.utc).isoformat()
            for notif in self._notifications.values():
                if notif.recipient_user_id == user_id and not notif.is_read:
                    notif.is_read = True
                    notif.read_at = now
                    count += 1
            if count > 0:
                self._save_notifications()
            return count

    def _save_notifications(self) -> None:
        data = {n_id: n.model_dump() for n_id, n in self._notifications.items()}
        self._atomic_save(self._notifications_file, data)

    # ─────────────────────────────────────────────────────────────
    # Collaboration Activity Log Operations
    # ─────────────────────────────────────────────────────────────

    def record_activity(self, event: CollaborationActivityEvent) -> None:
        with self._lock:
            self._activity.append(event)
            if len(self._activity) > 5000:
                self._activity = self._activity[-5000:]
            data = [e.model_dump() for e in self._activity]
            self._atomic_save(self._activity_file, data)

    def list_activity(
        self,
        workspace_id: Optional[str] = None,
        project_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[CollaborationActivityEvent]:
        with self._lock:
            results = self._activity
            if workspace_id:
                results = [e for e in results if e.workspace_id == workspace_id]
            if project_id:
                results = [e for e in results if e.project_id == project_id]
            if resource_id:
                results = [e for e in results if e.resource_id == resource_id]
            return sorted(results, key=lambda e: e.timestamp, reverse=True)[:limit]


# Global singleton instance
collaboration_repo = CollaborationRepository()
