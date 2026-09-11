"""
Domain models for Phase 18: Advanced Team Collaboration, Sharing & Secure Access Management.
Defines WorkspaceInvitations, ResourceShares, ShareLinks, In-App Notifications,
EffectiveAccess evaluations, and collaboration request/response schemas.
"""

from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field, field_validator

from backend.app.engines.auth.models import RoleName, normalize_email, validate_email_format


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class InvitationStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class ShareRecipientType(str, Enum):
    USER = "USER"
    WORKSPACE = "WORKSPACE"
    PROJECT = "PROJECT"
    LINK = "LINK"


class SharePermission(str, Enum):
    VIEW = "VIEW"
    EDIT = "EDIT"
    EXPORT = "EXPORT"
    COMMENT_FUTURE = "COMMENT_FUTURE"  # Reserved for future commenting capability


class ShareStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class ShareLinkMode(str, Enum):
    INTERNAL_AUTHENTICATED = "INTERNAL_AUTHENTICATED"
    PUBLIC_READ_ONLY = "PUBLIC_READ_ONLY"


class ResourceType(str, Enum):
    DATASET = "DATASET"
    DATASET_VERSION = "DATASET_VERSION"
    DASHBOARD = "DASHBOARD"
    REPORT = "REPORT"
    VISUALIZATION = "VISUALIZATION"
    QUERY = "QUERY"
    STATISTICAL_RESULT = "STATISTICAL_RESULT"
    ML_RESULT = "ML_RESULT"
    FORECAST_RESULT = "FORECAST_RESULT"
    AI_ANALYSIS = "AI_ANALYSIS"


class CollaborationEventType(str, Enum):
    INVITATION_CREATED = "INVITATION_CREATED"
    INVITATION_ACCEPTED = "INVITATION_ACCEPTED"
    INVITATION_REVOKED = "INVITATION_REVOKED"
    INVITATION_RESENT = "INVITATION_RESENT"
    MEMBER_ADDED = "MEMBER_ADDED"
    MEMBER_REMOVED = "MEMBER_REMOVED"
    MEMBER_ROLE_CHANGED = "MEMBER_ROLE_CHANGED"
    RESOURCE_SHARED = "RESOURCE_SHARED"
    RESOURCE_SHARE_UPDATED = "RESOURCE_SHARE_UPDATED"
    RESOURCE_SHARE_REVOKED = "RESOURCE_SHARE_REVOKED"
    SHARE_LINK_CREATED = "SHARE_LINK_CREATED"
    SHARE_LINK_REVOKED = "SHARE_LINK_REVOKED"
    SHARE_LINK_ACCESSED = "SHARE_LINK_ACCESSED"
    RESOURCE_ACCESS_DENIED = "RESOURCE_ACCESS_DENIED"


class NotificationType(str, Enum):
    INVITATION_RECEIVED = "INVITATION_RECEIVED"
    INVITATION_ACCEPTED = "INVITATION_ACCEPTED"
    SHARE_RECEIVED = "SHARE_RECEIVED"
    ACCESS_REVOKED = "ACCESS_REVOKED"
    ROLE_CHANGED = "ROLE_CHANGED"
    GENERAL_ALERT = "GENERAL_ALERT"


# ─────────────────────────────────────────────────────────────
# Core Entities
# ─────────────────────────────────────────────────────────────

class WorkspaceInvitation(BaseModel):
    """
    Represents an invitation to join a workspace with a designated role.
    Tokens are stored as SHA-256 hashes; raw tokens are never persisted.
    """
    invitation_id: str = Field(default_factory=lambda: f"inv_{uuid.uuid4().hex[:12]}")
    workspace_id: str
    email: str
    normalized_email: str
    invited_by_user_id: str
    intended_role: RoleName = RoleName.VIEWER
    status: InvitationStatus = InvitationStatus.PENDING
    token_hash: str
    expires_at: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    accepted_at: Optional[str] = None
    revoked_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_format(v)


class ResourceShare(BaseModel):
    """
    Explicitly grants access to an analytical resource (dataset, dashboard, report, etc.)
    for a user, project, or workspace principal without duplicating the asset.
    """
    share_id: str = Field(default_factory=lambda: f"shr_{uuid.uuid4().hex[:12]}")
    resource_type: ResourceType
    resource_id: str
    workspace_id: str
    project_id: Optional[str] = None
    shared_by_user_id: str
    recipient_type: ShareRecipientType = ShareRecipientType.USER
    recipient_id: str  # user_id, project_id, or workspace_id
    permission: SharePermission = SharePermission.VIEW
    status: ShareStatus = ShareStatus.ACTIVE
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None
    revoked_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ShareLink(BaseModel):
    """
    Secure link for sharing an analytical asset.
    Raw tokens are single-use/time-limited and stored as cryptographic SHA-256 hashes.
    """
    share_link_id: str = Field(default_factory=lambda: f"shl_{uuid.uuid4().hex[:12]}")
    share_id: Optional[str] = None
    token_hash: str
    resource_type: ResourceType
    resource_id: str
    workspace_id: str
    project_id: Optional[str] = None
    created_by_user_id: str
    link_mode: ShareLinkMode = ShareLinkMode.INTERNAL_AUTHENTICATED
    permission: SharePermission = SharePermission.VIEW
    status: ShareStatus = ShareStatus.ACTIVE
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None
    revoked_at: Optional[str] = None
    access_count: int = 0
    last_accessed_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Notification(BaseModel):
    """In-app notifications tracking team invitations, shared assets, and role modifications."""
    notification_id: str = Field(default_factory=lambda: f"notif_{uuid.uuid4().hex[:12]}")
    recipient_user_id: str
    type: NotificationType
    title: str
    message: str
    related_resource_type: Optional[ResourceType] = None
    related_resource_id: Optional[str] = None
    action_url: Optional[str] = None
    is_read: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    read_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EffectiveAccess(BaseModel):
    """
    Calculated effective access for a user on a given resource.
    Resolves role inheritance, explicit shares, project memberships, and expiration.
    """
    can_view: bool = False
    can_edit: bool = False
    can_export: bool = False
    access_sources: List[str] = Field(default_factory=list)  # e.g., "WORKSPACE_ROLE (OWNER)", "DIRECT_SHARE"
    effective_permission: Optional[SharePermission] = None
    expires_at: Optional[str] = None
    restrictions: List[str] = Field(default_factory=list)


class CollaborationActivityEvent(BaseModel):
    """Activity event specific to team collaboration and asset sharing."""
    activity_id: str = Field(default_factory=lambda: f"cact_{uuid.uuid4().hex[:16]}")
    workspace_id: str
    project_id: Optional[str] = None
    actor_user_id: str
    event_type: CollaborationEventType
    resource_type: Optional[ResourceType] = None
    resource_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────
# Request / Response DTOs
# ─────────────────────────────────────────────────────────────

class CreateInvitationRequest(BaseModel):
    email: str
    intended_role: RoleName = RoleName.VIEWER
    expires_in_days: int = Field(default=7, ge=1, le=90)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_format(v)


class InvitationResponse(BaseModel):
    invitation_id: str
    workspace_id: str
    workspace_name: Optional[str] = None
    email: str
    intended_role: RoleName
    status: InvitationStatus
    expires_at: str
    created_at: str
    invited_by_user_id: str
    invited_by_name: Optional[str] = None
    preview_token: Optional[str] = None  # Populated only on creation in development mode


class InvitationVerifyResponse(BaseModel):
    invitation_id: str
    workspace_id: str
    workspace_name: str
    email: str
    intended_role: RoleName
    status: InvitationStatus
    expires_at: str
    is_expired: bool
    invited_by_name: str


class CreateShareRequest(BaseModel):
    resource_type: ResourceType
    resource_id: str
    recipient_type: ShareRecipientType = ShareRecipientType.USER
    recipient_id: str
    permission: SharePermission = SharePermission.VIEW
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365)


class UpdateShareRequest(BaseModel):
    permission: Optional[SharePermission] = None
    expires_at: Optional[str] = None


class ResourceShareResponse(BaseModel):
    share_id: str
    resource_type: ResourceType
    resource_id: str
    workspace_id: str
    project_id: Optional[str]
    shared_by_user_id: str
    shared_by_name: Optional[str] = None
    recipient_type: ShareRecipientType
    recipient_id: str
    recipient_name: Optional[str] = None
    permission: SharePermission
    status: ShareStatus
    created_at: str
    expires_at: Optional[str]


class CreateShareLinkRequest(BaseModel):
    resource_type: ResourceType
    resource_id: str
    link_mode: ShareLinkMode = ShareLinkMode.INTERNAL_AUTHENTICATED
    permission: SharePermission = SharePermission.VIEW
    expires_in_days: Optional[int] = Field(default=7, ge=1, le=365)


class ShareLinkResponse(BaseModel):
    share_link_id: str
    resource_type: ResourceType
    resource_id: str
    link_mode: ShareLinkMode
    permission: SharePermission
    status: ShareStatus
    created_at: str
    expires_at: Optional[str]
    access_count: int
    share_url: Optional[str] = None  # Full URL, only returned to creator upon creation


class AddProjectMemberRequest(BaseModel):
    user_id: str
    role: RoleName = RoleName.VIEWER


class UpdateProjectMemberRequest(BaseModel):
    role: RoleName


class ProjectMemberResponse(BaseModel):
    membership_id: str
    project_id: str
    user_id: str
    email: str
    display_name: str
    role: RoleName
    status: str
    created_at: str


class ResourceAccessSummary(BaseModel):
    """Complete summary of who has access to a specific resource."""
    resource_type: ResourceType
    resource_id: str
    workspace_id: str
    project_id: Optional[str]
    direct_shares: List[ResourceShareResponse]
    inherited_workspace_access: List[Dict[str, Any]]
    inherited_project_access: List[Dict[str, Any]]
    active_share_links: List[ShareLinkResponse]
    effective_access: Optional[EffectiveAccess] = None


class SharedResourceView(BaseModel):
    """Restricted presentation projection for publicly or internally shared assets."""
    resource_type: ResourceType
    resource_id: str
    title: str
    description: Optional[str] = None
    permission: SharePermission
    created_at: str
    shared_by_name: str
    is_public: bool
    # Restricted content payload (e.g. dashboard components or report markdown)
    content: Dict[str, Any]
    warnings: List[str] = Field(default_factory=list)
