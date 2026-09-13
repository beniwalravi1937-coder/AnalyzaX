/**
 * Centralized API client for communicating with the AnalyzaX FastAPI backend.
 *
 * IMPORTANT: All backend communication must go through this module.
 * Do NOT scatter fetch() calls throughout components.
 *
 * AGENTS.md Rule #9: Backend logic must not live inside frontend code.
 * The frontend is strictly a presentation and interaction layer.
 */

import {
  DatasetResponse,
  DatasetProfileResponse,
  DataQualityReportResponse,
  QualityFilters,
  CleaningRecommendation,
  TransformationPlan,
  TransformationStep,
  TransformationPreview,
  DryRunResult,
  ApplyPlanResponse,
  DatasetVersion,
  LineageResponse,
  QualityComparison,
  EDAReport,
  EDAFinding,
  RelationshipQueryResponse,
} from "@/types";
import {
  parseDatasetLocally,
  getLocalDatasetsList,
  getLocalDataset,
  getLocalProfile,
  getLocalQuality,
  getLocalEDA,
} from "./localDatasetEngine";

const getBaseUrl = (): string => {
  if (typeof window !== "undefined") {
    const custom = localStorage.getItem("analyzax_backend_url");
    if (custom) return custom.replace(/\/$/, "");
  }
  return (
    (typeof import.meta !== "undefined" && (import.meta as any).env?.VITE_API_BASE_URL) ||
    (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_BASE_URL) ||
    ""
  );
};

export const API_BASE_URL = getBaseUrl();

export interface ApiSuccessResponse<T> {
  success?: boolean;
  data?: T;
  [key: string]: unknown;
}

export interface ApiErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  database: string;
  duckdb: string;
  duckdb_version?: string;
}

class ApiClient {
  private _configuredBaseUrl: string;

  constructor(baseUrl: string) {
    this._configuredBaseUrl = baseUrl;
  }

  public get baseUrl(): string {
    return this._configuredBaseUrl || getBaseUrl();
  }

  private async request<T>(
    path: string,
    options?: RequestInit,
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;

    try {
      const response = await fetch(url, {
        headers: {
          "Content-Type": "application/json",
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({
          error: { code: "NETWORK_ERROR", message: `HTTP ${response.status}` },
        })) as ApiErrorResponse;
        throw new ApiError(
          errorBody.error?.message ?? `HTTP ${response.status}`,
          errorBody.error?.code ?? "UNKNOWN_ERROR",
          response.status,
        );
      }

      return (await response.json()) as T;
    } catch (err) {
      if (err instanceof ApiError) throw err;
      // Network-level error (server down, CORS, etc.)
      throw new ApiError(
        "Unable to reach the AnalyzaX backend. Is the server running?",
        "NETWORK_UNREACHABLE",
        0,
      );
    }
  }

  // -------------------------------------------------------------------------
  // Health & System
  // -------------------------------------------------------------------------

  async getHealth(): Promise<HealthStatus> {
    return this.request<HealthStatus>("/api/v1/health");
  }

  // -------------------------------------------------------------------------
  // Datasets
  // -------------------------------------------------------------------------

  async uploadDataset(file: File): Promise<{
    dataset_id: string;
    status: string;
    filename: string;
    format: string;
    file_size_bytes: number;
    duckdb_table_name: string;
    message: string;
  }> {
    const formData = new FormData();
    formData.append("file", file);

    const url = `${this.baseUrl}/api/v1/datasets/upload`;
    try {
      const response = await fetch(url, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        // If HTTP 413 (Entity Too Large, e.g. Vercel 4.5MB limit) or 404 (endpoint absent on static host)
        if (response.status === 413 || response.status === 404 || response.status === 405 || response.status === 502) {
          return await parseDatasetLocally(file, response.status === 413);
        }
        const errorBody = (await response.json().catch(() => ({
          error: { code: "UPLOAD_ERROR", message: `HTTP ${response.status}` },
        }))) as ApiErrorResponse;
        throw new ApiError(
          errorBody.error?.message ?? `Upload failed with HTTP ${response.status}`,
          errorBody.error?.code ?? "UPLOAD_FAILED",
          response.status,
        );
      }

      return await response.json();
    } catch (err) {
      if (err instanceof ApiError) throw err;
      // Network failure or server unreachable — fall back to client-side analytical processing
      try {
        return await parseDatasetLocally(file, false);
      } catch (localErr: any) {
        throw new ApiError(
          `Failed to process dataset: ${localErr?.message || "Verify file format"}`,
          "UPLOAD_ERROR",
          0,
        );
      }
    }
  }

  async getDataset(datasetId: string): Promise<DatasetResponse> {
    try {
      return await this.request<DatasetResponse>(`/api/v1/datasets/${datasetId}`);
    } catch (err) {
      const local = getLocalDataset(datasetId);
      if (local) return local;
      throw err;
    }
  }

  async listDatasets(): Promise<{ datasets: DatasetResponse[]; total: number }> {
    const local = getLocalDatasetsList();
    try {
      const res = await this.request<{ datasets: DatasetResponse[]; total: number }>("/api/v1/datasets");
      const backendDatasets = res.datasets || [];
      const backendIds = new Set(backendDatasets.map((d) => d.id));
      const combined = [...backendDatasets, ...local.filter((l) => !backendIds.has(l.id))];
      return { datasets: combined, total: combined.length };
    } catch {
      return { datasets: local, total: local.length };
    }
  }

  async deleteDataset(datasetId: string): Promise<void> {
    try {
      await this.request<void>(`/api/v1/datasets/${datasetId}`, {
        method: "DELETE",
      });
    } catch {
      // Also remove from local storage if present
      if (typeof window !== "undefined") {
        const local = getLocalDatasetsList().filter((d) => d.id !== datasetId);
        localStorage.setItem("analyzax_local_datasets_meta", JSON.stringify(local));
      }
    }
  }

  async getDatasetProfile(datasetId: string): Promise<DatasetProfileResponse> {
    try {
      return await this.request<DatasetProfileResponse>(`/api/v1/datasets/${datasetId}/profile`);
    } catch (err) {
      const local = getLocalProfile(datasetId);
      if (local) return local;
      throw err;
    }
  }

  async refreshDatasetProfile(datasetId: string): Promise<DatasetProfileResponse> {
    try {
      return await this.request<DatasetProfileResponse>(`/api/v1/datasets/${datasetId}/profile/refresh`, {
        method: "POST",
      });
    } catch (err) {
      const local = getLocalProfile(datasetId);
      if (local) return local;
      throw err;
    }
  }

  async getDatasetQuality(
    datasetId: string,
    filters?: QualityFilters,
  ): Promise<DataQualityReportResponse> {
    const params = new URLSearchParams();
    if (filters?.severity) params.append("severity", filters.severity);
    if (filters?.dimension) params.append("dimension", filters.dimension);
    if (filters?.column) params.append("column", filters.column);
    const queryString = params.toString() ? `?${params.toString()}` : "";
    try {
      return await this.request<DataQualityReportResponse>(
        `/api/v1/datasets/${datasetId}/quality${queryString}`,
      );
    } catch (err) {
      const local = getLocalQuality(datasetId);
      if (local) return local;
      throw err;
    }
  }

  async refreshDatasetQuality(datasetId: string): Promise<DataQualityReportResponse> {
    try {
      return await this.request<DataQualityReportResponse>(
        `/api/v1/datasets/${datasetId}/quality/refresh`,
        {
          method: "POST",
        },
      );
    } catch (err) {
      const local = getLocalQuality(datasetId);
      if (local) return local;
      throw err;
    }
  }

  // ─────────────────────────────────────────────────────────────
  // Phase 6: Cleaning & Transformation Methods
  // ─────────────────────────────────────────────────────────────

  async getCleaningRecommendations(
    datasetId: string,
    forceRefresh: boolean = false,
  ): Promise<CleaningRecommendation[]> {
    const qs = forceRefresh ? "?force_refresh=true" : "";
    return this.request<CleaningRecommendation[]>(
      `/api/v1/cleaning/recommendations/${datasetId}${qs}`,
    );
  }

  async getTransformationPlan(datasetId: string): Promise<TransformationPlan> {
    return this.request<TransformationPlan>(`/api/v1/cleaning/plan/${datasetId}`);
  }

  async updateTransformationPlan(
    datasetId: string,
    steps: TransformationStep[],
    sourceVersionId?: string,
  ): Promise<TransformationPlan> {
    return this.request<TransformationPlan>(`/api/v1/cleaning/plan/${datasetId}`, {
      method: "POST",
      body: JSON.stringify({ steps, source_version_id: sourceVersionId }),
    });
  }

  async previewTransformationPlan(
    datasetId: string,
    steps: TransformationStep[],
    sourceVersionId?: string,
    previewRows: number = 10,
  ): Promise<TransformationPreview> {
    return this.request<TransformationPreview>(`/api/v1/cleaning/preview/${datasetId}`, {
      method: "POST",
      body: JSON.stringify({
        steps,
        source_version_id: sourceVersionId,
        preview_rows: previewRows,
      }),
    });
  }

  async dryRunTransformationPlan(
    datasetId: string,
    steps: TransformationStep[],
    sourceVersionId?: string,
  ): Promise<DryRunResult> {
    return this.request<DryRunResult>(`/api/v1/cleaning/dry-run/${datasetId}`, {
      method: "POST",
      body: JSON.stringify({ steps, source_version_id: sourceVersionId }),
    });
  }

  async applyTransformationPlan(
    datasetId: string,
    steps: TransformationStep[],
    versionLabel?: string,
    sourceVersionId?: string,
  ): Promise<ApplyPlanResponse> {
    return this.request<ApplyPlanResponse>(`/api/v1/cleaning/apply/${datasetId}`, {
      method: "POST",
      body: JSON.stringify({
        steps,
        version_label: versionLabel,
        source_version_id: sourceVersionId,
      }),
    });
  }

  // ─────────────────────────────────────────────────────────────
  // Phase 6: Dataset Versioning & Lineage Methods
  // ─────────────────────────────────────────────────────────────

  async getDatasetVersions(datasetId: string): Promise<DatasetVersion[]> {
    return this.request<DatasetVersion[]>(`/api/v1/versions/${datasetId}`);
  }

  async listVersions(datasetId: string): Promise<DatasetVersion[]> {
    return this.getDatasetVersions(datasetId);
  }

  async getActiveDatasetVersion(datasetId: string): Promise<DatasetVersion> {
    return this.request<DatasetVersion>(`/api/v1/versions/${datasetId}/active`);
  }

  async activateDatasetVersion(
    datasetId: string,
    versionId: string,
  ): Promise<{ active_version: DatasetVersion; message: string }> {
    return this.request<{ active_version: DatasetVersion; message: string }>(
      `/api/v1/versions/${datasetId}/activate/${versionId}`,
      {
        method: "POST",
      },
    );
  }

  async getDatasetLineage(datasetId: string): Promise<LineageResponse> {
    return this.request<LineageResponse>(`/api/v1/versions/${datasetId}/lineage`);
  }

  async compareDatasetVersions(
    datasetId: string,
    before: string,
    after: string,
  ): Promise<QualityComparison> {
    return this.request<QualityComparison>(
      `/api/v1/versions/${datasetId}/compare?before=${before}&after=${after}`,
    );
  }

  // -------------------------------------------------------------------------
  // Exploratory Data Analysis (EDA) Endpoints (Phase 7)
  // -------------------------------------------------------------------------

  async getEdaReport(
    datasetId: string,
    versionId?: string,
    correlationMethod?: string,
  ): Promise<EDAReport> {
    const query = correlationMethod ? `?correlation_method=${encodeURIComponent(correlationMethod)}` : "";
    const path = versionId
      ? `/api/v1/datasets/${datasetId}/versions/${versionId}/eda${query}`
      : `/api/v1/datasets/${datasetId}/eda${query}`;
    try {
      return await this.request<EDAReport>(path);
    } catch (err) {
      const local = getLocalEDA(datasetId);
      if (local) return local;
      throw err;
    }
  }

  async refreshEdaReport(
    datasetId: string,
    versionId?: string,
    correlationMethod?: string,
  ): Promise<EDAReport> {
    const query = correlationMethod ? `?correlation_method=${encodeURIComponent(correlationMethod)}` : "";
    const path = versionId
      ? `/api/v1/datasets/${datasetId}/versions/${versionId}/eda/refresh${query}`
      : `/api/v1/datasets/${datasetId}/eda/refresh${query}`;
    try {
      return await this.request<EDAReport>(path, { method: "POST" });
    } catch (err) {
      const local = getLocalEDA(datasetId);
      if (local) return local;
      throw err;
    }
  }

  async getColumnAnalysis(
    datasetId: string,
    column: string,
    versionId?: string,
  ): Promise<Record<string, unknown>> {
    const path = versionId
      ? `/api/v1/datasets/${datasetId}/versions/${versionId}/eda/columns/${encodeURIComponent(column)}`
      : `/api/v1/datasets/${datasetId}/eda/columns/${encodeURIComponent(column)}`;
    return this.request<Record<string, unknown>>(path);
  }

  async analyzeRelationship(
    datasetId: string,
    columnX: string,
    columnY: string,
    versionId?: string,
  ): Promise<RelationshipQueryResponse> {
    const path = versionId
      ? `/api/v1/datasets/${datasetId}/versions/${versionId}/eda/relationship`
      : `/api/v1/datasets/${datasetId}/eda/relationship`;
    return this.request<RelationshipQueryResponse>(path, {
      method: "POST",
      body: JSON.stringify({ column_x: columnX, column_y: columnY }),
    });
  }

  async getEdaFindings(
    datasetId: string,
    versionId?: string,
    category?: string,
    severity?: string,
  ): Promise<EDAFinding[]> {
    const queryParams = new URLSearchParams();
    if (category) queryParams.append("category", category);
    if (severity) queryParams.append("severity", severity);
    const qs = queryParams.toString() ? `?${queryParams.toString()}` : "";

    const path = versionId
      ? `/api/v1/datasets/${datasetId}/versions/${versionId}/eda/findings${qs}`
      : `/api/v1/datasets/${datasetId}/eda/findings${qs}`;
    return this.request<EDAFinding[]>(path);
  }
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// Singleton API client instance — import this across the app
export const apiClient = new ApiClient(API_BASE_URL);
export const api = apiClient;
