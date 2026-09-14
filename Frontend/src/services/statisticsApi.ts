/**
 * AnalyzaX — Phase 10: Statistics API Service
 * Handles client-side communication with the backend Statistical Intelligence Engine.
 */

import {
  MethodCatalogItem,
  MethodRecommendation,
  StatisticalAnalysisRequest,
  StatisticalResult,
  ValidationResponse,
} from "@/types/statistics";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export const statisticsApi = {
  async getMethods(): Promise<MethodCatalogItem[]> {
    const res = await fetch(`${API_BASE}/statistics/methods`);
    if (!res.ok) {
      throw new Error(`Failed to fetch statistical methods: ${res.statusText}`);
    }
    return res.json();
  },

  async recommendMethod(req: {
    dataset_id: string;
    dataset_version_id: string;
    target_columns: string[];
    group_columns?: string[];
    intent?: string;
  }): Promise<MethodRecommendation> {
    const res = await fetch(`${API_BASE}/statistics/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Failed to recommend statistical method");
    }
    return res.json();
  },

  async validateRequest(req: StatisticalAnalysisRequest): Promise<ValidationResponse> {
    const res = await fetch(`${API_BASE}/statistics/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Failed to validate statistical request");
    }
    return res.json();
  },

  async runAnalysis(req: StatisticalAnalysisRequest): Promise<StatisticalResult> {
    const res = await fetch(`${API_BASE}/statistics/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Statistical analysis computation failed");
    }
    return res.json();
  },

  async getHistory(datasetId?: string, versionId?: string): Promise<StatisticalResult[]> {
    const params = new URLSearchParams();
    if (datasetId) params.append("dataset_id", datasetId);
    if (versionId) params.append("dataset_version_id", versionId);

    const res = await fetch(`${API_BASE}/statistics/history?${params.toString()}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch statistical history: ${res.statusText}`);
    }
    return res.json();
  },

  async getAnalysis(analysisId: string): Promise<StatisticalResult> {
    const res = await fetch(`${API_BASE}/statistics/${analysisId}`);
    if (!res.ok) {
      throw new Error(`Failed to load statistical result: ${res.statusText}`);
    }
    return res.json();
  },

  async deleteAnalysis(analysisId: string): Promise<boolean> {
    const res = await fetch(`${API_BASE}/statistics/${analysisId}`, {
      method: "DELETE",
    });
    return res.ok;
  },

  async getVisualizations(analysisId: string): Promise<any[]> {
    const res = await fetch(`${API_BASE}/statistics/${analysisId}/visualizations`);
    if (!res.ok) {
      throw new Error(`Failed to fetch visualizations for analysis: ${res.statusText}`);
    }
    return res.json();
  },
};
