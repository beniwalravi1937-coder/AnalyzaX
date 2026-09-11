// API Client for Phase 14 Dashboard, Insight Workspace, and Analytical Storytelling

import {
  ComponentCreateRequest,
  ComponentUpdateRequest,
  Dashboard,
  DashboardComponent,
  DashboardCreateRequest,
  DashboardDataResponse,
  DashboardFilter,
  DashboardUpdateRequest,
  DashboardVersion,
} from "@/types/dashboard";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const err = await response.json();
      errorDetail = err.detail || errorDetail;
    } catch {
      // fallback
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export async function listDashboards(datasetId?: string, search?: string): Promise<Dashboard[]> {
  const params = new URLSearchParams();
  if (datasetId) params.append("dataset_id", datasetId);
  if (search) params.append("search", search);
  const q = params.toString() ? `?${params.toString()}` : "";
  return request<Dashboard[]>(`/dashboards${q}`);
}

export async function createDashboard(payload: DashboardCreateRequest): Promise<Dashboard> {
  return request<Dashboard>("/dashboards", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getDashboard(dashboardId: string): Promise<Dashboard> {
  return request<Dashboard>(`/dashboards/${dashboardId}`);
}

export async function updateDashboard(
  dashboardId: string,
  payload: DashboardUpdateRequest
): Promise<Dashboard> {
  return request<Dashboard>(`/dashboards/${dashboardId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteDashboard(dashboardId: string): Promise<{ deleted: boolean }> {
  return request<{ deleted: boolean }>(`/dashboards/${dashboardId}`, {
    method: "DELETE",
  });
}

export async function duplicateDashboard(
  dashboardId: string,
  newName?: string
): Promise<Dashboard> {
  return request<Dashboard>(`/dashboards/${dashboardId}/duplicate`, {
    method: "POST",
    body: JSON.stringify({ new_name: newName }),
  });
}

export async function listVersions(dashboardId: string): Promise<DashboardVersion[]> {
  return request<DashboardVersion[]>(`/dashboards/${dashboardId}/versions`);
}

export async function getVersion(
  dashboardId: string,
  versionNumber: number
): Promise<DashboardVersion> {
  return request<DashboardVersion>(`/dashboards/${dashboardId}/versions/${versionNumber}`);
}

export async function restoreVersion(
  dashboardId: string,
  versionNumber: number
): Promise<Dashboard> {
  return request<Dashboard>(`/dashboards/${dashboardId}/versions/${versionNumber}/restore`, {
    method: "POST",
  });
}

export async function addComponent(
  dashboardId: string,
  payload: ComponentCreateRequest
): Promise<DashboardComponent> {
  return request<DashboardComponent>(`/dashboards/${dashboardId}/components`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateComponent(
  dashboardId: string,
  componentId: string,
  payload: ComponentUpdateRequest
): Promise<DashboardComponent> {
  return request<DashboardComponent>(`/dashboards/${dashboardId}/components/${componentId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteComponent(
  dashboardId: string,
  componentId: string
): Promise<{ deleted: boolean }> {
  return request<{ deleted: boolean }>(`/dashboards/${dashboardId}/components/${componentId}`, {
    method: "DELETE",
  });
}

export async function duplicateComponent(
  dashboardId: string,
  componentId: string
): Promise<DashboardComponent> {
  return request<DashboardComponent>(
    `/dashboards/${dashboardId}/components/${componentId}/duplicate`,
    {
      method: "POST",
    }
  );
}

export async function getDashboardData(dashboardId: string): Promise<DashboardDataResponse> {
  return request<DashboardDataResponse>(`/dashboards/${dashboardId}/data`);
}

export async function refreshDashboard(
  dashboardId: string,
  componentIds?: string[]
): Promise<DashboardDataResponse> {
  return request<DashboardDataResponse>(`/dashboards/${dashboardId}/refresh`, {
    method: "POST",
    body: JSON.stringify({ component_ids: componentIds }),
  });
}

export async function validateFilter(
  dashboardId: string,
  filter: DashboardFilter,
  datasetId: string,
  datasetVersionId: string
): Promise<{ valid: boolean; message: string }> {
  return request<{ valid: boolean; message: string }>(`/dashboards/${dashboardId}/filters/validate`, {
    method: "POST",
    body: JSON.stringify({
      filter,
      dataset_id: datasetId,
      dataset_version_id: datasetVersionId,
    }),
  });
}

export async function exportDashboard(dashboardId: string, format = "json"): Promise<any> {
  return request<any>(`/dashboards/${dashboardId}/export?format=${format}`);
}
