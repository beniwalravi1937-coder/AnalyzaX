/**
 * Phase 19: Notification & Activity API Service
 * Handles user notifications, read/unread status, preferences, and activity feeds.
 */

import { getAuthToken } from "./authApi";
import {
  ActivityListResponse,
  ApplicationEventType,
  Notification,
  NotificationCategory,
  NotificationListResponse,
  NotificationPreference,
  NotificationStatus,
  UnreadCountResponse,
  UpdatePreferenceRequest,
} from "../types/notifications";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

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
  return res.json();
}

export interface ListNotificationsParams {
  category?: NotificationCategory;
  status?: NotificationStatus;
  unread_only?: boolean;
  search?: string;
  limit?: number;
  cursor?: string;
}

export interface ListActivityParams {
  eventType?: ApplicationEventType;
  actorUserId?: string;
  limit?: number;
  cursor?: string;
}

export const notificationApi = {
  // ─────────────────────────────────────────────────────────────
  // Notifications
  // ─────────────────────────────────────────────────────────────
  async listNotifications(params?: ListNotificationsParams): Promise<NotificationListResponse> {
    const query = new URLSearchParams();
    if (params?.category) query.append("category", params.category);
    if (params?.status) query.append("status", params.status);
    if (params?.unread_only) query.append("unread_only", "true");
    if (params?.search) query.append("search", params.search);
    if (params?.limit) query.append("limit", params.limit.toString());
    if (params?.cursor) query.append("cursor", params.cursor);

    const qs = query.toString() ? `?${query.toString()}` : "";
    const res = await fetch(`${API_BASE}/api/v1/notifications${qs}`, {
      headers: getHeaders(),
    });
    return handleResponse<NotificationListResponse>(res);
  },

  async getUnreadCount(): Promise<number> {
    const res = await fetch(`${API_BASE}/api/v1/notifications/unread-count`, {
      headers: getHeaders(),
    });
    const data = await handleResponse<UnreadCountResponse>(res);
    return data.unread_count;
  },

  async getNotification(notificationId: string): Promise<Notification> {
    const res = await fetch(`${API_BASE}/api/v1/notifications/${notificationId}`, {
      headers: getHeaders(),
    });
    return handleResponse<Notification>(res);
  },

  async markAsRead(notificationId: string): Promise<Notification> {
    const res = await fetch(`${API_BASE}/api/v1/notifications/${notificationId}/read`, {
      method: "POST",
      headers: getHeaders(),
    });
    return handleResponse<Notification>(res);
  },

  async markAsUnread(notificationId: string): Promise<Notification> {
    const res = await fetch(`${API_BASE}/api/v1/notifications/${notificationId}/unread`, {
      method: "POST",
      headers: getHeaders(),
    });
    return handleResponse<Notification>(res);
  },

  async markAllAsRead(): Promise<{ message: string; count: number }> {
    const res = await fetch(`${API_BASE}/api/v1/notifications/read-all`, {
      method: "POST",
      headers: getHeaders(),
    });
    return handleResponse<{ message: string; count: number }>(res);
  },

  async archiveNotification(notificationId: string): Promise<Notification> {
    const res = await fetch(`${API_BASE}/api/v1/notifications/${notificationId}/archive`, {
      method: "POST",
      headers: getHeaders(),
    });
    return handleResponse<Notification>(res);
  },

  async runCleanup(): Promise<{ message: string; cleaned_count: number }> {
    const res = await fetch(`${API_BASE}/api/v1/notifications/cleanup`, {
      method: "POST",
      headers: getHeaders(),
    });
    return handleResponse<{ message: string; cleaned_count: number }>(res);
  },

  // ─────────────────────────────────────────────────────────────
  // Notification Preferences
  // ─────────────────────────────────────────────────────────────
  async getPreferences(): Promise<NotificationPreference[]> {
    const res = await fetch(`${API_BASE}/api/v1/notification-preferences`, {
      headers: getHeaders(),
    });
    return handleResponse<NotificationPreference[]>(res);
  },

  async updatePreference(req: UpdatePreferenceRequest): Promise<NotificationPreference> {
    const res = await fetch(`${API_BASE}/api/v1/notification-preferences`, {
      method: "PATCH",
      headers: getHeaders(),
      body: JSON.stringify(req),
    });
    return handleResponse<NotificationPreference>(res);
  },

  // ─────────────────────────────────────────────────────────────
  // Activity Center
  // ─────────────────────────────────────────────────────────────
  async getProjectActivity(
    projectId: string,
    params?: ListActivityParams
  ): Promise<ActivityListResponse> {
    const query = new URLSearchParams();
    if (params?.eventType) query.append("event_type", params.eventType);
    if (params?.actorUserId) query.append("actor_user_id", params.actorUserId);
    if (params?.limit) query.append("limit", params.limit.toString());
    if (params?.cursor) query.append("cursor", params.cursor);

    const qs = query.toString() ? `?${query.toString()}` : "";
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/activity${qs}`, {
      headers: getHeaders(),
    });
    return handleResponse<ActivityListResponse>(res);
  },

  async getWorkspaceActivity(
    workspaceId: string,
    params?: ListActivityParams
  ): Promise<ActivityListResponse> {
    const query = new URLSearchParams();
    if (params?.eventType) query.append("event_type", params.eventType);
    if (params?.actorUserId) query.append("actor_user_id", params.actorUserId);
    if (params?.limit) query.append("limit", params.limit.toString());
    if (params?.cursor) query.append("cursor", params.cursor);

    const qs = query.toString() ? `?${query.toString()}` : "";
    const res = await fetch(`${API_BASE}/api/v1/workspaces/${workspaceId}/activity${qs}`, {
      headers: getHeaders(),
    });
    return handleResponse<ActivityListResponse>(res);
  },
};
