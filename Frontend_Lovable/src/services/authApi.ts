/**
 * Phase 17: Authentication & Memberships API Service
 */

import {
  AuthResponse,
  CurrentUserResponse,
  SafeSession,
  SecurityAuditEvent,
  User,
  WorkspaceMemberDetail,
  RoleName,
} from "../types/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

let authToken: string | null = null;

export function setAuthToken(token: string | null): void {
  authToken = token;
  if (typeof window !== "undefined") {
    if (token) {
      sessionStorage.setItem("analyzax_token", token);
    } else {
      sessionStorage.removeItem("analyzax_token");
    }
  }
}

export function getAuthToken(): string | null {
  if (authToken) return authToken;
  if (typeof window !== "undefined") {
    authToken = sessionStorage.getItem("analyzax_token");
  }
  return authToken;
}

function getHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...extra,
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errorJson = await res.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }
  if (res.status === 204) {
    return {} as T;
  }
  return res.json();
}

export const authApi = {
  async register(email: string, password: string, displayName: string): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email, password, display_name: displayName }),
    });
    const data = await handleResponse<AuthResponse>(res);
    setAuthToken(data.token);
    return data;
  },

  async login(email: string, password: string): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email, password }),
    });
    const data = await handleResponse<AuthResponse>(res);
    setAuthToken(data.token);
    return data;
  },

  async logout(): Promise<void> {
    try {
      await fetch(`${API_BASE}/api/v1/auth/logout`, {
        method: "POST",
        headers: getHeaders(),
        credentials: "include",
      });
    } finally {
      setAuthToken(null);
    }
  },

  async getMe(): Promise<CurrentUserResponse> {
    const res = await fetch(`${API_BASE}/api/v1/auth/me`, {
      method: "GET",
      headers: getHeaders(),
      credentials: "include",
    });
    return handleResponse<CurrentUserResponse>(res);
  },

  async updateProfile(displayName: string): Promise<User> {
    const res = await fetch(`${API_BASE}/api/v1/auth/profile`, {
      method: "PATCH",
      headers: getHeaders(),
      credentials: "include",
      body: JSON.stringify({ display_name: displayName }),
    });
    return handleResponse<User>(res);
  },

  async changePassword(currentPassword: string, newPassword: string): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE}/api/v1/auth/password/change`, {
      method: "POST",
      headers: getHeaders(),
      credentials: "include",
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    });
    return handleResponse<{ message: string }>(res);
  },

  async requestPasswordReset(email: string): Promise<{ message: string; dev_reset_token?: string }> {
    const res = await fetch(`${API_BASE}/api/v1/auth/password/reset/request`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    return handleResponse<{ message: string; dev_reset_token?: string }>(res);
  },

  async confirmPasswordReset(token: string, newPassword: string): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE}/api/v1/auth/password/reset/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, new_password: newPassword }),
    });
    return handleResponse<{ message: string }>(res);
  },

  async getSessions(): Promise<SafeSession[]> {
    const res = await fetch(`${API_BASE}/api/v1/auth/sessions`, {
      method: "GET",
      headers: getHeaders(),
      credentials: "include",
    });
    return handleResponse<SafeSession[]>(res);
  },

  async revokeSession(sessionId: string): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE}/api/v1/auth/sessions/${sessionId}/revoke`, {
      method: "POST",
      headers: getHeaders(),
      credentials: "include",
    });
    return handleResponse<{ message: string }>(res);
  },

  // ── Workspace Member Management ──
  async getMembers(workspaceId: string): Promise<WorkspaceMemberDetail[]> {
    const res = await fetch(`${API_BASE}/api/v1/workspaces/${workspaceId}/members`, {
      method: "GET",
      headers: getHeaders(),
      credentials: "include",
    });
    return handleResponse<WorkspaceMemberDetail[]>(res);
  },

  async addMember(workspaceId: string, email: string, role: RoleName): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/workspaces/${workspaceId}/members`, {
      method: "POST",
      headers: getHeaders(),
      credentials: "include",
      body: JSON.stringify({ email, role }),
    });
    return handleResponse<any>(res);
  },

  async updateMemberRole(workspaceId: string, memberUserId: string, role: RoleName): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/workspaces/${workspaceId}/members/${memberUserId}`, {
      method: "PATCH",
      headers: getHeaders(),
      credentials: "include",
      body: JSON.stringify({ role }),
    });
    return handleResponse<any>(res);
  },

  async removeMember(workspaceId: string, memberUserId: string): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE}/api/v1/workspaces/${workspaceId}/members/${memberUserId}`, {
      method: "DELETE",
      headers: getHeaders(),
      credentials: "include",
    });
    return handleResponse<{ message: string }>(res);
  },

  async transferOwnership(workspaceId: string, targetUserId: string): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE}/api/v1/workspaces/${workspaceId}/transfer-ownership`, {
      method: "POST",
      headers: getHeaders(),
      credentials: "include",
      body: JSON.stringify({ target_user_id: targetUserId }),
    });
    return handleResponse<{ message: string }>(res);
  },

  async getAuditLogs(workspaceId: string, limit: number = 50): Promise<SecurityAuditEvent[]> {
    const res = await fetch(`${API_BASE}/api/v1/workspaces/${workspaceId}/audit-logs?limit=${limit}`, {
      method: "GET",
      headers: getHeaders(),
      credentials: "include",
    });
    return handleResponse<SecurityAuditEvent[]>(res);
  },
};
