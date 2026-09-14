// API Client for Phase 15 Advanced Export, Reporting & Presentation Engine

import {
  ExportJob,
  ExportRequest,
  ReportGenerateRequest,
  ReportTemplateMeta,
} from "@/types/exports";

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
      // ignore parse errors
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

// ─────────────────────────────────────────────────────────────
// Export CRUD
// ─────────────────────────────────────────────────────────────

export async function createExport(req: ExportRequest): Promise<ExportJob> {
  return request<ExportJob>("/exports", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function listExports(datasetId?: string): Promise<ExportJob[]> {
  const params = datasetId ? `?dataset_id=${encodeURIComponent(datasetId)}` : "";
  return request<ExportJob[]>(`/exports${params}`);
}

export async function getExport(jobId: string): Promise<ExportJob> {
  return request<ExportJob>(`/exports/${encodeURIComponent(jobId)}`);
}

export async function deleteExport(jobId: string): Promise<{ deleted: boolean; job_id: string }> {
  return request<{ deleted: boolean; job_id: string }>(
    `/exports/${encodeURIComponent(jobId)}`,
    { method: "DELETE" }
  );
}

// ─────────────────────────────────────────────────────────────
// Download
// ─────────────────────────────────────────────────────────────

export function getDownloadUrl(jobId: string): string {
  return `${API_BASE}/exports/${encodeURIComponent(jobId)}/download`;
}

export async function downloadExport(jobId: string): Promise<void> {
  const url = getDownloadUrl(jobId);
  const link = document.createElement("a");
  link.href = url;
  link.download = "";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// ─────────────────────────────────────────────────────────────
// Reports
// ─────────────────────────────────────────────────────────────

export async function generateReport(req: ReportGenerateRequest): Promise<ExportJob> {
  return request<ExportJob>("/exports/reports", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function listReportTemplates(): Promise<ReportTemplateMeta[]> {
  return request<ReportTemplateMeta[]>("/exports/reports/templates");
}

// ─────────────────────────────────────────────────────────────
// Cleanup
// ─────────────────────────────────────────────────────────────

export async function cleanupExpired(): Promise<{ removed: number; message: string }> {
  return request<{ removed: number; message: string }>("/exports/cleanup", {
    method: "POST",
  });
}
