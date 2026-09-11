// TypeScript interfaces for Phase 14 Dashboard, Insight Workspace, and Analytical Storytelling

export type ComponentType =
  | "CHART"
  | "TABLE"
  | "KPI"
  | "TEXT"
  | "STATISTICS"
  | "ML_RESULT"
  | "FORECAST"
  | "EDA_FINDING"
  | "AI_INSIGHT"
  | "DIVIDER"
  | "SECTION";

export type SourceType =
  | "SQL_RESULT"
  | "EDA_RESULT"
  | "STATISTICAL_RESULT"
  | "ML_RESULT"
  | "FORECAST_RESULT"
  | "VISUALIZATION"
  | "AI_ANALYST_RESULT"
  | "MANUAL";

export type RefreshPolicy = "RELOAD" | "RECOMPUTE" | "STATIC";

export type ComponentStatus =
  | "IDLE"
  | "LOADING"
  | "READY"
  | "STALE_VERSION"
  | "ERROR"
  | "UNAVAILABLE";

export type FilterScope = "GLOBAL" | "COMPONENT";

export type FilterOperator =
  | "equals"
  | "not_equals"
  | "in"
  | "not_in"
  | "greater_than"
  | "greater_than_or_equal"
  | "less_than"
  | "less_than_or_equal"
  | "between"
  | "contains"
  | "starts_with"
  | "is_null"
  | "is_not_null";

export interface ComponentPosition {
  x: number; // 0-11
  y: number; // row offset
}

export interface ComponentSize {
  width: number; // 1-12
  height: number; // grid row units
}

export interface ComponentSource {
  source_type: SourceType;
  source_id?: string;
  dataset_id: string;
  dataset_version_id: string;
  result_id?: string;
  chart_id?: string;
  engine: string;
  created_at?: string;
}

export interface ComponentProvenance {
  dataset_id: string;
  dataset_version_id: string;
  source_engine: string;
  result_id?: string;
  chart_id?: string;
  created_at: string;
  last_refreshed_at?: string;
  is_stale: boolean;
  stale_reason?: string;
}

export interface DashboardFilter {
  filter_id: string;
  field: string;
  operator: FilterOperator;
  value: any;
  value2?: any;
  data_type: string;
  scope: FilterScope;
  component_ids?: string[];
  default_value?: any;
  label?: string;
}

export interface DashboardComponent {
  component_id: string;
  dashboard_id: string;
  type: ComponentType;
  title: string;
  subtitle?: string;
  description?: string;
  position: ComponentPosition;
  size: ComponentSize;
  configuration: Record<string, any>;
  source: ComponentSource;
  dataset_id: string;
  dataset_version_id: string;
  result_reference?: Record<string, any>;
  visualization_reference?: Record<string, any>;
  filter_bindings?: string[];
  refresh_policy?: RefreshPolicy;
  status?: ComponentStatus;
  provenance?: ComponentProvenance;
  visibility?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface DashboardLayout {
  columns: number;
  breakpoints: {
    desktop: number;
    tablet: number;
    mobile: number;
  };
}

export interface DashboardTheme {
  mode: string;
  density: "compact" | "comfortable" | "spacious";
  font_size: "small" | "medium" | "large";
  accent_color: string;
}

export interface Dashboard {
  dashboard_id: string;
  name: string;
  description?: string;
  dataset_id: string;
  dataset_version_id: string;
  status: string;
  layout: DashboardLayout;
  components: DashboardComponent[];
  filters: DashboardFilter[];
  variables?: Record<string, any>;
  theme: DashboardTheme;
  version: number;
  configuration_hash?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface DashboardVersion {
  version_id: string;
  dashboard_id: string;
  version_number: number;
  snapshot: Dashboard;
  created_at: string;
  created_by: string;
  comment?: string;
}

export interface ComponentDataResponse {
  component_id: string;
  type: ComponentType;
  status: ComponentStatus;
  data: any;
  is_stale: boolean;
  stale_reason?: string;
  requires_recomputation: boolean;
  recomputation_reason?: string;
  error_message?: string;
  provenance?: ComponentProvenance;
  refreshed_at: string;
}

export interface DashboardDataResponse {
  dashboard_id: string;
  version: number;
  generated_at: string;
  components: Record<string, ComponentDataResponse>;
  warnings: string[];
  stale_components_count: number;
}

export interface DashboardCreateRequest {
  name: string;
  description?: string;
  dataset_id: string;
  dataset_version_id?: string;
  template_id?: string;
}

export interface DashboardUpdateRequest {
  name?: string;
  description?: string;
  layout?: DashboardLayout;
  components?: DashboardComponent[];
  filters?: DashboardFilter[];
  variables?: Record<string, any>;
  theme?: DashboardTheme;
  expected_version?: number;
  expected_hash?: string;
}

export interface ComponentCreateRequest {
  type: ComponentType;
  title: string;
  subtitle?: string;
  description?: string;
  position?: ComponentPosition;
  size?: ComponentSize;
  configuration: Record<string, any>;
  source: ComponentSource;
  result_reference?: Record<string, any>;
  visualization_reference?: Record<string, any>;
  filter_bindings?: string[];
  refresh_policy?: RefreshPolicy;
}

export interface ComponentUpdateRequest {
  title?: string;
  subtitle?: string;
  description?: string;
  position?: ComponentPosition;
  size?: ComponentSize;
  configuration?: Record<string, any>;
  source?: ComponentSource;
  filter_bindings?: string[];
  refresh_policy?: RefreshPolicy;
  visibility?: boolean;
}
