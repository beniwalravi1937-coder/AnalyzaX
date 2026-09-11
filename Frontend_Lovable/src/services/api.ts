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

const API_BASE_URL =
  (typeof import.meta !== "undefined" && (import.meta as any).env?.VITE_API_BASE_URL) ||
  (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_BASE_URL) ||
  "";

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
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
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
      throw new ApiError(
        "Failed to upload file to backend. Verify the backend server is running.",
        "UPLOAD_NETWORK_ERROR",
        0,
      );
    }
  }

  async getDataset(datasetId: string): Promise<DatasetResponse> {
    return this.request<DatasetResponse>(`/api/v1/datasets/${datasetId}`);
  }

  async listDatasets(): Promise<{ datasets: DatasetResponse[]; total: number }> {
    return this.request<{ datasets: DatasetResponse[]; total: number }>("/api/v1/datasets");
  }

  async deleteDataset(datasetId: string): Promise<void> {
    await this.request<void>(`/api/v1/datasets/${datasetId}`, {
      method: "DELETE",
    });
  }

  async getDatasetProfile(datasetId: string): Promise<DatasetProfileResponse> {
    return this.request<DatasetProfileResponse>(`/api/v1/datasets/${datasetId}/profile`);
  }

  async refreshDatasetProfile(datasetId: string): Promise<DatasetProfileResponse> {
    return this.request<DatasetProfileResponse>(`/api/v1/datasets/${datasetId}/profile/refresh`, {
      method: "POST",
    });
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
    return this.request<DataQualityReportResponse>(
      `/api/v1/datasets/${datasetId}/quality${queryString}`,
    );
  }

  async refreshDatasetQuality(datasetId: string): Promise<DataQualityReportResponse> {
    return this.request<DataQualityReportResponse>(
      `/api/v1/datasets/${datasetId}/quality/refresh`,
      {
        method: "POST",
      },
    );
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
    return this.request<EDAReport>(path);
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
    return this.request<EDAReport>(path, { method: "POST" });
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
