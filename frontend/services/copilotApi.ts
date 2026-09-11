/**
 * AnalyzaX — Phase 25: AI Copilot, Proactive Insights & Metric Governance Client.
 */

import {
  CopilotContext,
  CopilotResponse,
  DashboardPlan,
  Insight,
  InsightSeverity,
  InsightStatus,
  InsightType,
  MetricCalculationResult,
  MetricDefinition,
  MetricStatus,
  MetricVersionRecord,
} from "@/types/copilot";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

// ─────────────────────────────────────────────────────────────
// Copilot Chat & Workflows
// ─────────────────────────────────────────────────────────────

export async function sendCopilotChat(params: {
  message: string;
  context: CopilotContext;
  session_id?: string;
  tone?: string;
  user_workspace_id?: string;
}): Promise<CopilotResponse> {
  const res = await fetch(`${API_BASE}/ai/copilot/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to process Copilot inquiry.");
  }
  return res.json();
}

export async function approveWorkflowStep(
  workflowId: string,
  stepId: string,
  userId: string = "user_default"
) {
  const res = await fetch(`${API_BASE}/ai/copilot/workflows/${workflowId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ step_id: stepId, user_id: userId }),
  });
  if (!res.ok) throw new Error("Failed to approve workflow step.");
  return res.json();
}

export async function cancelWorkflow(workflowId: string) {
  const res = await fetch(`${API_BASE}/ai/copilot/workflows/${workflowId}/cancel`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to cancel workflow.");
  return res.json();
}

export async function executeDashboardPlan(params: {
  plan: DashboardPlan;
  workspace_id: string;
  user_id?: string;
  project_id?: string | null;
}) {
  const res = await fetch(`${API_BASE}/ai/copilot/dashboards/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error("Failed to execute dashboard plan.");
  return res.json();
}

// ─────────────────────────────────────────────────────────────
// Proactive Insights
// ─────────────────────────────────────────────────────────────

export async function listInsights(params: {
  workspace_id: string;
  project_id?: string | null;
  dataset_id?: string | null;
  severity?: InsightSeverity;
  status?: InsightStatus;
  insight_type?: InsightType;
}): Promise<Insight[]> {
  const url = new URL(`${API_BASE}/ai/insights`);
  url.searchParams.set("workspace_id", params.workspace_id);
  if (params.project_id) url.searchParams.set("project_id", params.project_id);
  if (params.dataset_id) url.searchParams.set("dataset_id", params.dataset_id);
  if (params.severity) url.searchParams.set("severity", params.severity);
  if (params.status) url.searchParams.set("status", params.status);
  if (params.insight_type) url.searchParams.set("insight_type", params.insight_type);

  const res = await fetch(url.toString());
  if (!res.ok) throw new Error("Failed to load proactive insights.");
  return res.json();
}

export async function dismissInsight(insightId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/ai/insights/${insightId}/dismiss`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to dismiss insight.");
}

export async function triggerInsightDiscovery(params: {
  workspace_id: string;
  dataset_id: string;
  version_id: string;
  project_id?: string | null;
}): Promise<Insight[]> {
  const res = await fetch(`${API_BASE}/ai/insights/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error("Failed to trigger insight discovery.");
  return res.json();
}

// ─────────────────────────────────────────────────────────────
// Governed Metrics
// ─────────────────────────────────────────────────────────────

export async function listGovernedMetrics(params: {
  workspace_id: string;
  project_id?: string | null;
  status?: MetricStatus;
}): Promise<MetricDefinition[]> {
  const url = new URL(`${API_BASE}/metrics`);
  url.searchParams.set("workspace_id", params.workspace_id);
  if (params.project_id) url.searchParams.set("project_id", params.project_id);
  if (params.status) url.searchParams.set("status", params.status);

  const res = await fetch(url.toString());
  if (!res.ok) throw new Error("Failed to fetch metrics.");
  return res.json();
}

export async function createGovernedMetric(data: {
  workspace_id: string;
  name: string;
  expression: string;
  project_id?: string | null;
  description?: string;
  aggregation?: string;
  unit?: string | null;
  dimensions?: string[];
  synonyms?: string[];
}): Promise<MetricDefinition> {
  const res = await fetch(`${API_BASE}/metrics`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to create metric.");
  }
  return res.json();
}

export async function updateGovernedMetric(
  metricId: string,
  data: {
    name?: string;
    description?: string;
    expression?: string;
    status?: MetricStatus;
    unit?: string | null;
    synonyms?: string[];
    change_summary?: string;
  }
): Promise<MetricDefinition> {
  const res = await fetch(`${API_BASE}/metrics/${metricId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update metric.");
  }
  return res.json();
}

export async function deleteGovernedMetric(metricId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/metrics/${metricId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete metric.");
}

export async function validateMetricFormula(
  expression: string,
  available_columns?: string[]
): Promise<{ is_valid: boolean; error_message?: string; parsed_columns?: string[]; parsed_functions?: string[] }> {
  const res = await fetch(`${API_BASE}/metrics/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ expression, available_columns }),
  });
  if (!res.ok) throw new Error("Validation request failed.");
  return res.json();
}

export async function getMetricVersions(metricId: string): Promise<MetricVersionRecord[]> {
  const res = await fetch(`${API_BASE}/metrics/${metricId}/versions`);
  if (!res.ok) throw new Error("Failed to fetch metric versions.");
  return res.json();
}
