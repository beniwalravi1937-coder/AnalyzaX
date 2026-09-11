/**
 * Phase 9: Visualization Engine API Client
 * Centralized HTTP service for interacting with FastAPI /api/v1/visualizations endpoints.
 */

import {
  ChartSpec,
  ChartTypeDefinition,
  SavedVisualization,
  VisualizationRecommendation,
  VisualizationValidationResult,
} from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

class VisualizationApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}/api/v1/visualizations${endpoint}`;
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorMessage = `HTTP error ${response.status}: ${response.statusText}`;
      try {
        const errorBody = await response.json();
        if (errorBody && errorBody.detail) {
          errorMessage = typeof errorBody.detail === "string"
            ? errorBody.detail
            : JSON.stringify(errorBody.detail);
        }
      } catch {
        // Fallback to response status text
      }
      throw new Error(errorMessage);
    }

    return response.json();
  }

  async getRecommendations(
    datasetId: string,
    versionId?: string | null,
    selectedFields?: string[],
    intent?: string
  ): Promise<VisualizationRecommendation[]> {
    return this.request<VisualizationRecommendation[]>("/recommend", {
      method: "POST",
      body: JSON.stringify({
        dataset_id: datasetId,
        version_id: versionId || null,
        selected_fields: selectedFields || null,
        intent: intent || null,
      }),
    });
  }

  async validateSpec(spec: ChartSpec): Promise<VisualizationValidationResult> {
    return this.request<VisualizationValidationResult>("/validate", {
      method: "POST",
      body: JSON.stringify(spec),
    });
  }

  async previewChart(spec: ChartSpec): Promise<ChartSpec> {
    return this.request<ChartSpec>("/preview", {
      method: "POST",
      body: JSON.stringify(spec),
    });
  }

  async saveVisualization(
    name: string,
    spec: ChartSpec,
    description?: string,
    sourceReference?: string
  ): Promise<SavedVisualization> {
    return this.request<SavedVisualization>("", {
      method: "POST",
      body: JSON.stringify({
        name,
        spec,
        description: description || null,
        source_reference: sourceReference || null,
      }),
    });
  }

  async listSavedVisualizations(
    datasetId?: string,
    versionId?: string
  ): Promise<SavedVisualization[]> {
    const params = new URLSearchParams();
    if (datasetId) params.append("dataset_id", datasetId);
    if (versionId) params.append("version_id", versionId);
    const qs = params.toString() ? `?${params.toString()}` : "";
    return this.request<SavedVisualization[]>(qs);
  }

  async getSavedVisualization(visualizationId: string): Promise<SavedVisualization> {
    return this.request<SavedVisualization>(`/${visualizationId}`);
  }

  async deleteSavedVisualization(visualizationId: string): Promise<{ deleted: boolean; id: string }> {
    return this.request<{ deleted: boolean; id: string }>(`/${visualizationId}`, {
      method: "DELETE",
    });
  }

  async checkVersionCompatibility(
    visualizationId: string,
    targetVersionId: string
  ): Promise<VisualizationValidationResult> {
    return this.request<VisualizationValidationResult>(
      `/${visualizationId}/compatibility?target_version_id=${encodeURIComponent(targetVersionId)}`
    );
  }

  async getVisualizationData(
    visualizationId: string
  ): Promise<{ data: Record<string, any>[]; sampling?: any; row_count: number }> {
    return this.request<{ data: Record<string, any>[]; sampling?: any; row_count: number }>(
      `/${visualizationId}/data`
    );
  }

  async recommendFromSql(
    columns: Array<{ name: string; physical_type?: string; semantic_type?: string }>,
    rows: Array<Record<string, any>>,
    queryText?: string
  ): Promise<VisualizationRecommendation[]> {
    return this.request<VisualizationRecommendation[]>("/recommend-from-sql", {
      method: "POST",
      body: JSON.stringify({
        columns,
        rows,
        query_text: queryText || null,
      }),
    });
  }

  async getRegistry(tier?: number): Promise<ChartTypeDefinition[]> {
    const qs = tier ? `?tier=${tier}` : "";
    return this.request<ChartTypeDefinition[]>(`/registry${qs}`);
  }
}

export const visualizationApi = new VisualizationApiClient();
