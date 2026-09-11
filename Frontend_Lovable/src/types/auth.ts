/**
 * Phase 17: Authentication & Authorization TypeScript Interfaces
 */

export type UserStatus = "ACTIVE" | "SUSPENDED" | "DISABLED" | "PENDING_VERIFICATION";

export type RoleName = "OWNER" | "ADMIN" | "EDITOR" | "ANALYST" | "VIEWER";

export interface User {
  user_id: string;
  email: string;
  display_name: string;
  status: UserStatus;
  created_at: string;
  last_login_at?: string;
  email_verified_at?: string;
}

export interface SafeSession {
  session_id: string;
  created_at: string;
  expires_at: string;
  last_seen_at: string;
  is_current: boolean;
  ip_address?: string;
  user_agent?: string;
}

export interface WorkspaceMembership {
  workspace_id: string;
  workspace_name: string;
  workspace_slug: string;
  role: RoleName;
  status: string;
}

export interface CurrentUserResponse {
  user: User;
  workspace_memberships: WorkspaceMembership[];
  permissions_summary: string[];
}

export interface AuthResponse {
  user: User;
  token: string;
  expires_at: string;
  workspace_id: string;
  project_id: string;
}

export interface WorkspaceMemberDetail {
  membership_id: string;
  workspace_id: string;
  user_id: string;
  email: string;
  display_name: string;
  role: RoleName;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface SecurityAuditEvent {
  event_id: string;
  user_id?: string;
  workspace_id?: string;
  project_id?: string;
  event_type: string;
  timestamp: string;
  result: string;
  metadata: Record<string, any>;
  request_ip?: string;
}
