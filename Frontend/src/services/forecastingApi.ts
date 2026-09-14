/**
 * AnalyzaX — Phase 12: Forecasting API Client.
 * Strongly typed client communicating with the backend Forecasting Engine.
 */

import {
  ForecastExperiment,
  ForecastExperimentRequest,
  ForecastFrequency,
  ForecastModelDefinition,
  ForecastPoint,
  ForecastResult,
  FuturePredictRequest,
  FuturePredictResult,
  ResidualDiagnostics,
  TemporalAnalysisSummary,
  TemporalValidationReport,
} from "@/types/forecasting";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export const forecastingApi = {
  async getModels(): Promise<ForecastModelDefinition[]> {
    const res = await fetch(`${API_BASE}/forecasting/models`);
    if (!res.ok) {
      throw new Error(`Failed to fetch forecasting models: ${res.statusText}`);
    }
    return res.json();
  },

  async getMetrics(): Promise<Array<{ id: string; name: string; default: boolean; lower_is_better: boolean }>> {
    const res = await fetch(`${API_BASE}/forecasting/metrics`);
    if (!res.ok) {
      throw new Error(`Failed to fetch forecasting metrics: ${res.statusText}`);
    }
    return res.json();
  },

  async getTimeCandidates(datasetId: string, versionId: string): Promise<Array<{ column_name: string; confidence: number; data_type: string }>> {
    const res = await fetch(`${API_BASE}/forecasting/candidates/${datasetId}/${versionId}`);
    if (!res.ok) {
      throw new Error(`Failed to detect time candidates: ${res.statusText}`);
    }
    const data = await res.json();
    return data.candidates || [];
  },

  async checkSuitability(req: {
    dataset_id: string;
    dataset_version_id: string;
    time_column: string;
    target_column: string;
    frequency?: ForecastFrequency;
  }): Promise<TemporalValidationReport> {
    const res = await fetch(`${API_BASE}/forecasting/suitability`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      const msg = typeof err.detail === "object" ? err.detail.message : err.detail;
      throw new Error(msg || "Suitability validation failed");
    }
    return res.json();
  },

  async analyzeTemporal(req: {
    dataset_id: string;
    dataset_version_id: string;
    time_column: string;
    target_column: string;
    frequency: ForecastFrequency;
  }): Promise<TemporalAnalysisSummary> {
    const res = await fetch(`${API_BASE}/forecasting/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      const msg = typeof err.detail === "object" ? err.detail.message : err.detail;
      throw new Error(msg || "Temporal analysis failed");
    }
    return res.json();
  },

  async createExperiment(req: ForecastExperimentRequest, sync: boolean = false): Promise<ForecastExperiment> {
    const res = await fetch(`${API_BASE}/forecasting/experiments?sync=${sync}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      const msg = typeof err.detail === "object" ? err.detail.message : err.detail;
      throw new Error(msg || "Failed to launch forecasting experiment");
    }
    return res.json();
  },

  async getExperiment(experimentId: string): Promise<ForecastExperiment> {
    const res = await fetch(`${API_BASE}/forecasting/experiments/${experimentId}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch experiment status: ${res.statusText}`);
    }
    return res.json();
  },

  async cancelExperiment(experimentId: string): Promise<{ status: string }> {
    const res = await fetch(`${API_BASE}/forecasting/experiments/${experimentId}/cancel`, {
      method: "POST",
    });
    if (!res.ok) {
      throw new Error("Failed to cancel experiment");
    }
    return res.json();
  },

  async getExperimentResults(experimentId: string): Promise<ForecastResult> {
    const res = await fetch(`${API_BASE}/forecasting/experiments/${experimentId}/results`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      const msg = typeof err.detail === "object" ? err.detail.message : err.detail;
      throw new Error(msg || "Failed to fetch forecasting results");
    }
    return res.json();
  },

  async getForecasts(experimentId: string): Promise<ForecastPoint[]> {
    const res = await fetch(`${API_BASE}/forecasting/experiments/${experimentId}/forecasts`);
    if (!res.ok) {
      throw new Error("Failed to fetch forecast points");
    }
    return res.json();
  },

  async getDiagnostics(experimentId: string): Promise<ResidualDiagnostics | null> {
    const res = await fetch(`${API_BASE}/forecasting/experiments/${experimentId}/diagnostics`);
    if (!res.ok) {
      throw new Error("Failed to fetch diagnostics");
    }
    return res.json();
  },

  async predictFuture(runId: string, req: FuturePredictRequest): Promise<FuturePredictResult> {
    const res = await fetch(`${API_BASE}/forecasting/models/${runId}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      const msg = typeof err.detail === "object" ? err.detail.message : err.detail;
      throw new Error(msg || "Future prediction failed");
    }
    return res.json();
  },

  async getHistory(): Promise<{ experiments: ForecastExperiment[]; total_count: number }> {
    const res = await fetch(`${API_BASE}/forecasting/history`);
    if (!res.ok) {
      throw new Error("Failed to fetch forecasting history");
    }
    return res.json();
  },

  async listModels(): Promise<ForecastModelDefinition[]> {
    return this.getModels();
  },

  async listExperiments(datasetId?: string): Promise<ForecastExperiment[]> {
    const res = await this.getHistory();
    return datasetId ? res.experiments.filter((e) => e.dataset_id === datasetId) : res.experiments;
  },

  async getResults(experimentId: string): Promise<ForecastResult> {
    return this.getExperimentResults(experimentId);
  },

  async validateTimeSeries(
    datasetId: string,
    versionId: string,
    timeColumn: string,
    targetColumn: string,
    frequency?: ForecastFrequency
  ): Promise<TemporalValidationReport> {
    return this.checkSuitability({
      dataset_id: datasetId,
      dataset_version_id: versionId,
      time_column: timeColumn,
      target_column: targetColumn,
      frequency,
    });
  },

  async analyzeTimeSeries(
    datasetId: string,
    versionId: string,
    timeColumn: string,
    targetColumn: string,
    frequency: ForecastFrequency
  ): Promise<TemporalAnalysisSummary> {
    return this.analyzeTemporal({
      dataset_id: datasetId,
      dataset_version_id: versionId,
      time_column: timeColumn,
      target_column: targetColumn,
      frequency,
    });
  },
};

