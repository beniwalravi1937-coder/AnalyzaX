"""
Notification & Activity Repository for Phase 19.
Thread-safe, atomic JSON persistence for application events, notifications,
user preferences, and activity feeds.
"""

from datetime import datetime, timedelta, timezone
import json
import logging
import os
import threading
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.app.core.config import settings
from backend.app.engines.notifications.models import (
    ActivityFeedItem,
    ApplicationEvent,
    Notification,
    NotificationCategory,
    NotificationPreference,
    NotificationStatus,
)

logger = logging.getLogger("analyzax")


class NotificationRepository:
    """Thread-safe persistence layer for notifications, events, preferences, and activity."""

    def __init__(self, data_dir: Optional[str] = None, storage_dir: Optional[str] = None):
        self._data_dir = data_dir or storage_dir or settings.DATA_NOTIFICATIONS_DIR
        os.makedirs(self._data_dir, exist_ok=True)

        self._notifications_file = os.path.join(self._data_dir, "notifications.json")
        self._events_file = os.path.join(self._data_dir, "events.json")
        self._preferences_file = os.path.join(self._data_dir, "preferences.json")
        self._activity_file = os.path.join(self._data_dir, "activity.json")

        self._lock = threading.RLock()
        self._load_all()

    def _atomic_save(self, file_path: str, data: Any) -> None:
        tmp_file = f"{file_path}.tmp"
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            os.replace(tmp_file, file_path)
        except Exception as e:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
            logger.error(f"Error atomically saving to {file_path}: {e}")
            raise

    def _load_json(self, file_path: str, default_val: Any) -> Any:
        if not os.path.exists(file_path):
            return default_val
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading json from {file_path}: {e}")
            return default_val

    def _load_all(self) -> None:
        with self._lock:
            # 1. Notifications
            n_raw = self._load_json(self._notifications_file, {})
            self._notifications: Dict[str, Notification] = {}
            self._dedup_index: Set[str] = set()
            for n_id, data in n_raw.items():
                try:
                    n = Notification(**data)
                    self._notifications[n.notification_id] = n
                    if n.event_id:
                        self._dedup_index.add(f"{n.event_id}:{n.recipient_user_id}:{n.notification_type}")
                except Exception as e:
                    logger.error(f"Error loading notification {n_id}: {e}")

            # 2. Events
            e_raw = self._load_json(self._events_file, {})
            self._events: Dict[str, ApplicationEvent] = {}
            for e_id, data in e_raw.items():
                try:
                    ev = ApplicationEvent(**data)
                    self._events[ev.event_id] = ev
                except Exception as e:
                    logger.error(f"Error loading event {e_id}: {e}")

            # 3. Preferences
            p_raw = self._load_json(self._preferences_file, {})
            self._preferences: Dict[str, NotificationPreference] = {}
            for p_id, data in p_raw.items():
                try:
                    pref = NotificationPreference(**data)
                    self._preferences[f"{pref.user_id}:{pref.category.value}"] = pref
                except Exception as e:
                    logger.error(f"Error loading preference {p_id}: {e}")

            # 4. Activity
            a_raw = self._load_json(self._activity_file, [])
            self._activity: List[ActivityFeedItem] = []
            for item in a_raw:
                try:
                    self._activity.append(ActivityFeedItem(**item))
                except Exception as e:
                    logger.error(f"Error loading activity item: {e}")

    # ─────────────────────────────────────────────────────────────
    # Notifications
    # ─────────────────────────────────────────────────────────────

    def save_notification(self, notification: Notification) -> None:
        with self._lock:
            self._notifications[notification.notification_id] = notification
            if notification.event_id:
                self._dedup_index.add(
                    f"{notification.event_id}:{notification.recipient_user_id}:{notification.notification_type}"
                )
            self._save_notifications()

    def get_notification(self, notification_id: str) -> Optional[Notification]:
        with self._lock:
            return self._notifications.get(notification_id)

    def is_duplicate_notification(
        self, event_id: str, recipient_user_id: str, notification_type: str
    ) -> bool:
        with self._lock:
            key = f"{event_id}:{recipient_user_id}:{notification_type}"
            return key in self._dedup_index

    def list_notifications(
        self,
        user_id: Optional[str] = None,
        status: Optional[NotificationStatus] = None,
        category: Optional[NotificationCategory] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        recipient_user_id: Optional[str] = None,
    ) -> Tuple[List[Notification], int]:
        target_uid = user_id or recipient_user_id
        with self._lock:
            matched: List[Notification] = []
            search_clean = search.strip().lower() if search else None

            for n in self._notifications.values():
                if target_uid and n.recipient_user_id != target_uid:
                    continue
                if status and n.status != status:
                    continue
                if category and n.category != category:
                    continue
                if search_clean:
                    if (
                        search_clean not in n.title.lower()
                        and search_clean not in n.message.lower()
                        and search_clean not in (n.resource_type or "").lower()
                    ):
                        continue
                matched.append(n)

            # Sort newest first
            matched.sort(key=lambda item: item.created_at, reverse=True)
            total = len(matched)
            start = (page - 1) * page_size
            paginated = matched[start : start + page_size]
            return paginated, total

    def count_unread(self, user_id: str) -> int:
        with self._lock:
            count = 0
            for n in self._notifications.values():
                if n.recipient_user_id == user_id and n.status == NotificationStatus.UNREAD:
                    count += 1
            return count

    def mark_all_as_read(self, user_id: str) -> int:
        with self._lock:
            updated = 0
            now_str = datetime.now(timezone.utc).isoformat()
            for n in self._notifications.values():
                if n.recipient_user_id == user_id and n.status == NotificationStatus.UNREAD:
                    n.status = NotificationStatus.READ
                    n.read_at = now_str
                    updated += 1
            if updated > 0:
                self._save_notifications()
            return updated

    def _save_notifications(self) -> None:
        data = {n_id: n.model_dump() for n_id, n in self._notifications.items()}
        self._atomic_save(self._notifications_file, data)

    # ─────────────────────────────────────────────────────────────
    # Events
    # ─────────────────────────────────────────────────────────────

    def save_event(self, event: ApplicationEvent) -> None:
        with self._lock:
            self._events[event.event_id] = event
            data = {e_id: ev.model_dump() for e_id, ev in self._events.items()}
            self._atomic_save(self._events_file, data)

    def get_event(self, event_id: str) -> Optional[ApplicationEvent]:
        with self._lock:
            return self._events.get(event_id)

    # ─────────────────────────────────────────────────────────────
    # Preferences
    # ─────────────────────────────────────────────────────────────

    def save_preference(self, pref: NotificationPreference) -> None:
        with self._lock:
            key = f"{pref.user_id}:{pref.category.value}"
            self._preferences[key] = pref
            data = {k: p.model_dump() for k, p in self._preferences.items()}
            self._atomic_save(self._preferences_file, data)

    def get_preference(self, user_id: str, category: NotificationCategory) -> Optional[NotificationPreference]:
        with self._lock:
            key = f"{user_id}:{category.value}"
            return self._preferences.get(key)

    def list_preferences(self, user_id: str) -> List[NotificationPreference]:
        with self._lock:
            return [p for p in self._preferences.values() if p.user_id == user_id]

    # ─────────────────────────────────────────────────────────────
    # Activity Feed
    # ─────────────────────────────────────────────────────────────

    def save_activity(self, item: ActivityFeedItem) -> None:
        with self._lock:
            self._activity.append(item)
            data = [act.model_dump() for act in self._activity]
            self._atomic_save(self._activity_file, data)

    def list_project_activity(
        self,
        project_id: str,
        page: int = 1,
        page_size: int = 20,
        actor: Optional[str] = None,
        resource_type: Optional[str] = None,
    ) -> Tuple[List[ActivityFeedItem], int]:
        with self._lock:
            matched: List[ActivityFeedItem] = []
            for item in self._activity:
                if item.project_id != project_id:
                    continue
                if actor and item.actor_user_id != actor:
                    continue
                if resource_type and item.resource_type != resource_type:
                    continue
                matched.append(item)

            matched.sort(key=lambda a: a.timestamp, reverse=True)
            total = len(matched)
            start = (page - 1) * page_size
            paginated = matched[start : start + page_size]
            return paginated, total

    def list_workspace_activity(
        self,
        workspace_id: str,
        page: int = 1,
        page_size: int = 20,
        actor: Optional[str] = None,
        resource_type: Optional[str] = None,
    ) -> Tuple[List[ActivityFeedItem], int]:
        with self._lock:
            matched: List[ActivityFeedItem] = []
            for item in self._activity:
                if item.workspace_id != workspace_id:
                    continue
                if actor and item.actor_user_id != actor:
                    continue
                if resource_type and item.resource_type != resource_type:
                    continue
                matched.append(item)

            matched.sort(key=lambda a: a.timestamp, reverse=True)
            total = len(matched)
            start = (page - 1) * page_size
            paginated = matched[start : start + page_size]
            return paginated, total

    # ─────────────────────────────────────────────────────────────
    # Retention & Bounded Cleanup
    # ─────────────────────────────────────────────────────────────

    def cleanup_expired_and_bounded(
        self, max_per_user: int = 500, retention_days: int = 30
    ) -> int:
        """Purges old expired notifications while respecting bounds and preserving security audits."""
        with self._lock:
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(days=retention_days)
            cleaned_count = 0

            to_remove: List[str] = []
            user_items: Dict[str, List[Notification]] = {}

            for n_id, n in self._notifications.items():
                # Check explicit expiration
                if n.expires_at:
                    exp = datetime.fromisoformat(n.expires_at)
                    if exp <= now:
                        to_remove.append(n_id)
                        continue

                # Check general retention cutoff for read/archived
                if n.status in (NotificationStatus.READ, NotificationStatus.ARCHIVED):
                    created = datetime.fromisoformat(n.created_at)
                    if created <= cutoff and n.category != NotificationCategory.SECURITY:
                        to_remove.append(n_id)
                        continue

                user_items.setdefault(n.recipient_user_id, []).append(n)

            # Enforce max per user
            for u_id, items in user_items.items():
                if len(items) > max_per_user:
                    items.sort(key=lambda x: x.created_at)
                    excess = len(items) - max_per_user
                    for x in items[:excess]:
                        if x.category != NotificationCategory.SECURITY:
                            to_remove.append(x.notification_id)

            for rid in set(to_remove):
                if rid in self._notifications:
                    del self._notifications[rid]
                    cleaned_count += 1

            if cleaned_count > 0:
                self._save_notifications()

            return cleaned_count


# Singleton instance
notification_repo = NotificationRepository()
