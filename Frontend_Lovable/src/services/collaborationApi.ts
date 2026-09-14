/**
 * Phase 18 Collaboration API Service
 * Handles invitations, project membership, direct shares, share links,
 * shared views, and in-app notifications.
 */

import { getAuthToken } from "./authApi";
import {
  AddProjectMemberRequest,
  CreateInvitationRequest,
  CreateShareLinkRequest,
  CreateShareRequest,
  EffectiveAccess,
  InAppNotification,
  InvitationResponse,
  ProjectMemberDetail,
  ResourceAccessSummary,
  ResourceShare,
  ShareLink,
  SharedResourceView,
  VerifyInvitationResponse,
  WorkspaceInvitation,
} from "../types/collaboration";

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

export const collaborationApi = {
  // ─────────────────────────────────────────────────────────────
  // Workspace Invitations
  // ─────────────────────────────────────────────────────────────
  async createInvitation(
    workspaceId: string,
    req: CreateInvitationRequest
  ): Promise<InvitationResponse> {
    const res = await fetch(`${API_BASE}/api/v1/workspaces/${workspaceId}/invitations`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(req),
    });
    return handleResponse<InvitationResponse>(res);
  },

  async listInvitations(
    workspaceId: string,
    status?: string
  ): Promise<InvitationResponse[]> {
    const query = status ? `?status=${status}` : "";
    const res = await fetch(
      `${API_BASE}/api/v1/workspaces/${workspaceId}/invitations${query}`,
      {
        headers: getHeaders(),
      }
    );
    return handleResponse<InvitationResponse[]>(res);
  },

  async verifyInvitation(token: string): Promise<VerifyInvitationResponse> {
    const res = await fetch(`${API_BASE}/api/v1/invitations/verify/${token}`, {
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse<VerifyInvitationResponse>(res);
  },

  async acceptInvitation(
    invitationId: string,
    token: string
  ): Promise<{ message: string; role: string; workspace_id: string }> {
    const res = await fetch(`${API_BASE}/api/v1/invitations/${invitationId}/accept`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ token }),
    });
    return handleResponse<{ message: string; role: string; workspace_id: string }>(res);
  },

  async revokeInvitation(invitationId: string): Promise<WorkspaceInvitation> {
    const res = await fetch(`${API_BASE}/api/v1/invitations/${invitationId}/revoke`, {
      method: "POST",
      headers: getHeaders(),
    });
    return handleResponse<WorkspaceInvitation>(res);
  },

  async resendInvitation(invitationId: string): Promise<InvitationResponse> {
    const res = await fetch(`${API_BASE}/api/v1/invitations/${invitationId}/resend`, {
      method: "POST",
      headers: getHeaders(),
    });
    return handleResponse<InvitationResponse>(res);
  },

  // ─────────────────────────────────────────────────────────────
  // Project Membership
  // ─────────────────────────────────────────────────────────────
  async listProjectMembers(projectId: string): Promise<ProjectMemberDetail[]> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/members`, {
      headers: getHeaders(),
    });
    return handleResponse<ProjectMemberDetail[]>(res);
  },

  async addProjectMember(
    projectId: string,
    req: AddProjectMemberRequest
  ): Promise<ProjectMemberDetail> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/members`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(req),
    });
    return handleResponse<ProjectMemberDetail>(res);
  },

  async removeProjectMember(projectId: string, userId: string): Promise<{ success: boolean }> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/members/${userId}`, {
      method: "DELETE",
      headers: getHeaders(),
    });
    return handleResponse<{ success: boolean }>(res);
  },

  // ─────────────────────────────────────────────────────────────
  // Resource Sharing & Access Control
  // ─────────────────────────────────────────────────────────────
  async createShare(req: CreateShareRequest): Promise<ResourceShare> {
    const res = await fetch(`${API_BASE}/api/v1/shares`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(req),
    });
    return handleResponse<ResourceShare>(res);
  },

  async getResourceAccess(
    resourceType: string,
    resourceId: string
  ): Promise<ResourceAccessSummary> {
    const res = await fetch(
      `${API_BASE}/api/v1/resources/${resourceType}/${resourceId}/access`,
      {
        headers: getHeaders(),
      }
    );
    return handleResponse<ResourceAccessSummary>(res);
  },

  async revokeShare(shareId: string): Promise<{ success: boolean }> {
    const res = await fetch(`${API_BASE}/api/v1/shares/${shareId}/revoke`, {
      method: "POST",
      headers: getHeaders(),
    });
    return handleResponse<{ success: boolean }>(res);
  },

  // ─────────────────────────────────────────────────────────────
  // Share Links
  // ─────────────────────────────────────────────────────────────
  async createShareLink(req: CreateShareLinkRequest): Promise<ShareLink> {
    const res = await fetch(
      `${API_BASE}/api/v1/resources/${req.resource_type}/${req.resource_id}/share-links`,
      {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(req),
      }
    );
    return handleResponse<ShareLink>(res);
  },

  async listShareLinks(resourceType: string, resourceId: string): Promise<ShareLink[]> {
    const res = await fetch(
      `${API_BASE}/api/v1/resources/${resourceType}/${resourceId}/share-links`,
      {
        headers: getHeaders(),
      }
    );
    return handleResponse<ShareLink[]>(res);
  },

  async revokeShareLink(shareLinkId: string): Promise<{ success: boolean }> {
    const res = await fetch(`${API_BASE}/api/v1/share-links/${shareLinkId}/revoke`, {
      method: "POST",
      headers: getHeaders(),
    });
    return handleResponse<{ success: boolean }>(res);
  },

  // ─────────────────────────────────────────────────────────────
  // Shared Resource Resolution (Public / Authenticated)
  // ─────────────────────────────────────────────────────────────
  async getSharedResource(token: string): Promise<SharedResourceView> {
    const res = await fetch(`${API_BASE}/api/v1/shared/${token}`, {
      headers: getHeaders(),
    });
    return handleResponse<SharedResourceView>(res);
  },

  // ─────────────────────────────────────────────────────────────
  // In-App Notifications
  // ─────────────────────────────────────────────────────────────
  async listNotifications(unreadOnly = false): Promise<InAppNotification[]> {
    const query = unreadOnly ? "?unread_only=true" : "";
    const res = await fetch(`${API_BASE}/api/v1/notifications${query}`, {
      headers: getHeaders(),
    });
    return handleResponse<InAppNotification[]>(res);
  },

  async markNotificationRead(notificationId: string): Promise<{ success: boolean }> {
    const res = await fetch(`${API_BASE}/api/v1/notifications/${notificationId}/read`, {
      method: "POST",
      headers: getHeaders(),
    });
    return handleResponse<{ success: boolean }>(res);
  },

  async markAllNotificationsRead(): Promise<{ success: boolean; count: number }> {
    const res = await fetch(`${API_BASE}/api/v1/notifications/read-all`, {
      method: "POST",
      headers: getHeaders(),
    });
    return handleResponse<{ success: boolean; count: number }>(res);
  },
};
