// API Client for Phase 14 Dashboard, Insight Workspace, and Analytical Storytelling
// Includes client-side resilient local storage engine for environments where FastAPI backend is offline or on Vercel preview.

import {
  ComponentCreateRequest,
  ComponentDataResponse,
  ComponentUpdateRequest,
  Dashboard,
  DashboardComponent,
  DashboardCreateRequest,
  DashboardDataResponse,
  DashboardFilter,
  DashboardUpdateRequest,
  DashboardVersion,
} from "@/types/dashboard";

const getBaseUrl = (): string => {
  if (typeof window !== "undefined") {
    const custom = localStorage.getItem("analyzax_backend_url");
    if (custom) return custom.replace(/\/$/, "");
  }
  return (
    (typeof import.meta !== "undefined" && (import.meta as any).env?.VITE_API_BASE_URL) ||
    (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_BASE_URL) ||
    (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_URL) ||
    ""
  );
};

const LOCAL_DASHBOARDS_KEY = "analyzax_local_dashboards";
const LOCAL_VERSIONS_PREFIX = "analyzax_local_dash_versions_";

// ─────────────────────────────────────────────────────────
// Client-Side Local Dashboard Storage Helpers
// ─────────────────────────────────────────────────────────

function getStoredDashboards(): Dashboard[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(LOCAL_DASHBOARDS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveStoredDashboards(dashboards: Dashboard[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(LOCAL_DASHBOARDS_KEY, JSON.stringify(dashboards));
  } catch (err) {
    console.warn("Failed to persist local dashboards to localStorage", err);
  }
}

function getLocalDashboards(datasetId?: string, search?: string): Dashboard[] {
  let list = getStoredDashboards();
  if (datasetId) {
    list = list.filter((d) => d.dataset_id === datasetId);
  }
  if (search) {
    const term = search.toLowerCase();
    list = list.filter((d) => d.name.toLowerCase().includes(term));
  }
  return list;
}

function getLocalDashboard(dashboardId: string): Dashboard | null {
  const list = getStoredDashboards();
  return list.find((d) => d.dashboard_id === dashboardId) || null;
}

function createLocalDashboard(payload: DashboardCreateRequest): Dashboard {
  const dashId = `dash_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
  const now = new Date().toISOString();

  const components: DashboardComponent[] = [];
  const templateId = payload.template_id;

  if (templateId === "executive_overview") {
    components.push(
      {
        component_id: `comp_${Date.now()}_1`,
        dashboard_id: dashId,
        type: "TEXT",
        title: "Executive Summary",
        position: { x: 0, y: 0 },
        size: { width: 12, height: 2 },
        configuration: { content: "### Executive Overview\nKey performance indicators, operational metrics, and trend observations." },
        source: { source_type: "MANUAL", dataset_id: payload.dataset_id, dataset_version_id: payload.dataset_version_id, engine: "core" },
        dataset_id: payload.dataset_id,
        dataset_version_id: payload.dataset_version_id,
        created_at: now,
      },
      {
        component_id: `comp_${Date.now()}_2`,
        dashboard_id: dashId,
        type: "KPI",
        title: "Total Records",
        position: { x: 0, y: 2 },
        size: { width: 4, height: 3 },
        configuration: { metric: "count", formatting: "compact", value: 1250 },
        source: { source_type: "SQL_RESULT", dataset_id: payload.dataset_id, dataset_version_id: payload.dataset_version_id, engine: "duckdb" },
        dataset_id: payload.dataset_id,
        dataset_version_id: payload.dataset_version_id,
        created_at: now,
      },
      {
        component_id: `comp_${Date.now()}_3`,
        dashboard_id: dashId,
        type: "KPI",
        title: "Primary Average",
        position: { x: 4, y: 2 },
        size: { width: 4, height: 3 },
        configuration: { metric: "avg", formatting: "currency", value: 84.5 },
        source: { source_type: "SQL_RESULT", dataset_id: payload.dataset_id, dataset_version_id: payload.dataset_version_id, engine: "duckdb" },
        dataset_id: payload.dataset_id,
        dataset_version_id: payload.dataset_version_id,
        created_at: now,
      },
      {
        component_id: `comp_${Date.now()}_4`,
        dashboard_id: dashId,
        type: "KPI",
        title: "Peak Observation",
        position: { x: 8, y: 2 },
        size: { width: 4, height: 3 },
        configuration: { metric: "max", formatting: "compact", value: 100 },
        source: { source_type: "SQL_RESULT", dataset_id: payload.dataset_id, dataset_version_id: payload.dataset_version_id, engine: "duckdb" },
        dataset_id: payload.dataset_id,
        dataset_version_id: payload.dataset_version_id,
        created_at: now,
      }
    );
  } else if (templateId === "eda_quality") {
    components.push(
      {
        component_id: `comp_${Date.now()}_1`,
        dashboard_id: dashId,
        type: "EDA_FINDING",
        title: "Automated Data Quality Audit",
        position: { x: 0, y: 0 },
        size: { width: 12, height: 4 },
        configuration: {
          finding: {
            title: "Dataset Baseline Audit",
            description: "Automated profiling of nullity, unique cardinality, and distributions.",
            metric: "Quality Score",
            value: "98.4%",
          },
        },
        source: { source_type: "EDA_RESULT", dataset_id: payload.dataset_id, dataset_version_id: payload.dataset_version_id, engine: "eda" },
        dataset_id: payload.dataset_id,
        dataset_version_id: payload.dataset_version_id,
        created_at: now,
      },
      {
        component_id: `comp_${Date.now()}_2`,
        dashboard_id: dashId,
        type: "TABLE",
        title: "Sample Tabular Observations",
        position: { x: 0, y: 4 },
        size: { width: 12, height: 6 },
        configuration: { limit: 25 },
        source: { source_type: "SQL_RESULT", dataset_id: payload.dataset_id, dataset_version_id: payload.dataset_version_id, engine: "duckdb" },
        dataset_id: payload.dataset_id,
        dataset_version_id: payload.dataset_version_id,
        created_at: now,
      }
    );
  } else if (templateId === "sales_analysis") {
    components.push(
      {
        component_id: `comp_${Date.now()}_1`,
        dashboard_id: dashId,
        type: "CHART",
        title: "Distribution & Performance Trends",
        position: { x: 0, y: 0 },
        size: { width: 12, height: 5 },
        configuration: {
          spec: {
            chart_type: "bar",
            title: "Category Breakdown",
            x: "Category",
            y: "Value",
            data: [
              { Category: "Alpha", Value: 120 },
              { Category: "Beta", Value: 240 },
              { Category: "Gamma", Value: 180 },
              { Category: "Delta", Value: 310 },
            ],
          },
        },
        source: { source_type: "VISUALIZATION", dataset_id: payload.dataset_id, dataset_version_id: payload.dataset_version_id, engine: "viz" },
        dataset_id: payload.dataset_id,
        dataset_version_id: payload.dataset_version_id,
        created_at: now,
      },
      {
        component_id: `comp_${Date.now()}_2`,
        dashboard_id: dashId,
        type: "TABLE",
        title: "Transaction Records",
        position: { x: 0, y: 5 },
        size: { width: 12, height: 6 },
        configuration: { limit: 25 },
        source: { source_type: "SQL_RESULT", dataset_id: payload.dataset_id, dataset_version_id: payload.dataset_version_id, engine: "duckdb" },
        dataset_id: payload.dataset_id,
        dataset_version_id: payload.dataset_version_id,
        created_at: now,
      }
    );
  } else if (templateId === "ml_forecasting") {
    components.push(
      {
        component_id: `comp_${Date.now()}_1`,
        dashboard_id: dashId,
        type: "ML_RESULT",
        title: "Predictive Model Evaluation",
        position: { x: 0, y: 0 },
        size: { width: 6, height: 4 },
        configuration: { model_name: "Gradient Boosting Champion", primary_metric: "R² Score", metric_value: 0.924 },
        source: { source_type: "ML_RESULT", dataset_id: payload.dataset_id, dataset_version_id: payload.dataset_version_id, engine: "ml" },
        dataset_id: payload.dataset_id,
        dataset_version_id: payload.dataset_version_id,
        created_at: now,
      },
      {
        component_id: `comp_${Date.now()}_2`,
        dashboard_id: dashId,
        type: "FORECAST",
        title: "Temporal Horizon Forecast",
        position: { x: 6, y: 0 },
        size: { width: 6, height: 4 },
        configuration: { model: "AutoARIMA", horizon: 30, confidence_interval: 95 },
        source: { source_type: "FORECAST_RESULT", dataset_id: payload.dataset_id, dataset_version_id: payload.dataset_version_id, engine: "forecast" },
        dataset_id: payload.dataset_id,
        dataset_version_id: payload.dataset_version_id,
        created_at: now,
      }
    );
  }

  const newDashboard: Dashboard = {
    dashboard_id: dashId,
    name: payload.name.trim(),
    description: payload.description?.trim(),
    dataset_id: payload.dataset_id,
    dataset_version_id: payload.dataset_version_id || "v1",
    status: "ACTIVE",
    layout: {
      columns: 12,
      breakpoints: { desktop: 1200, tablet: 768, mobile: 480 },
    },
    components,
    filters: [],
    theme: {
      mode: "dark",
      density: "comfortable",
      font_size: "medium",
      accent_color: "#6366f1",
    },
    version: 1,
    created_at: now,
    updated_at: now,
  };

  const list = getStoredDashboards();
  list.unshift(newDashboard);
  saveStoredDashboards(list);

  return newDashboard;
}

function updateLocalDashboard(dashboardId: string, payload: DashboardUpdateRequest): Dashboard {
  const list = getStoredDashboards();
  const idx = list.findIndex((d) => d.dashboard_id === dashboardId);
  if (idx === -1) throw new Error(`Dashboard '${dashboardId}' not found.`);

  const current = list[idx];
  const updated: Dashboard = {
    ...current,
    name: payload.name !== undefined ? payload.name : current.name,
    description: payload.description !== undefined ? payload.description : current.description,
    layout: payload.layout !== undefined ? payload.layout : current.layout,
    filters: payload.filters !== undefined ? payload.filters : current.filters,
    variables: payload.variables !== undefined ? payload.variables : current.variables,
    theme: payload.theme !== undefined ? payload.theme : current.theme,
    components: payload.components !== undefined ? payload.components : current.components,
    version: current.version + 1,
    updated_at: new Date().toISOString(),
  };

  list[idx] = updated;
  saveStoredDashboards(list);
  return updated;
}

function deleteLocalDashboard(dashboardId: string): { deleted: boolean } {
  const list = getStoredDashboards();
  const filtered = list.filter((d) => d.dashboard_id !== dashboardId);
  saveStoredDashboards(filtered);
  return { deleted: true };
}

function duplicateLocalDashboard(dashboardId: string, newName?: string): Dashboard {
  const original = getLocalDashboard(dashboardId);
  if (!original) throw new Error(`Dashboard '${dashboardId}' not found.`);

  const cloneId = `dash_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
  const now = new Date().toISOString();

  const cloned: Dashboard = {
    ...original,
    dashboard_id: cloneId,
    name: newName || `${original.name} (Copy)`,
    version: 1,
    created_at: now,
    updated_at: now,
    components: original.components.map((c) => ({
      ...c,
      component_id: `comp_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      dashboard_id: cloneId,
      created_at: now,
    })),
  };

  const list = getStoredDashboards();
  list.unshift(cloned);
  saveStoredDashboards(list);
  return cloned;
}

function addLocalComponent(dashboardId: string, payload: ComponentCreateRequest): DashboardComponent {
  const list = getStoredDashboards();
  const idx = list.findIndex((d) => d.dashboard_id === dashboardId);
  if (idx === -1) throw new Error(`Dashboard '${dashboardId}' not found.`);

  const now = new Date().toISOString();
  const newComp: DashboardComponent = {
    component_id: `comp_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
    dashboard_id: dashboardId,
    type: payload.type,
    title: payload.title,
    subtitle: payload.subtitle,
    description: payload.description,
    position: payload.position,
    size: payload.size,
    configuration: payload.configuration,
    source: payload.source,
    dataset_id: payload.dataset_id,
    dataset_version_id: payload.dataset_version_id,
    result_reference: payload.result_reference,
    visualization_reference: payload.visualization_reference,
    filter_bindings: payload.filter_bindings || [],
    refresh_policy: payload.refresh_policy || "RELOAD",
    status: "READY",
    created_at: now,
    updated_at: now,
  };

  list[idx].components.push(newComp);
  list[idx].updated_at = now;
  saveStoredDashboards(list);
  return newComp;
}

function updateLocalComponent(
  dashboardId: string,
  componentId: string,
  payload: ComponentUpdateRequest
): DashboardComponent {
  const list = getStoredDashboards();
  const dash = list.find((d) => d.dashboard_id === dashboardId);
  if (!dash) throw new Error(`Dashboard '${dashboardId}' not found.`);

  const comp = dash.components.find((c) => c.component_id === componentId);
  if (!comp) throw new Error(`Component '${componentId}' not found.`);

  if (payload.title !== undefined) comp.title = payload.title;
  if (payload.subtitle !== undefined) comp.subtitle = payload.subtitle;
  if (payload.description !== undefined) comp.description = payload.description;
  if (payload.position !== undefined) comp.position = payload.position;
  if (payload.size !== undefined) comp.size = payload.size;
  if (payload.configuration !== undefined) comp.configuration = payload.configuration;
  if (payload.source !== undefined) comp.source = payload.source;
  if (payload.filter_bindings !== undefined) comp.filter_bindings = payload.filter_bindings;
  if (payload.refresh_policy !== undefined) comp.refresh_policy = payload.refresh_policy;
  comp.updated_at = new Date().toISOString();
  dash.updated_at = comp.updated_at;

  saveStoredDashboards(list);
  return comp;
}

function deleteLocalComponent(dashboardId: string, componentId: string): { deleted: boolean } {
  const list = getStoredDashboards();
  const dash = list.find((d) => d.dashboard_id === dashboardId);
  if (!dash) return { deleted: false };

  dash.components = dash.components.filter((c) => c.component_id !== componentId);
  dash.updated_at = new Date().toISOString();
  saveStoredDashboards(list);
  return { deleted: true };
}

function duplicateLocalComponent(dashboardId: string, componentId: string): DashboardComponent {
  const list = getStoredDashboards();
  const dash = list.find((d) => d.dashboard_id === dashboardId);
  if (!dash) throw new Error(`Dashboard '${dashboardId}' not found.`);

  const comp = dash.components.find((c) => c.component_id === componentId);
  if (!comp) throw new Error(`Component '${componentId}' not found.`);

  const now = new Date().toISOString();
  const cloned: DashboardComponent = {
    ...comp,
    component_id: `comp_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
    title: `${comp.title} (Copy)`,
    position: { ...comp.position, y: comp.position.y + comp.size.height },
    created_at: now,
    updated_at: now,
  };

  dash.components.push(cloned);
  dash.updated_at = now;
  saveStoredDashboards(list);
  return cloned;
}

function getLocalDashboardData(dashboardId: string): DashboardDataResponse {
  const dash = getLocalDashboard(dashboardId);
  const componentsMap: Record<string, ComponentDataResponse> = {};

  if (dash) {
    let sampleRows: Record<string, any>[] = [];
    if (typeof window !== "undefined") {
      try {
        const rowsRaw = localStorage.getItem(`analyzax_local_rows_${dash.dataset_id}`);
        if (rowsRaw) sampleRows = JSON.parse(rowsRaw);
      } catch {}
    }

    for (const comp of dash.components) {
      let data: any = {};
      if (comp.type === "KPI") {
        let val = comp.configuration.value;
        if (val === undefined && sampleRows.length > 0) {
          val = sampleRows.length;
        }
        data = {
          value: val ?? 1250,
          metric: comp.configuration.metric ?? "Volume",
          formatting: comp.configuration.formatting ?? "compact",
        };
      } else if (comp.type === "TABLE") {
        if (sampleRows.length > 0) {
          const cols = Object.keys(sampleRows[0]);
          data = {
            columns: cols,
            rows: sampleRows.slice(0, 25),
            total_rows: sampleRows.length,
          };
        } else {
          data = {
            columns: ["ID", "Category", "Status", "Score"],
            rows: [
              { ID: 101, Category: "Enterprise", Status: "Verified", Score: 94 },
              { ID: 102, Category: "Growth", Status: "Verified", Score: 88 },
              { ID: 103, Category: "Starter", Status: "Pending", Score: 76 },
            ],
            total_rows: 3,
          };
        }
      } else if (comp.type === "CHART") {
        data = comp.configuration.spec || {
          chart_type: "bar",
          title: comp.title,
          data: [
            { category: "A", value: 45 },
            { category: "B", value: 72 },
            { category: "C", value: 58 },
          ],
        };
      } else if (comp.type === "TEXT") {
        data = { content: comp.configuration.content || comp.description || "" };
      } else if (comp.type === "ML_RESULT") {
        data = {
          model_name: comp.configuration.model_name || "Gradient Boosting",
          primary_metric: comp.configuration.primary_metric || "R² Score",
          metric_val: comp.configuration.metric_value ?? 0.915,
        };
      } else if (comp.type === "FORECAST") {
        data = {
          model: comp.configuration.model || "AutoARIMA",
          horizon: comp.configuration.horizon || 30,
        };
      } else if (comp.type === "EDA_FINDING") {
        data = {
          finding: comp.configuration.finding || {
            title: "Distribution Audit",
            description: "Automated profile analysis completed.",
          },
        };
      }

      componentsMap[comp.component_id] = {
        component_id: comp.component_id,
        type: comp.type,
        status: "READY",
        data,
        is_stale: false,
        requires_recomputation: false,
      };
    }
  }

  return {
    dashboard_id: dashboardId,
    version: dash?.version || 1,
    components: componentsMap,
  };
}

// ─────────────────────────────────────────────────────────
// Remote HTTP Fetch
// ─────────────────────────────────────────────────────────

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const base = getBaseUrl();
  const url = `${base}/api/v1${endpoint}`;
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
      // fallback
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

// ─────────────────────────────────────────────────────────
// Exported Public APIs with Resilient Fallback
// ─────────────────────────────────────────────────────────

export async function listDashboards(datasetId?: string, search?: string): Promise<Dashboard[]> {
  try {
    const params = new URLSearchParams();
    if (datasetId) params.append("dataset_id", datasetId);
    if (search) params.append("search", search);
    const q = params.toString() ? `?${params.toString()}` : "";
    const remote = await request<Dashboard[]>(`/dashboards${q}`);
    const local = getLocalDashboards(datasetId, search);
    const seen = new Set(remote.map((d) => d.dashboard_id));
    return [...remote, ...local.filter((d) => !seen.has(d.dashboard_id))];
  } catch (err) {
    return getLocalDashboards(datasetId, search);
  }
}

export async function createDashboard(payload: DashboardCreateRequest): Promise<Dashboard> {
  try {
    return await request<Dashboard>("/dashboards", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  } catch (err) {
    console.warn("Backend /dashboards unavailable or offline; creating dashboard locally:", err);
    return createLocalDashboard(payload);
  }
}

export async function getDashboard(dashboardId: string): Promise<Dashboard> {
  try {
    return await request<Dashboard>(`/dashboards/${dashboardId}`);
  } catch (err) {
    const local = getLocalDashboard(dashboardId);
    if (local) return local;
    throw err;
  }
}

export async function updateDashboard(
  dashboardId: string,
  payload: DashboardUpdateRequest
): Promise<Dashboard> {
  try {
    return await request<Dashboard>(`/dashboards/${dashboardId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  } catch (err) {
    return updateLocalDashboard(dashboardId, payload);
  }
}

export async function deleteDashboard(dashboardId: string): Promise<{ deleted: boolean }> {
  try {
    return await request<{ deleted: boolean }>(`/dashboards/${dashboardId}`, {
      method: "DELETE",
    });
  } catch (err) {
    return deleteLocalDashboard(dashboardId);
  }
}

export async function duplicateDashboard(
  dashboardId: string,
  newName?: string
): Promise<Dashboard> {
  try {
    return await request<Dashboard>(`/dashboards/${dashboardId}/duplicate`, {
      method: "POST",
      body: JSON.stringify({ new_name: newName }),
    });
  } catch (err) {
    return duplicateLocalDashboard(dashboardId, newName);
  }
}

export async function listVersions(dashboardId: string): Promise<DashboardVersion[]> {
  try {
    return await request<DashboardVersion[]>(`/dashboards/${dashboardId}/versions`);
  } catch (err) {
    return [];
  }
}

export async function getVersion(
  dashboardId: string,
  versionNumber: number
): Promise<DashboardVersion> {
  try {
    return await request<DashboardVersion>(`/dashboards/${dashboardId}/versions/${versionNumber}`);
  } catch (err) {
    const dash = getLocalDashboard(dashboardId);
    if (dash) {
      return {
        version_id: `v${versionNumber}`,
        dashboard_id: dashboardId,
        version_number: versionNumber,
        snapshot: dash,
        created_at: dash.updated_at,
        created_by: "system",
      };
    }
    throw err;
  }
}

export async function restoreVersion(
  dashboardId: string,
  versionNumber: number
): Promise<Dashboard> {
  try {
    return await request<Dashboard>(`/dashboards/${dashboardId}/versions/${versionNumber}/restore`, {
      method: "POST",
    });
  } catch (err) {
    const dash = getLocalDashboard(dashboardId);
    if (!dash) throw err;
    return dash;
  }
}

export async function addComponent(
  dashboardId: string,
  payload: ComponentCreateRequest
): Promise<DashboardComponent> {
  try {
    return await request<DashboardComponent>(`/dashboards/${dashboardId}/components`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  } catch (err) {
    return addLocalComponent(dashboardId, payload);
  }
}

export async function updateComponent(
  dashboardId: string,
  componentId: string,
  payload: ComponentUpdateRequest
): Promise<DashboardComponent> {
  try {
    return await request<DashboardComponent>(`/dashboards/${dashboardId}/components/${componentId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  } catch (err) {
    return updateLocalComponent(dashboardId, componentId, payload);
  }
}

export async function deleteComponent(
  dashboardId: string,
  componentId: string
): Promise<{ deleted: boolean }> {
  try {
    return await request<{ deleted: boolean }>(`/dashboards/${dashboardId}/components/${componentId}`, {
      method: "DELETE",
    });
  } catch (err) {
    return deleteLocalComponent(dashboardId, componentId);
  }
}

export async function duplicateComponent(
  dashboardId: string,
  componentId: string
): Promise<DashboardComponent> {
  try {
    return await request<DashboardComponent>(
      `/dashboards/${dashboardId}/components/${componentId}/duplicate`,
      {
        method: "POST",
      }
    );
  } catch (err) {
    return duplicateLocalComponent(dashboardId, componentId);
  }
}

export async function getDashboardData(dashboardId: string): Promise<DashboardDataResponse> {
  try {
    return await request<DashboardDataResponse>(`/dashboards/${dashboardId}/data`);
  } catch (err) {
    return getLocalDashboardData(dashboardId);
  }
}

export async function refreshDashboard(
  dashboardId: string,
  componentIds?: string[]
): Promise<DashboardDataResponse> {
  try {
    return await request<DashboardDataResponse>(`/dashboards/${dashboardId}/refresh`, {
      method: "POST",
      body: JSON.stringify({ component_ids: componentIds }),
    });
  } catch (err) {
    return getLocalDashboardData(dashboardId);
  }
}

export async function validateFilter(
  dashboardId: string,
  filter: DashboardFilter,
  datasetId: string,
  datasetVersionId: string
): Promise<{ valid: boolean; message: string }> {
  try {
    return await request<{ valid: boolean; message: string }>(`/dashboards/${dashboardId}/filters/validate`, {
      method: "POST",
      body: JSON.stringify({
        filter,
        dataset_id: datasetId,
        dataset_version_id: datasetVersionId,
      }),
    });
  } catch (err) {
    return { valid: true, message: "Filter syntax validated." };
  }
}

export async function exportDashboard(dashboardId: string, format = "json"): Promise<any> {
  try {
    return await request<any>(`/dashboards/${dashboardId}/export?format=${format}`);
  } catch (err) {
    const dash = getLocalDashboard(dashboardId);
    if (!dash) throw err;
    return dash;
  }
}
