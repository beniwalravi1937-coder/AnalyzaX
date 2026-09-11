/**
 * Phase 20: Usage Metering, Quotas & Plan Management API Client
 */

import { getAuthToken } from "./authApi";
import {
  Plan,
  PlanChangeResponse,
  PlanComparisonResponse,
  PlanTier,
  UsageHistoryResponse,
  UsageReconciliationReport,
  UsageSummaryResponse,
  WorkspacePlanAssignment,
} from "../types/usage";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

function getHeaders(workspaceId?: string): Record<string, string> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (workspaceId) {
    headers["X-Workspace-Id"] = workspaceId;
  }
  return headers;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errorJson = await res.json();
      errorDetail =
        errorJson.error?.message ||
        errorJson.detail?.message ||
        errorJson.detail ||
        errorDetail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export async function getUsageSummary(workspaceId?: string): Promise<UsageSummaryResponse> {
  const url = new URL(`${API_BASE}/api/v1/usage/summary`);
  if (workspaceId) {
    url.searchParams.set("workspace_id", workspaceId);
  }
  const res = await fetch(url.toString(), {
    headers: getHeaders(workspaceId),
  });
  return handleResponse<UsageSummaryResponse>(res);
}

export async function getUsageHistory(params?: {
  workspaceId?: string;
  metricKey?: string;
  periodKey?: string;
  limit?: number;
  cursor?: string;
}): Promise<UsageHistoryResponse> {
  const url = new URL(`${API_BASE}/api/v1/usage/history`);
  if (params?.workspaceId) url.searchParams.set("workspace_id", params.workspaceId);
  if (params?.metricKey) url.searchParams.set("metric_key", params.metricKey);
  if (params?.periodKey) url.searchParams.set("period_key", params.periodKey);
  if (params?.limit) url.searchParams.set("limit", params.limit.toString());
  if (params?.cursor) url.searchParams.set("cursor", params.cursor);

  const res = await fetch(url.toString(), {
    headers: getHeaders(params?.workspaceId),
  });
  return handleResponse<UsageHistoryResponse>(res);
}

export async function getPlans(): Promise<Plan[]> {
  const res = await fetch(`${API_BASE}/api/v1/plans`, {
    headers: getHeaders(),
  });
  return handleResponse<Plan[]>(res);
}

export async function getPlanComparisonMatrix(): Promise<PlanComparisonResponse> {
  const res = await fetch(`${API_BASE}/api/v1/plans/matrix`, {
    headers: getHeaders(),
  });
  return handleResponse<PlanComparisonResponse>(res);
}

export async function getCurrentPlan(workspaceId?: string): Promise<WorkspacePlanAssignment> {
  const url = new URL(`${API_BASE}/api/v1/plans/current`);
  if (workspaceId) url.searchParams.set("workspace_id", workspaceId);

  const res = await fetch(url.toString(), {
    headers: getHeaders(workspaceId),
  });
  return handleResponse<WorkspacePlanAssignment>(res);
}

export async function changeWorkspacePlan(
  workspaceId: string,
  planTier: PlanTier,
  reason?: string
): Promise<PlanChangeResponse> {
  const res = await fetch(`${API_BASE}/api/v1/workspaces/${workspaceId}/plan`, {
    method: "POST",
    headers: getHeaders(workspaceId),
    body: JSON.stringify({
      plan_tier: planTier,
      reason: reason || `Updated plan to ${planTier}`,
    }),
  });
  return handleResponse<PlanChangeResponse>(res);
}

export async function reconcileUsage(
  workspaceId?: string,
  periodKey?: string
): Promise<UsageReconciliationReport> {
  const url = new URL(`${API_BASE}/api/v1/usage/reconcile`);
  if (workspaceId) url.searchParams.set("workspace_id", workspaceId);
  if (periodKey) url.searchParams.set("period_key", periodKey);

  const res = await fetch(url.toString(), {
    headers: getHeaders(workspaceId),
  });
  return handleResponse<UsageReconciliationReport>(res);
}
