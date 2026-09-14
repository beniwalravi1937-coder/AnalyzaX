/**
 * Phase 19: Enterprise Notifications, Activity Center & Preferences Types
 */

export enum ApplicationEventType {
  // Auth & Identity
  USER_REGISTERED = "USER_REGISTERED",
  USER_LOGIN = "USER_LOGIN",
  USER_LOGOUT = "USER_LOGOUT",
  PASSWORD_CHANGED = "PASSWORD_CHANGED",
  PASSWORD_RESET = "PASSWORD_RESET",
  SESSION_REVOKED = "SESSION_REVOKED",
  SECURITY_ALERT = "SECURITY_ALERT",

  // Workspace & Project
  PROJECT_CREATED = "PROJECT_CREATED",
  PROJECT_ARCHIVED = "PROJECT_ARCHIVED",
  PROJECT_RESTORED = "PROJECT_RESTORED",

  // Team Membership & Invitations
  INVITATION_CREATED = "INVITATION_CREATED",
  INVITATION_ACCEPTED = "INVITATION_ACCEPTED",
  INVITATION_REVOKED = "INVITATION_REVOKED",
  MEMBER_ADDED = "MEMBER_ADDED",
  MEMBER_REMOVED = "MEMBER_REMOVED",
  MEMBER_ROLE_CHANGED = "MEMBER_ROLE_CHANGED",

  // Sharing & Collaboration
  RESOURCE_SHARED = "RESOURCE_SHARED",
  RESOURCE_SHARE_REVOKED = "RESOURCE_SHARE_REVOKED",
  SHARE_LINK_CREATED = "SHARE_LINK_CREATED",
  SHARE_LINK_REVOKED = "SHARE_LINK_REVOKED",

  // Datasets & Versions
  DATASET_CREATED = "DATASET_CREATED",
  DATASET_VERSION_CREATED = "DATASET_VERSION_CREATED",
  DATASET_ARCHIVED = "DATASET_ARCHIVED",
  DATASET_RESTORED = "DATASET_RESTORED",

  // Analytical Jobs & Engines
  ANALYSIS_STARTED = "ANALYSIS_STARTED",
  ANALYSIS_COMPLETED = "ANALYSIS_COMPLETED",
  ANALYSIS_FAILED = "ANALYSIS_FAILED",

  ML_EXPERIMENT_COMPLETED = "ML_EXPERIMENT_COMPLETED",
  ML_EXPERIMENT_FAILED = "ML_EXPERIMENT_FAILED",

  FORECAST_COMPLETED = "FORECAST_COMPLETED",
  FORECAST_FAILED = "FORECAST_FAILED",

  // Exports & Reports
  EXPORT_COMPLETED = "EXPORT_COMPLETED",
  EXPORT_FAILED = "EXPORT_FAILED",

  REPORT_CREATED = "REPORT_CREATED",
  REPORT_UPDATED = "REPORT_UPDATED",
  REPORT_EXPORTED = "REPORT_EXPORTED",

  // Dashboards
  DASHBOARD_CREATED = "DASHBOARD_CREATED",
  DASHBOARD_UPDATED = "DASHBOARD_UPDATED",
}

export enum NotificationCategory {
  COLLABORATION = "COLLABORATION",
  PROJECT = "PROJECT",
  DATA = "DATA",
  ANALYSIS = "ANALYSIS",
  EXPORT = "EXPORT",
  REPORT = "REPORT",
  SECURITY = "SECURITY",
  SYSTEM = "SYSTEM",
}

export enum NotificationPriority {
  LOW = "LOW",
  NORMAL = "NORMAL",
  HIGH = "HIGH",
  CRITICAL = "CRITICAL",
}

export enum NotificationStatus {
  UNREAD = "UNREAD",
  READ = "READ",
  EXPIRED = "EXPIRED",
  ARCHIVED = "ARCHIVED",
}

export enum NotificationChannel {
  IN_APP = "IN_APP",
  EMAIL_FUTURE = "EMAIL_FUTURE",
  PUSH_FUTURE = "PUSH_FUTURE",
}

export interface Notification {
  notification_id: string;
  recipient_user_id: string;
  event_id?: string | null;
  notification_type: string;
  category: NotificationCategory;
  priority: NotificationPriority;
  title: string;
  message: string;
  resource_type?: string | null;
  resource_id?: string | null;
  workspace_id?: string | null;
  project_id?: string | null;
  deep_link?: string | null;
  status: NotificationStatus;
  created_at: string;
  read_at?: string | null;
  expires_at?: string | null;
  metadata?: Record<string, any>;
}

export interface NotificationPreference {
  preference_id: string;
  user_id: string;
  category: NotificationCategory;
  channel: NotificationChannel;
  enabled: boolean;
  updated_at: string;
}

export interface UpdatePreferenceRequest {
  category: NotificationCategory;
  channel?: NotificationChannel;
  enabled: boolean;
}

export interface ActivityFeedItem {
  activity_id: string;
  event_id?: string | null;
  actor_user_id?: string | null;
  actor_name: string;
  action: string;
  description: string;
  workspace_id?: string | null;
  project_id?: string | null;
  resource_type?: string | null;
  resource_id?: string | null;
  resource_name?: string | null;
  deep_link?: string | null;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface NotificationListResponse {
  items: Notification[];
  total: number;
  total_count: number;
  page: number;
  page_size: number;
  unread_count: number;
  next_cursor?: string | null;
  has_more: boolean;
}

export interface ActivityListResponse {
  items: ActivityFeedItem[];
  total: number;
  total_count: number;
  page: number;
  page_size: number;
  next_cursor?: string | null;
  has_more: boolean;
}

export interface UnreadCountResponse {
  unread_count: number;
}
