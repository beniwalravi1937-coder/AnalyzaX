/**
 * Frontend types for Phase 18: Advanced Team Collaboration, Sharing & Secure Access Management.
 */

export type InvitationStatus = "PENDING" | "ACCEPTED" | "EXPIRED" | "REVOKED";

export type ShareRecipientType = "USER" | "WORKSPACE" | "PROJECT" | "LINK";

export type SharePermission = "VIEW" | "EDIT" | "EXPORT" | "ADMIN";

export type ShareStatus = "ACTIVE" | "REVOKED" | "EXPIRED";

export type ShareLinkMode = "INTERNAL_AUTHENTICATED" | "PUBLIC_READ_ONLY";

export type CollaborationResourceType =
  | "DATASET"
  | "DATASET_VERSION"
  | "DASHBOARD"
  | "REPORT"
  | "VISUALIZATION"
  | "QUERY"
  | "STATISTICAL_RESULT"
  | "ML_RESULT"
  | "FORECAST_RESULT"
  | "AI_ANALYSIS"
  | "EXPORT";

export type NotificationType =
  | "INVITATION_RECEIVED"
  | "INVITATION_ACCEPTED"
  | "SHARE_RECEIVED"
  | "ACCESS_REVOKED"
  | "ROLE_CHANGED"
  | "SYSTEM_ALERT";

export interface WorkspaceInvitation {
  invitation_id: string;
  workspace_id: string;
  email: string;
  invited_by_user_id: string;
  intended_role: string;
  status: InvitationStatus;
  expires_at: string;
  created_at: string;
  accepted_at?: string | null;
  revoked_at?: string | null;
  metadata: Record<string, any>;
}

export interface CreateInvitationRequest {
  email: string;
  intended_role: string;
  expires_in_days?: number;
  metadata?: Record<string, any>;
}

export interface InvitationResponse {
  invitation_id: string;
  workspace_id: string;
  workspace_name: string;
  email: string;
  intended_role: string;
  status: InvitationStatus;
  invited_by_user_id: string;
  inviter_name: string;
  expires_at: string;
  created_at: string;
  accepted_at?: string | null;
  revoked_at?: string | null;
  preview_token?: string | null;
}

export interface VerifyInvitationResponse {
  invitation_id: string;
  workspace_id: string;
  workspace_name: string;
  email: string;
  intended_role: string;
  status: InvitationStatus;
  inviter_name: string;
  expires_at: string;
  is_expired: boolean;
}

export interface ResourceShare {
  share_id: string;
  resource_type: CollaborationResourceType;
  resource_id: string;
  workspace_id: string;
  project_id?: string | null;
  shared_by_user_id: string;
  recipient_type: ShareRecipientType;
  recipient_id: string;
  permission: SharePermission;
  status: ShareStatus;
  created_at: string;
  updated_at: string;
  expires_at?: string | null;
  revoked_at?: string | null;
  metadata: Record<string, any>;
}

export interface CreateShareRequest {
  resource_type: CollaborationResourceType;
  resource_id: string;
  recipient_type: ShareRecipientType;
  recipient_id: string;
  permission: SharePermission;
  expires_in_hours?: number | null;
  metadata?: Record<string, any>;
}

export interface ShareLink {
  share_link_id: string;
  share_id: string;
  resource_type: CollaborationResourceType;
  resource_id: string;
  workspace_id: string;
  project_id?: string | null;
  link_mode: ShareLinkMode;
  permission: SharePermission;
  created_by_user_id: string;
  status: ShareStatus;
  expires_at?: string | null;
  access_count: number;
  created_at: string;
  revoked_at?: string | null;
  share_url?: string | null;
}

export interface CreateShareLinkRequest {
  resource_type: CollaborationResourceType;
  resource_id: string;
  link_mode?: ShareLinkMode;
  permission?: SharePermission;
  expires_in_hours?: number | null;
}

export interface EffectiveAccess {
  can_view: boolean;
  can_edit: boolean;
  can_export: boolean;
  access_sources: string[];
  expires_at?: string | null;
  restrictions: Record<string, any>;
}

export interface AccessEntry {
  principal_id: string;
  principal_name: string;
  principal_type: string;
  source: string;
  permission: SharePermission;
  expires_at?: string | null;
  share_id?: string | null;
  is_direct: boolean;
}

export interface ResourceAccessSummary {
  resource_id: string;
  resource_type: CollaborationResourceType;
  direct_shares: AccessEntry[];
  inherited_access: AccessEntry[];
  active_links: ShareLink[];
}

export interface SharedResourceView {
  resource_id: string;
  resource_type: CollaborationResourceType;
  title: string;
  is_public: boolean;
  permission: SharePermission;
  can_export: boolean;
  content: Record<string, any>;
  masked_dependencies: string[];
}

export interface InAppNotification {
  notification_id: string;
  recipient_user_id: string;
  type: NotificationType;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
  read_at?: string | null;
  metadata: Record<string, any>;
}

export interface ProjectMemberDetail {
  project_id: string;
  user_id: string;
  role: string;
  joined_at: string;
  display_name: string;
  email: string;
}

export interface AddProjectMemberRequest {
  user_id: string;
  role?: string;
}
