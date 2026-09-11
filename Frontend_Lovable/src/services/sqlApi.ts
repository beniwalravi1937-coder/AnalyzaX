/**
 * Phase 8: SQL Studio & Analytics Engine API Client
 * Centralized HTTP service for interacting with FastAPI /api/v1/sql endpoints.
 */

import {
  QueryHistoryItem,
  SavedQuery,
  SchemaTableInfo,
  SQLExplainResult,
  SQLQueryRequest,
  SQLQueryResponse,
  SQLTemplate,
  SQLValidationResult,
  ChartSpec,
} from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

class SQLApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}/api/v1/sql${endpoint}`;
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
        if (errorBody.detail) {
          errorMessage = typeof errorBody.detail === "string" 
            ? errorBody.detail 
            : JSON.stringify(errorBody.detail);
        }
      } catch {
        // use default error message
      }
      throw new Error(errorMessage);
    }

    return response.json();
  }

  // 1. Query Execution & Validation
  async executeQuery(req: SQLQueryRequest): Promise<SQLQueryResponse> {
    return this.request<SQLQueryResponse>("/query", {
      method: "POST",
      body: JSON.stringify(req),
    });
  }

  async validateQuery(req: SQLQueryRequest): Promise<SQLValidationResult> {
    return this.request<SQLValidationResult>("/validate", {
      method: "POST",
      body: JSON.stringify(req),
    });
  }

  async explainQuery(req: SQLQueryRequest): Promise<SQLExplainResult> {
    return this.request<SQLExplainResult>("/explain", {
      method: "POST",
      body: JSON.stringify(req),
    });
  }

  async cancelQuery(queryId: string): Promise<{ query_id: string; cancelled: boolean }> {
    return this.request<{ query_id: string; cancelled: boolean }>(`/cancel/${queryId}`, {
      method: "POST",
    });
  }

  // 2. Schema Introspection & Templates
  async getSchema(datasetId: string, versionId?: string | null): Promise<SchemaTableInfo> {
    const query = versionId ? `?version_id=${encodeURIComponent(versionId)}` : "";
    return this.request<SchemaTableInfo>(`/schema/${datasetId}${query}`);
  }

  async getTemplates(datasetId: string, versionId?: string | null): Promise<SQLTemplate[]> {
    const query = versionId ? `?version_id=${encodeURIComponent(versionId)}` : "";
    return this.request<SQLTemplate[]>(`/templates/${datasetId}${query}`);
  }

  // 3. Visualization Advice
  async visualize(params: {
    dataset_id: string;
    version_id: string;
    columns: any[];
    rows: any[];
  }): Promise<ChartSpec[]> {
    return this.request<ChartSpec[]>("/visualize", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  // 4. Query History
  async getHistory(params?: {
    dataset_id?: string;
    status?: string;
    search?: string;
    limit?: number;
  }): Promise<QueryHistoryItem[]> {
    const queryParts: string[] = [];
    if (params?.dataset_id) queryParts.push(`dataset_id=${encodeURIComponent(params.dataset_id)}`);
    if (params?.status) queryParts.push(`status=${encodeURIComponent(params.status)}`);
    if (params?.search) queryParts.push(`search=${encodeURIComponent(params.search)}`);
    if (params?.limit) queryParts.push(`limit=${params.limit}`);

    const queryString = queryParts.length ? `?${queryParts.join("&")}` : "";
    return this.request<QueryHistoryItem[]>(`/history${queryString}`);
  }

  async clearHistory(datasetId?: string): Promise<{ cleared_count: number }> {
    const query = datasetId ? `?dataset_id=${encodeURIComponent(datasetId)}` : "";
    return this.request<{ cleared_count: number }>(`/history${query}`, {
      method: "DELETE",
    });
  }

  // 5. Saved Queries
  async getSavedQueries(datasetId?: string, tag?: string): Promise<SavedQuery[]> {
    const queryParts: string[] = [];
    if (datasetId) queryParts.push(`dataset_id=${encodeURIComponent(datasetId)}`);
    if (tag) queryParts.push(`tag=${encodeURIComponent(tag)}`);

    const queryString = queryParts.length ? `?${queryParts.join("&")}` : "";
    return this.request<SavedQuery[]>(`/saved${queryString}`);
  }

  async createSavedQuery(data: {
    name: string;
    description?: string | null;
    dataset_id: string;
    version_scope?: string | null;
    sql: string;
    tags?: string[];
  }): Promise<SavedQuery> {
    return this.request<SavedQuery>("/saved", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateSavedQuery(
    id: string,
    data: {
      name?: string;
      description?: string | null;
      version_scope?: string | null;
      sql?: string;
      tags?: string[];
    }
  ): Promise<SavedQuery> {
    return this.request<SavedQuery>(`/saved/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteSavedQuery(id: string): Promise<{ deleted: boolean }> {
    return this.request<{ deleted: boolean }>(`/saved/${id}`, {
      method: "DELETE",
    });
  }
}

export const sqlApi = new SQLApiClient();
