/**
 * AnalyzaX — Phase 11: Machine Learning API Service.
 * Strongly typed client for communicating with the backend ML Engine.
 */

import {
  MLExperiment,
  MLExperimentRequest,
  MLModelDefinition,
  MLModelRun,
  MLResult,
  MLTaskType,
  PredictionRequest,
  PredictionResult,
  SuitabilityReport,
} from "@/types/ml";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export const mlApi = {
  async getModels(taskType?: MLTaskType): Promise<MLModelDefinition[]> {
    const url = new URL(`${API_BASE}/ml/models`);
    if (taskType) {
      url.searchParams.set("task_type", taskType);
    }
    const res = await fetch(url.toString());
    if (!res.ok) {
      throw new Error(`Failed to fetch ML models: ${res.statusText}`);
    }
    return res.json();
  },

  async getMetrics(taskType?: MLTaskType): Promise<Record<string, string[]>> {
    const url = new URL(`${API_BASE}/ml/metrics`);
    if (taskType) {
      url.searchParams.set("task_type", taskType);
    }
    const res = await fetch(url.toString());
    if (!res.ok) {
      throw new Error(`Failed to fetch ML metrics: ${res.statusText}`);
    }
    return res.json();
  },

  async checkSuitability(req: {
    dataset_id: string;
    dataset_version_id: string;
    target_column?: string;
    task_type?: MLTaskType;
    candidate_features?: string[];
  }): Promise<SuitabilityReport> {
    const res = await fetch(`${API_BASE}/ml/suitability`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      const msg = typeof err.detail === "object" ? err.detail.message : err.detail;
      throw new Error(msg || "Suitability check failed");
    }
    return res.json();
  },

  async validateInputs(req: {
    dataset_id: string;
    dataset_version_id: string;
    target_column?: string;
    task_type?: MLTaskType;
    candidate_features?: string[];
  }): Promise<SuitabilityReport> {
    const res = await fetch(`${API_BASE}/ml/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      const msg = typeof err.detail === "object" ? err.detail.message : err.detail;
      throw new Error(msg || "Validation check failed");
    }
    return res.json();
  },

  async runExperiment(req: MLExperimentRequest): Promise<MLResult> {
    const res = await fetch(`${API_BASE}/ml/experiments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      const msg = typeof err.detail === "object" ? err.detail.message : err.detail;
      throw new Error(msg || "Experiment execution failed");
    }
    return res.json();
  },

  async listExperiments(datasetId?: string, versionId?: string): Promise<MLExperiment[]> {
    const url = new URL(`${API_BASE}/ml/experiments`);
    if (datasetId) url.searchParams.set("dataset_id", datasetId);
    if (versionId) url.searchParams.set("version_id", versionId);
    const res = await fetch(url.toString());
    if (!res.ok) {
      throw new Error(`Failed to list experiments: ${res.statusText}`);
    }
    return res.json();
  },

  async getExperimentResult(experimentId: string): Promise<MLResult> {
    const res = await fetch(`${API_BASE}/ml/experiments/${experimentId}/results`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      const msg = typeof err.detail === "object" ? err.detail.message : err.detail;
      throw new Error(msg || "Failed to load experiment result");
    }
    return res.json();
  },

  async cancelExperiment(experimentId: string): Promise<{ experiment_id: string; status: string }> {
    const res = await fetch(`${API_BASE}/ml/experiments/${experimentId}/cancel`, {
      method: "POST",
    });
    if (!res.ok) {
      throw new Error("Failed to cancel experiment");
    }
    return res.json();
  },

  async predict(modelRunId: string, req: PredictionRequest): Promise<PredictionResult> {
    const res = await fetch(`${API_BASE}/ml/models/${modelRunId}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      const msg = typeof err.detail === "object" ? err.detail.message : err.detail;
      throw new Error(msg || "Prediction failed");
    }
    return res.json();
  },
};
