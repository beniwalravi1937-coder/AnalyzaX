/**
 * AnalyzaX — AI Analyst API Client (Phase 13)
 * Strongly typed HTTP client interacting with /api/v1/ai-analyst endpoints.
 */

import {
  AnalysisPlan,
  AnalystChatRequest,
  AnalystChatResponse,
  AnalystMessage,
  AnalystSession,
  ToolDefinition,
} from "@/types/ai_analyst";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

export async function sendChatMessage(request: AnalystChatRequest): Promise<AnalystChatResponse> {
  const res = await fetch(`${API_BASE}/ai-analyst/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail?.message || `HTTP ${res.status}: Failed to process inquiry.`);
  }
  return res.json();
}

export async function createAnalysisPlan(
  datasetId: string,
  question: string,
  versionId?: string
): Promise<AnalysisPlan> {
  const res = await fetch(`${API_BASE}/ai-analyst/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      dataset_id: datasetId,
      question,
      dataset_version_id: versionId,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail?.message || "Failed to create analysis plan.");
  }
  return res.json();
}

export async function listAnalystSessions(): Promise<AnalystSession[]> {
  const res = await fetch(`${API_BASE}/ai-analyst/sessions`);
  if (!res.ok) throw new Error("Failed to fetch sessions.");
  return res.json();
}

export async function createAnalystSession(
  title: string = "New Analysis",
  datasetId?: string,
  datasetVersionId?: string
): Promise<AnalystSession> {
  const res = await fetch(`${API_BASE}/ai-analyst/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title,
      dataset_id: datasetId,
      dataset_version_id: datasetVersionId,
    }),
  });
  if (!res.ok) throw new Error("Failed to create session.");
  return res.json();
}

export async function getAnalystSession(sessionId: string): Promise<AnalystSession> {
  const res = await fetch(`${API_BASE}/ai-analyst/sessions/${sessionId}`);
  if (!res.ok) throw new Error(`Failed to load session ${sessionId}.`);
  return res.json();
}

export async function deleteAnalystSession(sessionId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/ai-analyst/sessions/${sessionId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete session.");
}

export async function getAnalystSessionMessages(sessionId: string): Promise<AnalystMessage[]> {
  const res = await fetch(`${API_BASE}/ai-analyst/sessions/${sessionId}/messages`);
  if (!res.ok) throw new Error("Failed to load messages.");
  return res.json();
}

export async function confirmCleaningProposal(sessionId: string, proposalId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/ai-analyst/sessions/${sessionId}/confirm-cleaning`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ proposal_id: proposalId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail?.message || "Failed to apply cleaning proposal.");
  }
  return res.json();
}

export async function listAnalystTools(): Promise<ToolDefinition[]> {
  const res = await fetch(`${API_BASE}/ai-analyst/tools`);
  if (!res.ok) throw new Error("Failed to list tools.");
  return res.json();
}
