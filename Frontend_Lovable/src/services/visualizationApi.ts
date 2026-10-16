/**
 * Phase 9: Visualization Engine API Client
 * Centralized HTTP service for interacting with FastAPI /api/v1/visualizations endpoints.
 * Includes resilient backend fallback, auth token preservation, and Vercel CDN 405 mitigation.
 */

import {
  ChartSpec,
  ChartTypeDefinition,
  SavedVisualization,
  VisualizationRecommendation,
  VisualizationValidationResult,
  ChartType,
} from "@/types";
import { getLocalProfile, getLocalSampleRows } from "./localDatasetEngine";

const LOCAL_SAVED_VIZ_KEY = "analyzax_saved_visualizations";

function getBaseUrl(): string {
  if (typeof window !== "undefined") {
    const custom = localStorage.getItem("analyzax_backend_url");
    if (custom) return custom.trim().replace(/\/$/, "");
  }
  return (
    (typeof import.meta !== "undefined" && (import.meta as any).env?.VITE_API_BASE_URL) ||
    (typeof import.meta !== "undefined" && (import.meta as any).env?.VITE_API_URL) ||
    (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_BASE_URL) ||
    (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_URL) ||
    ""
  );
}

function getAuthHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token =
    sessionStorage.getItem("analyzax_token") ||
    localStorage.getItem("analyzax_token");
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

class VisualizationApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const baseUrl = getBaseUrl();
    const url = `${baseUrl}/api/v1/visualizations${endpoint}`;
    const headers = {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
      ...(options.headers || {}),
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Check if response is HTML (e.g. Vercel SPA index.html fallback on 404/405)
    const contentType = response.headers.get("content-type") || "";
    const isHtml = contentType.includes("text/html");

    if (!response.ok || isHtml) {
      if (response.status === 405 || isHtml) {
        throw new Error(
          `ENDPOINT_METHOD_NOT_ALLOWED: Endpoint ${endpoint} received HTTP ${response.status} (Method Not Allowed or HTML fallback)`
        );
      }

      let errorMessage = `HTTP error ${response.status}: ${response.statusText}`;
      try {
        const errorBody = await response.json();
        if (errorBody && errorBody.detail) {
          errorMessage = typeof errorBody.detail === "string"
            ? errorBody.detail
            : JSON.stringify(errorBody.detail);
        } else if (errorBody && errorBody.error && errorBody.error.message) {
          errorMessage = errorBody.error.message;
        }
      } catch {
        // Fallback to response status text
      }
      throw new Error(errorMessage);
    }

    return response.json();
  }

  /**
   * Generates deterministic recommendations for a dataset version.
   * Tries POST first, falls back to GET on HTTP 405, and uses client-side deterministic
   * recommendation engine if backend is absent on Vercel.
   */
  async getRecommendations(
    datasetId: string,
    versionId?: string | null,
    selectedFields?: string[],
    intent?: string
  ): Promise<VisualizationRecommendation[]> {
    // 1. Try POST to /recommend
    try {
      const recs = await this.request<VisualizationRecommendation[]>("/recommend", {
        method: "POST",
        body: JSON.stringify({
          dataset_id: datasetId,
          version_id: versionId || null,
          selected_fields: selectedFields || null,
          intent: intent || null,
        }),
      });

      return this.normalizeRecommendations(recs, datasetId, versionId);
    } catch (postErr: any) {
      const is405 =
        postErr?.message?.includes("ENDPOINT_METHOD_NOT_ALLOWED") ||
        postErr?.message?.includes("405") ||
        postErr?.message?.includes("Method Not Allowed");

      // 2. If POST received 405, try GET to /recommend
      if (is405) {
        try {
          const params = new URLSearchParams({ dataset_id: datasetId });
          if (versionId) params.append("version_id", versionId);
          if (intent) params.append("intent", intent);
          if (selectedFields && selectedFields.length > 0) {
            selectedFields.forEach((f) => params.append("selected_fields", f));
          }

          const getRecs = await this.request<VisualizationRecommendation[]>(
            `/recommend?${params.toString()}`
          );
          return this.normalizeRecommendations(getRecs, datasetId, versionId);
        } catch {
          // Fall through to deterministic client-side generation
        }
      }

      // 3. Fallback: Generate deterministic recommendations from dataset profile/schema
      const fallbackRecs = this.generateLocalRecommendations(
        datasetId,
        versionId,
        selectedFields,
        intent
      );

      if (fallbackRecs.length > 0) {
        return fallbackRecs;
      }

      // Re-throw with clean user-friendly wording if no fallback could be constructed
      throw new Error(
        "Automated recommendations could not be computed for this dataset. Please verify the dataset contains valid columns."
      );
    }
  }

  /**
   * Ensures every recommendation has `spec`, `score`, `rationale`, and `is_recommended` populated.
   */
  private normalizeRecommendations(
    recs: VisualizationRecommendation[],
    datasetId: string,
    versionId?: string | null
  ): VisualizationRecommendation[] {
    if (!Array.isArray(recs)) return [];

    return recs.map((r, idx) => {
      const conf = r.confidence ?? r.score ?? 0.85;
      const title = r.title || `Chart ${idx + 1}`;
      const recId = r.recommendation_id || `rec_${idx}_${Date.now()}`;
      const spec: ChartSpec = r.spec || {
        id: `chart_${recId}`,
        chart_id: `chart_${recId}`,
        chart_type: r.chart_type,
        title,
        description: r.reason || r.rationale || "",
        dataset_id: datasetId,
        dataset_version_id: versionId || "v1",
        x: r.x_field || null,
        y: r.y_field || null,
        series: r.series_field || null,
        color: r.color_field || null,
        aggregation: r.aggregation || "sum",
        data: [],
      };

      return {
        ...r,
        recommendation_id: recId,
        confidence: conf,
        score: r.score ?? conf,
        rationale: r.rationale || r.reason || "High analytical suitability based on distribution rules.",
        is_recommended: r.is_recommended ?? conf >= 0.85,
        spec,
      };
    });
  }

  /**
   * Deterministic client-side recommendation engine when backend is offline or on Vercel SPA.
   */
  private generateLocalRecommendations(
    datasetId: string,
    versionId?: string | null,
    selectedFields?: string[],
    intent?: string
  ): VisualizationRecommendation[] {
    const profile = getLocalProfile(datasetId);
    const columns = profile?.columns || [];
    const sampleRows = getLocalSampleRows(datasetId);

    if (columns.length === 0 && sampleRows.length > 0) {
      // Introspect from first row
      const firstRow = sampleRows[0];
      Object.keys(firstRow).forEach((key) => {
        const val = firstRow[key];
        const isNum = typeof val === "number" || (!isNaN(Number(val)) && val !== "");
        columns.push({
          name: key,
          data_type: isNum ? "float" : "varchar",
          nullable: false,
          distinct_count: 10,
          missing_count: 0,
          missing_percentage: 0,
        });
      });
    }

    if (columns.length === 0) {
      return [];
    }

    const catCols = columns
      .filter((c) => {
        const dt = (c.data_type || "").toLowerCase();
        return (
          dt.includes("varchar") ||
          dt.includes("string") ||
          dt.includes("text") ||
          dt.includes("char") ||
          (c.distinct_count && c.distinct_count <= 25)
        );
      })
      .map((c) => c.name);

    const numCols = columns
      .filter((c) => {
        const dt = (c.data_type || "").toLowerCase();
        return (
          dt.includes("int") ||
          dt.includes("float") ||
          dt.includes("double") ||
          dt.includes("decimal") ||
          dt.includes("numeric")
        );
      })
      .map((c) => c.name);

    const dateCols = columns
      .filter((c) => {
        const dt = (c.data_type || "").toLowerCase();
        return dt.includes("date") || dt.includes("time") || dt.includes("timestamp");
      })
      .map((c) => c.name);

    const recs: VisualizationRecommendation[] = [];

    // Rule 1: Temporal Trend (Date vs Metric)
    if (dateCols.length > 0 && numCols.length > 0) {
      const dCol = dateCols[0];
      const mCol = numCols[0];
      const recId = `rec_temporal_${dCol}_${mCol}`;
      recs.push({
        recommendation_id: recId,
        chart_type: "line" as ChartType,
        tier: 1,
        title: `${mCol} Trend over ${dCol}`,
        reason: `Temporal column '${dCol}' paired with metric '${mCol}' provides chronological trend intelligence.`,
        rationale: `Chronological trends reveal seasonal patterns, trajectory, and sudden velocity shifts.`,
        confidence: 0.96,
        score: 0.96,
        is_recommended: true,
        x_field: dCol,
        y_field: mCol,
        aggregation: "sum",
        priority: 1,
        intent: "trend",
        spec: {
          id: `spec_${recId}`,
          chart_id: `chart_${recId}`,
          chart_type: "line",
          title: `${mCol} Trend over ${dCol}`,
          dataset_id: datasetId,
          dataset_version_id: versionId || "v1",
          x: dCol,
          y: mCol,
          aggregation: "sum",
        },
      });
    }

    // Rule 2: Categorical Comparison (Dimension vs Metric)
    if (catCols.length > 0 && numCols.length > 0) {
      const cCol = catCols[0];
      const mCol = numCols[0];
      const recId = `rec_bar_${cCol}_${mCol}`;
      recs.push({
        recommendation_id: recId,
        chart_type: "bar" as ChartType,
        tier: 1,
        title: `${mCol} by ${cCol}`,
        reason: `Categorical dimension '${cCol}' with continuous measure '${mCol}' is optimal for discrete comparison.`,
        rationale: `Bar charts provide high visual clarity and immediate comparative benchmarking across groups.`,
        confidence: 0.94,
        score: 0.94,
        is_recommended: true,
        x_field: cCol,
        y_field: mCol,
        aggregation: "sum",
        sorting: "desc",
        priority: 1,
        intent: "comparison",
        spec: {
          id: `spec_${recId}`,
          chart_id: `chart_${recId}`,
          chart_type: "bar",
          title: `${mCol} by ${cCol}`,
          dataset_id: datasetId,
          dataset_version_id: versionId || "v1",
          x: cCol,
          y: mCol,
          aggregation: "sum",
          sort_direction: "desc",
        },
      });

      // Also add Horizontal Bar
      const recIdHoriz = `rec_hbar_${cCol}_${mCol}`;
      recs.push({
        recommendation_id: recIdHoriz,
        chart_type: "horizontal_bar" as ChartType,
        tier: 1,
        title: `${mCol} by ${cCol} (Horizontal)`,
        reason: `Horizontal layout gives enhanced label readability across categories in '${cCol}'.`,
        rationale: `Prevents label clipping and provides intuitive rank ordering.`,
        confidence: 0.91,
        score: 0.91,
        is_recommended: true,
        x_field: cCol,
        y_field: mCol,
        aggregation: "sum",
        sorting: "desc",
        priority: 2,
        intent: "comparison",
        spec: {
          id: `spec_${recIdHoriz}`,
          chart_id: `chart_${recIdHoriz}`,
          chart_type: "horizontal_bar",
          title: `${mCol} by ${cCol} (Horizontal)`,
          dataset_id: datasetId,
          dataset_version_id: versionId || "v1",
          x: cCol,
          y: mCol,
          aggregation: "sum",
          sort_direction: "desc",
        },
      });
    }

    // Rule 3: Numeric Distribution (Histogram / Boxplot)
    if (numCols.length > 0) {
      const mCol = numCols[0];
      const recIdHist = `rec_hist_${mCol}`;
      recs.push({
        recommendation_id: recIdHist,
        chart_type: "histogram" as ChartType,
        tier: 1,
        title: `Distribution of ${mCol}`,
        reason: `Measure '${mCol}' shows variance and skewness suitable for binned frequency distribution.`,
        rationale: `Histograms immediately uncover skewness, bimodal modes, and outlier clusters.`,
        confidence: 0.92,
        score: 0.92,
        is_recommended: true,
        x_field: mCol,
        priority: 1,
        intent: "distribution",
        spec: {
          id: `spec_${recIdHist}`,
          chart_id: `chart_${recIdHist}`,
          chart_type: "histogram",
          title: `Distribution of ${mCol}`,
          dataset_id: datasetId,
          dataset_version_id: versionId || "v1",
          x: mCol,
        },
      });

      const recIdBox = `rec_box_${mCol}`;
      recs.push({
        recommendation_id: recIdBox,
        chart_type: "boxplot" as ChartType,
        tier: 1,
        title: `${mCol} Five-Number Summary`,
        reason: `Boxplot outlines IQR spread, median, quartiles, and statistical anomalies for '${mCol}'.`,
        rationale: `Boxplots provide dense summary of dispersion, IQR, and statistical outlier thresholds.`,
        confidence: 0.88,
        score: 0.88,
        is_recommended: false,
        y_field: mCol,
        priority: 2,
        intent: "distribution",
        spec: {
          id: `spec_${recIdBox}`,
          chart_id: `chart_${recIdBox}`,
          chart_type: "boxplot",
          title: `${mCol} Five-Number Summary`,
          dataset_id: datasetId,
          dataset_version_id: versionId || "v1",
          y: mCol,
        },
      });
    }

    // Rule 4: Correlation / Relationship (Scatter)
    if (numCols.length >= 2) {
      const xCol = numCols[0];
      const yCol = numCols[1];
      const recIdScatter = `rec_scatter_${xCol}_${yCol}`;
      recs.push({
        recommendation_id: recIdScatter,
        chart_type: "scatter" as ChartType,
        tier: 1,
        title: `${yCol} vs. ${xCol} Correlation`,
        reason: `Paired measures '${xCol}' and '${yCol}' evaluate linear co-dependence and dispersion.`,
        rationale: `Scatter plots surface non-linear trends, cluster groupings, and multivariate anomalies.`,
        confidence: 0.93,
        score: 0.93,
        is_recommended: true,
        x_field: xCol,
        y_field: yCol,
        priority: 1,
        intent: "relationship",
        spec: {
          id: `spec_${recIdScatter}`,
          chart_id: `chart_${recIdScatter}`,
          chart_type: "scatter",
          title: `${yCol} vs. ${xCol} Correlation`,
          dataset_id: datasetId,
          dataset_version_id: versionId || "v1",
          x: xCol,
          y: yCol,
        },
      });
    }

    // Rule 5: Composition (Donut)
    if (catCols.length > 0) {
      const cCol = catCols[0];
      const mCol = numCols.length > 0 ? numCols[0] : undefined;
      const recIdDonut = `rec_donut_${cCol}`;
      recs.push({
        recommendation_id: recIdDonut,
        chart_type: "donut" as ChartType,
        tier: 1,
        title: `${cCol} Share & Composition`,
        reason: `Low cardinality dimension '${cCol}' represents part-to-whole proportions.`,
        rationale: `Donut charts highlight market share and percentage breakdown with minimal cognitive load.`,
        confidence: 0.89,
        score: 0.89,
        is_recommended: false,
        x_field: cCol,
        y_field: mCol || null,
        aggregation: mCol ? "sum" : "count",
        priority: 2,
        intent: "composition",
        spec: {
          id: `spec_${recIdDonut}`,
          chart_id: `chart_${recIdDonut}`,
          chart_type: "donut",
          title: `${cCol} Share & Composition`,
          dataset_id: datasetId,
          dataset_version_id: versionId || "v1",
          x: cCol,
          y: mCol || null,
          aggregation: mCol ? "sum" : "count",
        },
      });
    }

    return recs;
  }

  async validateSpec(spec: ChartSpec): Promise<VisualizationValidationResult> {
    try {
      return await this.request<VisualizationValidationResult>("/validate", {
        method: "POST",
        body: JSON.stringify(spec),
      });
    } catch {
      // Local structural validation fallback
      const errors: string[] = [];
      if (!spec.title) errors.push("Chart title is required.");
      if (!spec.chart_type) errors.push("Chart type must be specified.");
      return {
        is_valid: errors.length === 0,
        errors,
        warnings: [],
      };
    }
  }

  async previewChart(spec: ChartSpec): Promise<ChartSpec> {
    try {
      return await this.request<ChartSpec>("/preview", {
        method: "POST",
        body: JSON.stringify(spec),
      });
    } catch {
      // Hydrate from local sample rows
      const rows = getLocalSampleRows(spec.dataset_id || "");
      if (rows && rows.length > 0) {
        const xField = spec.x || spec.x_field;
        const yField = spec.y || spec.y_field;

        let aggregatedData = rows;
        if (xField && yField && spec.aggregation && spec.aggregation !== "none") {
          const map = new Map<string, { count: number; sum: number }>();
          rows.forEach((r) => {
            const key = String(r[xField] ?? "Unknown");
            const val = Number(r[yField]) || 0;
            const existing = map.get(key) || { count: 0, sum: 0 };
            existing.count += 1;
            existing.sum += val;
            map.set(key, existing);
          });

          aggregatedData = Array.from(map.entries()).map(([k, v]) => ({
            [xField]: k,
            [yField]: spec.aggregation === "avg" ? Number((v.sum / v.count).toFixed(2)) : v.sum,
          }));

          if (spec.sort_direction === "desc") {
            aggregatedData.sort((a, b) => (Number(b[yField]) || 0) - (Number(a[yField]) || 0));
          }
        }

        return {
          ...spec,
          data: aggregatedData.slice(0, 500),
          sampling: {
            is_sampled: rows.length > 500,
            original_row_count: rows.length,
            sample_size: Math.min(rows.length, 500),
          },
        };
      }

      return {
        ...spec,
        data: spec.data || [],
      };
    }
  }

  async saveVisualization(
    name: string,
    spec: ChartSpec,
    description?: string,
    sourceReference?: string
  ): Promise<SavedVisualization> {
    const payload = {
      name,
      spec,
      description: description || null,
      source_reference: sourceReference || null,
    };

    try {
      return await this.request<SavedVisualization>("", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    } catch {
      // Local storage fallback
      const saved: SavedVisualization = {
        id: `viz_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
        name,
        description: description || null,
        dataset_id: spec.dataset_id || "default",
        dataset_version_id: spec.dataset_version_id || "v1",
        spec,
        chart_spec: spec,
        source_reference: sourceReference || null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      if (typeof window !== "undefined") {
        try {
          const raw = localStorage.getItem(LOCAL_SAVED_VIZ_KEY);
          const list: SavedVisualization[] = raw ? JSON.parse(raw) : [];
          list.unshift(saved);
          localStorage.setItem(LOCAL_SAVED_VIZ_KEY, JSON.stringify(list));
        } catch {
          // ignore
        }
      }

      return saved;
    }
  }

  async listSavedVisualizations(
    datasetId?: string,
    versionId?: string
  ): Promise<SavedVisualization[]> {
    const params = new URLSearchParams();
    if (datasetId) params.append("dataset_id", datasetId);
    if (versionId) params.append("version_id", versionId);
    const qs = params.toString() ? `?${params.toString()}` : "";

    try {
      return await this.request<SavedVisualization[]>(qs);
    } catch {
      if (typeof window !== "undefined") {
        try {
          const raw = localStorage.getItem(LOCAL_SAVED_VIZ_KEY);
          let list: SavedVisualization[] = raw ? JSON.parse(raw) : [];
          if (datasetId) {
            list = list.filter((s) => s.dataset_id === datasetId);
          }
          return list;
        } catch {
          return [];
        }
      }
      return [];
    }
  }

  async getSavedVisualization(visualizationId: string): Promise<SavedVisualization> {
    try {
      return await this.request<SavedVisualization>(`/${visualizationId}`);
    } catch (err) {
      if (typeof window !== "undefined") {
        const raw = localStorage.getItem(LOCAL_SAVED_VIZ_KEY);
        const list: SavedVisualization[] = raw ? JSON.parse(raw) : [];
        const found = list.find((s) => s.id === visualizationId || s.visualization_id === visualizationId);
        if (found) return found;
      }
      throw err;
    }
  }

  async deleteSavedVisualization(visualizationId: string): Promise<{ deleted: boolean; id: string }> {
    try {
      return await this.request<{ deleted: boolean; id: string }>(`/${visualizationId}`, {
        method: "DELETE",
      });
    } catch {
      if (typeof window !== "undefined") {
        const raw = localStorage.getItem(LOCAL_SAVED_VIZ_KEY);
        const list: SavedVisualization[] = raw ? JSON.parse(raw) : [];
        const filtered = list.filter((s) => s.id !== visualizationId && s.visualization_id !== visualizationId);
        localStorage.setItem(LOCAL_SAVED_VIZ_KEY, JSON.stringify(filtered));
      }
      return { deleted: true, id: visualizationId };
    }
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
    try {
      const recs = await this.request<VisualizationRecommendation[]>("/recommend-from-sql", {
        method: "POST",
        body: JSON.stringify({
          columns,
          rows,
          query_text: queryText || null,
        }),
      });
      return this.normalizeRecommendations(recs, "sql_result", "current");
    } catch {
      return [];
    }
  }

  async getRegistry(tier?: number): Promise<ChartTypeDefinition[]> {
    const qs = tier ? `?tier=${tier}` : "";
    try {
      return await this.request<ChartTypeDefinition[]>(`/registry${qs}`);
    } catch {
      return [];
    }
  }
}

export const visualizationApi = new VisualizationApiClient();
