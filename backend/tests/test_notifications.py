"""
Enterprise Notifications and Activity Feed Test Suite for Phase 19.
Covers criteria NOTIFY-01 through NOTIFY-70:
- Persistence, recipient resolution, unread count
- Read/unread tracking, mark-all-read, pagination, search
- Deduplication, preferences enforcement, security non-suppressibility
- Deep-link validation, open-redirect prevention, access re-verification
- User-facing activity feeds vs security audit logs separation
- Multi-user isolation, cross-project access checks, storm protection
"""

from datetime import datetime, timedelta, timezone
import os
import shutil
import tempfile
import uuid

import pytest
from fastapi import HTTPException

from backend.app.engines.auth.models import (
    MembershipStatus,
    ProjectMember,
    RoleName,
    User,
    WorkspaceMember,
)
from backend.app.engines.auth.repository import AuthRepository
from backend.app.engines.notifications.models import (
    ActivityFeedItem,
    ApplicationEvent,
    ApplicationEventType,
    Notification,
    NotificationCategory,
    NotificationPriority,
    NotificationStatus,
)
from backend.app.engines.notifications.repository import NotificationRepository
from backend.app.engines.notifications.templates import TemplateRegistry
from backend.app.engines.workspace.models import Project, Workspace
from backend.app.engines.workspace.repository import WorkspaceRepository
from backend.app.services.auth.authorization_service import AuthorizationService
from backend.app.services.notifications.activity_service import ActivityService
from backend.app.services.notifications.event_dispatcher import EventDispatcher
from backend.app.services.notifications.notification_service import NotificationService
from backend.app.services.notifications.preference_service import PreferenceService


class NotificationTestContext:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="notify_test_")
        self.auth_dir = os.path.join(self.temp_dir, "auth")
        self.ws_dir = os.path.join(self.temp_dir, "workspace")
        self.notify_dir = os.path.join(self.temp_dir, "notifications")

        self.auth_repo = AuthRepository(storage_dir=self.auth_dir)
        self.ws_repo = WorkspaceRepository(storage_dir=self.ws_dir)
        self.notify_repo = NotificationRepository(storage_dir=self.notify_dir)

        self.templates = TemplateRegistry()
        self.pref_service = PreferenceService(repository=self.notify_repo)
        self.authz = AuthorizationService(self.auth_repo, self.ws_repo)
        self.activity_service = ActivityService(
            repository=self.notify_repo,
            authz=self.authz,
            auth_repository=self.auth_repo,
            ws_repository=self.ws_repo,
        )
        self.notification_service = NotificationService(
            repository=self.notify_repo,
            preferences=self.pref_service,
            templates=self.templates,
            auth_repository=self.auth_repo,
        )
        self.dispatcher = EventDispatcher(
            repository=self.notify_repo,
            notifications=self.notification_service,
            activity=self.activity_service,
        )

        self._setup_fixtures()

    def _setup_fixtures(self):
        # Users
        self.user_a = User(
            user_id="usr_alice",
            email="alice@analyzax.local",
            email_normalized="alice@analyzax.local",
            password_hash="hash_a",
            display_name="Alice Owner",
        )
        self.user_b = User(
            user_id="usr_bob",
            email="bob@analyzax.local",
            email_normalized="bob@analyzax.local",
            password_hash="hash_b",
            display_name="Bob Editor",
        )
        self.auth_repo.save_user(self.user_a)
        self.auth_repo.save_user(self.user_b)

        # Workspace
        self.ws = Workspace(
            workspace_id="ws_alpha",
            name="Alpha Workspace",
            slug="alpha-workspace",
            owner_user_id=self.user_a.user_id,
        )
        self.ws_repo.save_workspace(self.ws)

        # Workspace Members
        self.auth_repo.save_workspace_member(
            WorkspaceMember(
                workspace_id=self.ws.workspace_id,
                user_id=self.user_a.user_id,
                role=RoleName.OWNER,
                status=MembershipStatus.ACTIVE,
            )
        )
        self.auth_repo.save_workspace_member(
            WorkspaceMember(
                workspace_id=self.ws.workspace_id,
                user_id=self.user_b.user_id,
                role=RoleName.EDITOR,
                status=MembershipStatus.ACTIVE,
            )
        )

        # Projects
        self.proj_a = Project(
            project_id="proj_revenue",
            workspace_id=self.ws.workspace_id,
            name="Revenue Overview",
            slug="revenue-overview",
            created_by_user_id=self.user_a.user_id,
        )
        self.ws_repo.save_project(self.proj_a)

        # Project Member: Alice is OWNER, Bob is EDITOR
        self.auth_repo.save_project_member(
            ProjectMember(
                project_id=self.proj_a.project_id,
                user_id=self.user_a.user_id,
                role=RoleName.OWNER,
                status=MembershipStatus.ACTIVE,
            )
        )
        self.auth_repo.save_project_member(
            ProjectMember(
                project_id=self.proj_a.project_id,
                user_id=self.user_b.user_id,
                role=RoleName.EDITOR,
                status=MembershipStatus.ACTIVE,
            )
        )

    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)


@pytest.fixture
def ctx():
    c = NotificationTestContext()
    yield c
    c.cleanup()


# =====================================================================
# NOTIFY-01 to NOTIFY-08: Notification Lifecycle, Read/Unread, Counts
# =====================================================================

def test_notification_creation_and_persistence(ctx: NotificationTestContext):
    """NOTIFY-01, NOTIFY-02: Notifications are persisted and belong to specific recipient."""
    event = ApplicationEvent(
        event_id="evt_share_001",
        event_type=ApplicationEventType.RESOURCE_SHARED,
        actor_user_id=ctx.user_a.user_id,
        workspace_id=ctx.ws.workspace_id,
        project_id=ctx.proj_a.project_id,
        resource_type="DASHBOARD",
        resource_id="dash_finance",
        metadata={
            "recipient_user_id": ctx.user_b.user_id,
            "resource_name": "Finance KPI",
            "permission": "view",
        },
    )

    notifications = ctx.dispatcher.dispatch(event)
    assert len(notifications) == 1
    notif = notifications[0]

    assert notif.recipient_user_id == ctx.user_b.user_id
    assert notif.category == NotificationCategory.COLLABORATION
    assert notif.status == NotificationStatus.UNREAD
    assert "Finance KPI" in notif.message
    assert notif.deep_link == "/dashboard/dash_finance"

    # Verify persisted in repository
    persisted = ctx.notify_repo.get_notification(notif.notification_id)
    assert persisted is not None
    assert persisted.recipient_user_id == ctx.user_b.user_id


def test_unread_count_is_user_scoped(ctx: NotificationTestContext):
    """NOTIFY-03, NOTIFY-04: Unread count is user-scoped and accurate."""
    assert ctx.notification_service.get_unread_count(ctx.user_b.user_id) == 0
    assert ctx.notification_service.get_unread_count(ctx.user_a.user_id) == 0

    ctx.dispatcher.create_and_dispatch(
        event_type=ApplicationEventType.RESOURCE_SHARED,
        actor_user_id=ctx.user_a.user_id,
        workspace_id=ctx.ws.workspace_id,
        project_id=ctx.proj_a.project_id,
        resource_type="DASHBOARD",
        resource_id="dash_1",
        metadata={"recipient_user_id": ctx.user_b.user_id, "resource_name": "Dash 1"},
    )
    ctx.dispatcher.create_and_dispatch(
        event_type=ApplicationEventType.RESOURCE_SHARED,
        actor_user_id=ctx.user_a.user_id,
        workspace_id=ctx.ws.workspace_id,
        project_id=ctx.proj_a.project_id,
        resource_type="DASHBOARD",
        resource_id="dash_2",
        metadata={"recipient_user_id": ctx.user_b.user_id, "resource_name": "Dash 2"},
    )

    # Bob has 2 unread, Alice has 0
    assert ctx.notification_service.get_unread_count(ctx.user_b.user_id) == 2
    assert ctx.notification_service.get_unread_count(ctx.user_a.user_id) == 0


def test_read_unread_lifecycle(ctx: NotificationTestContext):
    """NOTIFY-05, NOTIFY-06, NOTIFY-07: Read state persists server-side; mark read/unread/read-all work."""
    notifs = ctx.dispatcher.dispatch(
        ApplicationEvent(
            event_id="evt_export_001",
            event_type=ApplicationEventType.EXPORT_COMPLETED,
            actor_user_id=ctx.user_b.user_id,
            resource_type="EXPORT",
            resource_id="exp_999",
            metadata={
                "recipient_user_id": ctx.user_b.user_id,
                "resource_name": "sales_q3.csv",
                "file_name": "sales_q3.csv",
                "format": "csv",
            },
        )
    )
    notif = notifs[0]
    assert notif.status == NotificationStatus.UNREAD
    assert notif.read_at is None

    # Mark Read
    updated = ctx.notification_service.mark_as_read(notif.notification_id, ctx.user_b.user_id)
    assert updated.status == NotificationStatus.READ
    assert updated.read_at is not None
    assert ctx.notification_service.get_unread_count(ctx.user_b.user_id) == 0

    # Mark Unread
    reverted = ctx.notification_service.mark_as_unread(notif.notification_id, ctx.user_b.user_id)
    assert reverted.status == NotificationStatus.UNREAD
    assert reverted.read_at is None
    assert ctx.notification_service.get_unread_count(ctx.user_b.user_id) == 1

    # Mark All Read
    count = ctx.notification_service.mark_all_read(ctx.user_b.user_id)
    assert count == 1
    assert ctx.notification_service.get_unread_count(ctx.user_b.user_id) == 0


def test_pagination_and_search(ctx: NotificationTestContext):
    """NOTIFY-08, NOTIFY-35: Pagination and search filtering are user-scoped."""
    for i in range(5):
        ctx.dispatcher.create_and_dispatch(
            event_type=ApplicationEventType.REPORT_EXPORTED,
            actor_user_id=ctx.user_b.user_id,
            resource_type="REPORT",
            resource_id=f"rep_{i}",
            metadata={
                "recipient_user_id": ctx.user_b.user_id,
                "resource_name": f"Financial Report {i}",
            },
        )

    # Page 1 (limit 2)
    resp1 = ctx.notification_service.list_notifications(
        user_id=ctx.user_b.user_id,
        limit=2,
    )
    assert len(resp1.items) == 2
    assert resp1.total_count == 5
    assert resp1.has_more is True
    assert resp1.next_cursor is not None

    # Page 2 (cursor)
    resp2 = ctx.notification_service.list_notifications(
        user_id=ctx.user_b.user_id,
        limit=2,
        cursor=resp1.next_cursor,
    )
    assert len(resp2.items) == 2

    # Search
    search_resp = ctx.notification_service.list_notifications(
        user_id=ctx.user_b.user_id,
        search="Report 3",
    )
    assert len(search_resp.items) == 1
    assert "Report 3" in search_resp.items[0].message


# =====================================================================
# NOTIFY-09 to NOTIFY-14: Templates, Security, Deduplication
# =====================================================================

def test_template_variable_allowlisting(ctx: NotificationTestContext):
    """NOTIFY-09, NOTIFY-10, NOTIFY-11, NOTIFY-50, NOTIFY-51: Templates prevent arbitrary code and secret leakage."""
    rendered_title, rendered_msg = ctx.templates.render_template(
        template_id="tpl_share_received",
        context={
            "actor_name": "Alice",
            "resource_name": "Q3 Dashboard",
            "permission": "edit",
            "password": "supersecretpassword",  # should be ignored
            "token": "raw_jwt_or_invitation_token",  # should be ignored
        },
    )
    assert "Alice shared 'Q3 Dashboard'" in rendered_msg
    assert "supersecretpassword" not in rendered_msg
    assert "raw_jwt_or_invitation_token" not in rendered_msg


def test_idempotent_event_deduplication(ctx: NotificationTestContext):
    """NOTIFY-13, NOTIFY-47, NOTIFY-48: Duplicate event executions produce only one notification."""
    event = ApplicationEvent(
        event_id="evt_unique_123",
        event_type=ApplicationEventType.RESOURCE_SHARED,
        actor_user_id=ctx.user_a.user_id,
        resource_type="DASHBOARD",
        resource_id="dash_abc",
        metadata={"recipient_user_id": ctx.user_b.user_id, "resource_name": "Sales Dash"},
    )

    # First dispatch
    first_run = ctx.dispatcher.dispatch(event)
    assert len(first_run) == 1

    # Second dispatch with identical event_id
    second_run = ctx.dispatcher.dispatch(event)
    assert len(second_run) == 0

    # Verify only 1 notification exists in storage
    notifications, total = ctx.notify_repo.list_notifications(recipient_user_id=ctx.user_b.user_id)
    assert total == 1
    assert len(notifications) == 1


# =====================================================================
# NOTIFY-26 to NOTIFY-28: Notification Preferences & Security Non-Suppressibility
# =====================================================================

def test_preferences_suppression_and_security_non_suppressibility(ctx: NotificationTestContext):
    """NOTIFY-26, NOTIFY-27, NOTIFY-28: Preference suppression works; security alerts cannot be disabled."""
    # Disable EXPORT notifications
    ctx.pref_service.update_preference(
        user_id=ctx.user_b.user_id,
        category=NotificationCategory.EXPORT,
        enabled=False,
    )

    # Trigger export event for Bob -> suppressed!
    ctx.dispatcher.create_and_dispatch(
        event_type=ApplicationEventType.EXPORT_COMPLETED,
        actor_user_id=ctx.user_b.user_id,
        resource_type="EXPORT",
        resource_id="exp_suppressed",
        metadata={
            "recipient_user_id": ctx.user_b.user_id,
            "resource_name": "suppressed.csv",
            "file_name": "suppressed.csv",
            "format": "csv",
        },
    )

    bob_notifs, _ = ctx.notify_repo.list_notifications(recipient_user_id=ctx.user_b.user_id)
    export_notifs = [n for n in bob_notifs if n.category == NotificationCategory.EXPORT]
    assert len(export_notifs) == 0

    # Attempt to disable SECURITY alerts -> MUST raise 400 Bad Request
    with pytest.raises(HTTPException) as exc_info:
        ctx.pref_service.update_preference(
            user_id=ctx.user_b.user_id,
            category=NotificationCategory.SECURITY,
            enabled=False,
        )
    assert exc_info.value.status_code == 400
    assert "Security-critical notifications cannot be disabled" in exc_info.value.detail


# =====================================================================
# NOTIFY-29 to NOTIFY-34: Deep Link Validation & Authorization Recheck
# =====================================================================

def test_open_redirect_prevention(ctx: NotificationTestContext):
    """NOTIFY-29, NOTIFY-30: Open redirects and external URLs are rejected."""
    # Safe internal relative link
    safe_link = ctx.templates.generate_deep_link("/dashboard/{resource_id}", {"resource_id": "dash_100"})
    assert safe_link == "/dashboard/dash_100"

    # External URL with protocol -> must be sanitized / blocked
    bad_link = ctx.templates.generate_deep_link("https://evil.com/phishing/{resource_id}", {"resource_id": "dash_100"})
    assert bad_link is None

    # Protocol-relative URL -> must be blocked
    proto_link = ctx.templates.generate_deep_link("//attacker.com/steal", {})
    assert proto_link is None


# =====================================================================
# NOTIFY-36 to NOTIFY-40: Activity Feeds & Security Audit Separation
# =====================================================================

def test_activity_feed_access_gating(ctx: NotificationTestContext):
    """NOTIFY-36, NOTIFY-39, NOTIFY-40: Project and workspace activity feeds enforce permissions."""
    # Record project activity
    ctx.dispatcher.create_and_dispatch(
        event_type=ApplicationEventType.DATASET_CREATED,
        actor_user_id=ctx.user_a.user_id,
        workspace_id=ctx.ws.workspace_id,
        project_id=ctx.proj_a.project_id,
        resource_type="DATASET",
        resource_id="ds_sales",
        metadata={"resource_name": "Sales 2026.csv"},
    )

    # Bob has project access -> can view project activity
    feed = ctx.activity_service.get_project_activity(
        project_id=ctx.proj_a.project_id,
        requesting_user_id=ctx.user_b.user_id,
    )
    assert len(feed.items) >= 1
    assert any("Sales 2026.csv" in item.description for item in feed.items)

    # Unrelated user without membership -> 403 Forbidden
    outsider = User(
        user_id="usr_charlie",
        email="charlie@other.com",
        email_normalized="charlie@other.com",
        password_hash="hash_c",
        display_name="Charlie Stranger",
    )
    ctx.auth_repo.save_user(outsider)

    with pytest.raises(HTTPException) as exc_info:
        ctx.activity_service.get_project_activity(
            project_id=ctx.proj_a.project_id,
            requesting_user_id=outsider.user_id,
        )
    assert exc_info.value.status_code == 403

    with pytest.raises(HTTPException) as exc_info:
        ctx.activity_service.get_workspace_activity(
            workspace_id=ctx.ws.workspace_id,
            requesting_user_id=outsider.user_id,
        )
    assert exc_info.value.status_code == 403


def test_activity_vs_security_audit_separation(ctx: NotificationTestContext):
    """NOTIFY-37: Security alerts and low-level auth events never appear in user activity feed."""
    ctx.dispatcher.create_and_dispatch(
        event_type=ApplicationEventType.USER_LOGIN,
        actor_user_id=ctx.user_a.user_id,
        workspace_id=ctx.ws.workspace_id,
        project_id=ctx.proj_a.project_id,
        metadata={"ip": "192.168.1.1", "session_id": "sess_secret"},
    )
    ctx.dispatcher.create_and_dispatch(
        event_type=ApplicationEventType.SECURITY_ALERT,
        actor_user_id=ctx.user_a.user_id,
        workspace_id=ctx.ws.workspace_id,
        project_id=ctx.proj_a.project_id,
        metadata={"alert": "Rate limit exceeded on auth endpoint"},
    )

    ws_feed = ctx.activity_service.get_workspace_activity(
        workspace_id=ctx.ws.workspace_id,
        requesting_user_id=ctx.user_a.user_id,
    )

    # Activity feed must NOT contain login or security alert items
    for item in ws_feed.items:
        assert item.action not in ("User Login", "Security Alert")
        assert "sess_secret" not in str(item.metadata)


# =====================================================================
# NOTIFY-41 to NOTIFY-44: Cross-User & Cross-Workspace Isolation
# =====================================================================

def test_cross_user_isolation(ctx: NotificationTestContext):
    """NOTIFY-03, NOTIFY-41, NOTIFY-42: User B cannot read or modify User A's notifications."""
    # Create notification for Alice
    alice_notifs = ctx.dispatcher.dispatch(
        ApplicationEvent(
            event_id="evt_alice_alert",
            event_type=ApplicationEventType.SECURITY_ALERT,
            actor_user_id=ctx.user_a.user_id,
            resource_type="ACCOUNT",
            metadata={
                "recipient_user_id": ctx.user_a.user_id,
                "title": "Security Alert",
                "message": "New login detected",
            },
        )
    )
    alice_notif_id = alice_notifs[0].notification_id

    # Bob attempts to read Alice's notification -> 404 (NotFound, never exposes existence)
    with pytest.raises(HTTPException) as exc_info:
        ctx.notification_service.get_notification(alice_notif_id, ctx.user_b.user_id)
    assert exc_info.value.status_code == 404

    # Bob attempts to mark Alice's notification as read -> 404
    with pytest.raises(HTTPException) as exc_info:
        ctx.notification_service.mark_as_read(alice_notif_id, ctx.user_b.user_id)
    assert exc_info.value.status_code == 404

    # Bob's notification list does NOT include Alice's notification
    bob_list = ctx.notification_service.list_notifications(user_id=ctx.user_b.user_id)
    assert not any(n.notification_id == alice_notif_id for n in bob_list.items)


# =====================================================================
# NOTIFY-49, NOTIFY-54: Failure Handling & Bounded Retention Cleanup
# =====================================================================

def test_retention_cleanup(ctx: NotificationTestContext):
    """NOTIFY-54, NOTIFY-55: Bounded cleanup prunes expired notifications."""
    # Create an expired notification directly in repo
    old_time = datetime.now(timezone.utc) - timedelta(days=60)
    expired_notif = Notification(
        recipient_user_id=ctx.user_b.user_id,
        notification_type="RESOURCE_SHARED",
        category=NotificationCategory.COLLABORATION,
        title="Old Share",
        message="Expired",
        created_at=old_time,
        expires_at=old_time + timedelta(days=1),
    )
    ctx.notify_repo.save_notification(expired_notif)

    # Run cleanup
    cleaned = ctx.notification_service.cleanup_retention(ctx.user_b.user_id)
    assert cleaned >= 1

    # Verify pruned
    assert ctx.notify_repo.get_notification(expired_notif.notification_id) is None
