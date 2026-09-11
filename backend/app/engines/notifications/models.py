"""
Domain models for Phase 19: Enterprise-Grade Notifications, Activity Center & Collaboration Communication.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class ApplicationEventType(str, Enum):
    # Auth & Identity
    USER_REGISTERED = "USER_REGISTERED"
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    PASSWORD_RESET = "PASSWORD_RESET"
    SESSION_REVOKED = "SESSION_REVOKED"
    SECURITY_ALERT = "SECURITY_ALERT"

    # Workspace & Project
    PROJECT_CREATED = "PROJECT_CREATED"
    PROJECT_ARCHIVED = "PROJECT_ARCHIVED"
    PROJECT_RESTORED = "PROJECT_RESTORED"

    # Team Membership & Invitations
    INVITATION_CREATED = "INVITATION_CREATED"
    INVITATION_ACCEPTED = "INVITATION_ACCEPTED"
    INVITATION_REVOKED = "INVITATION_REVOKED"
    MEMBER_ADDED = "MEMBER_ADDED"
    MEMBER_REMOVED = "MEMBER_REMOVED"
    MEMBER_ROLE_CHANGED = "MEMBER_ROLE_CHANGED"

    # Sharing & Collaboration
    RESOURCE_SHARED = "RESOURCE_SHARED"
    RESOURCE_SHARE_REVOKED = "RESOURCE_SHARE_REVOKED"
    SHARE_LINK_CREATED = "SHARE_LINK_CREATED"
    SHARE_LINK_REVOKED = "SHARE_LINK_REVOKED"

    # Datasets & Versions
    DATASET_CREATED = "DATASET_CREATED"
    DATASET_VERSION_CREATED = "DATASET_VERSION_CREATED"
    DATASET_ARCHIVED = "DATASET_ARCHIVED"
    DATASET_RESTORED = "DATASET_RESTORED"

    # Analytical Jobs & Engines
    ANALYSIS_STARTED = "ANALYSIS_STARTED"
    ANALYSIS_COMPLETED = "ANALYSIS_COMPLETED"
    ANALYSIS_FAILED = "ANALYSIS_FAILED"

    ML_EXPERIMENT_COMPLETED = "ML_EXPERIMENT_COMPLETED"
    ML_EXPERIMENT_FAILED = "ML_EXPERIMENT_FAILED"

    FORECAST_COMPLETED = "FORECAST_COMPLETED"
    FORECAST_FAILED = "FORECAST_FAILED"

    # Exports & Reports
    EXPORT_COMPLETED = "EXPORT_COMPLETED"
    EXPORT_FAILED = "EXPORT_FAILED"

    REPORT_CREATED = "REPORT_CREATED"
    REPORT_UPDATED = "REPORT_UPDATED"
    REPORT_EXPORTED = "REPORT_EXPORTED"

    # Dashboards
    DASHBOARD_CREATED = "DASHBOARD_CREATED"
    DASHBOARD_UPDATED = "DASHBOARD_UPDATED"

    # Usage & Plans (Phase 20)
    QUOTA_WARNING = "QUOTA_WARNING"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    PLAN_CHANGED = "PLAN_CHANGED"

    # Billing & Subscriptions (Phase 21)
    SUBSCRIPTION_CREATED = "SUBSCRIPTION_CREATED"
    SUBSCRIPTION_ACTIVATED = "SUBSCRIPTION_ACTIVATED"
    SUBSCRIPTION_CHANGED = "SUBSCRIPTION_CHANGED"
    SUBSCRIPTION_CANCELED = "SUBSCRIPTION_CANCELED"
    SUBSCRIPTION_PAST_DUE = "SUBSCRIPTION_PAST_DUE"
    PAYMENT_SUCCEEDED = "PAYMENT_SUCCEEDED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    INVOICE_CREATED = "INVOICE_CREATED"
    INVOICE_OVERDUE = "INVOICE_OVERDUE"


class NotificationCategory(str, Enum):
    COLLABORATION = "COLLABORATION"
    PROJECT = "PROJECT"
    DATA = "DATA"
    ANALYSIS = "ANALYSIS"
    EXPORT = "EXPORT"
    REPORT = "REPORT"
    SECURITY = "SECURITY"
    SYSTEM = "SYSTEM"
    BILLING = "BILLING"


class NotificationPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class NotificationStatus(str, Enum):
    UNREAD = "UNREAD"
    READ = "READ"
    EXPIRED = "EXPIRED"
    ARCHIVED = "ARCHIVED"


class NotificationChannel(str, Enum):
    IN_APP = "IN_APP"
    EMAIL_FUTURE = "EMAIL_FUTURE"
    PUSH_FUTURE = "PUSH_FUTURE"


# ─────────────────────────────────────────────────────────────
# Domain Entities
# ─────────────────────────────────────────────────────────────

class ApplicationEvent(BaseModel):
    """Normalized application event emitted upon real system mutations."""
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:16]}")
    event_type: ApplicationEventType
    actor_user_id: Optional[str] = None
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None

    @field_validator("timestamp", mode="before")
    @classmethod
    def _coerce_timestamp(cls, v: Any) -> str:
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v)


class Notification(BaseModel):
    """
    Enterprise-grade notification entity.
    Communicates system events, collaboration milestones, and job statuses.
    Never acts as an authorization mechanism.
    """
    notification_id: str = Field(default_factory=lambda: f"ntf_{uuid.uuid4().hex[:16]}")
    recipient_user_id: str
    event_id: Optional[str] = None
    notification_type: str
    category: NotificationCategory
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str
    message: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    deep_link: Optional[str] = None
    status: NotificationStatus = NotificationStatus.UNREAD
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    read_at: Optional[str] = None
    expires_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("created_at", "read_at", "expires_at", mode="before")
    @classmethod
    def _coerce_datetimes(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v)


class NotificationPreference(BaseModel):
    """User preferences per notification category and channel."""
    preference_id: str = Field(default_factory=lambda: f"pref_{uuid.uuid4().hex[:12]}")
    user_id: str
    category: NotificationCategory
    channel: NotificationChannel = NotificationChannel.IN_APP
    enabled: bool = True
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class NotificationTemplate(BaseModel):
    """Configuration-driven template definition for safe notification text rendering."""
    template_id: str
    notification_type: str
    title_template: str
    message_template: str
    category: NotificationCategory
    priority: NotificationPriority = NotificationPriority.NORMAL
    deep_link_strategy: Optional[str] = None
    is_security: bool = False


class ActivityFeedItem(BaseModel):
    """User-facing activity feed record distinct from security audit logs."""
    activity_id: str = Field(default_factory=lambda: f"act_{uuid.uuid4().hex[:16]}")
    event_id: Optional[str] = None
    actor_user_id: Optional[str] = None
    actor_name: str = "System"
    action: str
    description: str
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    deep_link: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp", mode="before")
    @classmethod
    def _coerce_activity_timestamp(cls, v: Any) -> str:
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v)


# ─────────────────────────────────────────────────────────────
# Request & Response DTOs
# ─────────────────────────────────────────────────────────────

class UpdatePreferenceRequest(BaseModel):
    category: NotificationCategory
    channel: NotificationChannel = NotificationChannel.IN_APP
    enabled: bool


class NotificationListResponse(BaseModel):
    items: List[Notification]
    total: int = 0
    total_count: int = 0
    page: int = 1
    page_size: int = 50
    unread_count: int = 0
    next_cursor: Optional[str] = None
    has_more: bool = False


class ActivityListResponse(BaseModel):
    items: List[ActivityFeedItem]
    total: int = 0
    total_count: int = 0
    page: int = 1
    page_size: int = 50
    next_cursor: Optional[str] = None
    has_more: bool = False


class UnreadCountResponse(BaseModel):
    unread_count: int
