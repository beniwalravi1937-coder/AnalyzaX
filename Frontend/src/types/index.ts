// Shared TypeScript interfaces for AnalyzaX
// Keep these synchronized with backend schemas and domain models

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  database: string;
  duckdb: string;
  duckdb_version?: string;
}

// ─────────────────────────────────────────────────────────────
// Dataset Domain Types
// ─────────────────────────────────────────────────────────────

export type DatasetStatus = "uploading" | "processing" | "ready" | "error" | "UPLOADING" | "VALIDATING" | "STORING" | "INGESTING" | "READY" | "FAILED";

export interface DatasetResponse {
  id: string;
  name: string;
  original_filename: string;
  filename?: string;
  format: "csv" | "xlsx" | "json" | "parquet" | string;
  file_size_bytes: number;
  status: string;
  duckdb_table_name: string;
  sheet_name?: string | null;
  created_at: string;
  updated_at: string;
  error_message?: string | null;
  active_version_id?: string | null;
  current_version_id?: string | null;
}

export interface Dataset {
  id: string;
  name: string;
  filename: string;
  format: "csv" | "xlsx" | "json" | "parquet";
  sizeBytes: number;
  rowCount?: number;
  columnCount?: number;
  createdAt: string;
  updatedAt: string;
  status: DatasetStatus;
  version: number;
  description?: string;
}

export interface QuantilesSummary {
  p0?: number | null;
  p5?: number | null;
  p25?: number | null;
  p50?: number | null;
  p75?: number | null;
  p95?: number | null;
  p100?: number | null;
  iqr?: number | null;
}

export interface NumericMetrics {
  min?: number | null;
  max?: number | null;
  mean?: number | null;
  median?: number | null;
  stddev?: number | null;
  variance?: number | null;
  skewness?: number | null;
  kurtosis?: number | null;
  quantiles?: QuantilesSummary | null;
}

export interface CategoryFrequency {
  value: string | number | boolean;
  count: number;
  percentage: number;
}

export interface CategoricalMetrics {
  top_categories: CategoryFrequency[];
  avg_length?: number | null;
  max_length?: number | null;
  is_text: boolean;
}

export interface DatetimeMetrics {
  min_timestamp?: string | null;
  max_timestamp?: string | null;
  span_days?: number | null;
  distinct_dates_count?: number | null;
  detected_frequency?: string | null;
}

export interface TargetCandidate {
  column_name: string;
  task_type: "binary_classification" | "multiclass_classification" | "regression" | string;
  confidence: number;
  reason: string;
}

export interface ColumnProfile {
  name: string;
  physical_type: string;
  semantic_type: string;
  semantic_confidence: number;
  nullable: boolean;
  null_count: number;
  null_percentage: number;
  unique_count: number;
  unique_percentage: number;
  cardinality_ratio: number;
  sample_values: (string | number | boolean | null)[];
  numeric_metrics?: NumericMetrics | null;
  categorical_metrics?: CategoricalMetrics | null;
  datetime_metrics?: DatetimeMetrics | null;
  is_identifier_candidate: boolean;
  identifier_confidence: number;
  target_candidate?: TargetCandidate | null;
}

export interface DatasetProfileResponse {
  dataset_id: string;
  row_count: number;
  column_count: number;
  columns: ColumnProfile[];
  numeric_columns_count: number;
  categorical_columns_count: number;
  datetime_columns_count: number;
  identifier_columns_count: number;
  target_candidates: TargetCandidate[];
  profiling_version: string;
  status: "NOT_STARTED" | "PROFILING" | "READY" | "FAILED" | string;
  generated_at: string;
  error_message?: string | null;
}

export interface DatasetColumn {
  name: string;
  type: string;
  inferredType: "numeric" | "categorical" | "datetime" | "text" | "boolean" | "unknown";
  nullCount: number;
  nullPercentage: number;
  uniqueCount: number;
  sampleValues: (string | number | boolean | null)[];
}

// ─────────────────────────────────────────────────────────────
// Data Quality Assessment Types
// ─────────────────────────────────────────────────────────────

export interface QualityMetric {
  name: string;
  score: number; // 0 - 100
  status: "good" | "warning" | "critical";
  description: string;
  issuesCount: number;
}

export interface DataQualityReport {
  overallScore: number;
  metrics: QualityMetric[];
  missingCellsTotal: number;
  duplicateRowsTotal: number;
  inconsistentTypesCount: number;
  outliersDetected: number;
  evaluatedAt: string;
}

// ─────────────────────────────────────────────────────────────
// Table & SQL Types
// ─────────────────────────────────────────────────────────────

export interface TableColumn {
  name: string;
  type?: string;
  nullable?: boolean;
}

export interface TableResult {
  columns: TableColumn[];
  rows: Record<string, unknown>[];
  totalRows: number;
  executionTimeMs?: number;
}

export interface LegacyQueryHistoryItem {
  id: string;
  query: string;
  executedAt: string;
  durationMs: number;
  status: "success" | "error";
  rowCount?: number;
  errorMessage?: string;
}

// (Visualization & Chart Types are defined under Phase 7 EDA section below)

// ─────────────────────────────────────────────────────────────
// Machine Learning & Forecasting Types
// ─────────────────────────────────────────────────────────────

export type MLTaskType = "classification" | "regression" | "clustering" | "anomaly_detection";

export interface MLModelSummary {
  id: string;
  name: string;
  taskType: MLTaskType;
  targetColumn?: string;
  metricName: string;
  metricValue: number;
  status: "trained" | "evaluating" | "ready";
}

export interface ForecastConfig {
  metricColumn: string;
  dateColumn: string;
  horizonPeriods: number;
  frequency: "D" | "W" | "M" | "Q" | "Y";
  confidenceLevel: number; // e.g., 0.95
}

// ─────────────────────────────────────────────────────────────
// AI Analyst Chat Types
// ─────────────────────────────────────────────────────────────

export type ChatRole = "user" | "assistant" | "system" | "tool";

export interface ToolCallRecord {
  id: string;
  toolName: string;
  query?: string;
  status: "running" | "completed" | "failed";
  durationMs?: number;
  resultSummary?: string;
}

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: string;
  toolCalls?: ToolCallRecord[];
  chartSpec?: ChartSpec;
  tableData?: TableResult;
}

// ─────────────────────────────────────────────────────────────
// Export Types
// ─────────────────────────────────────────────────────────────

export type ExportFormat = "csv" | "parquet" | "xlsx" | "pdf" | "html" | "json";

export interface ExportJob {
  id: string;
  datasetId: string;
  format: ExportFormat;
  status: "pending" | "processing" | "ready" | "failed";
  downloadUrl?: string;
  createdAt: string;
}

// ─────────────────────────────────────────────────────────────
// Data Quality Types (Phase 5)
// ─────────────────────────────────────────────────────────────

export type QualitySeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";

export type QualityDimension =
  | "COMPLETENESS"
  | "UNIQUENESS"
  | "VALIDITY"
  | "CONSISTENCY"
  | "INTEGRITY"
  | "ANOMALY_RISK";

export interface QualityIssue {
  issue_id: string;
  dataset_id: string;
  dataset_version: string;
  issue_type: string;
  dimension: QualityDimension;
  severity: QualitySeverity;
  column_name?: string | null;
  affected_rows: number;
  affected_percentage: number;
  description: string;
  evidence: Record<string, unknown>;
  rule_id: string;
  confidence: number;
  recommended_action: string;
  created_at: string;
}

export interface DimensionScore {
  dimension: QualityDimension;
  score: number;
  issue_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  info_count: number;
  description: string;
}

export interface ColumnQualitySummary {
  column_name: string;
  physical_type: string;
  semantic_type: string;
  quality_score: number;
  null_percentage: number;
  unique_percentage: number;
  issues_count: number;
  highest_severity?: QualitySeverity | null;
  issue_types: string[];
}

export interface DataQualityReportResponse {
  dataset_id: string;
  dataset_version: string;
  quality_report_version: string;
  status: string;
  overall_score: number;
  overall_grade: "EXCELLENT" | "GOOD" | "FAIR" | "POOR" | "CRITICAL" | string;
  dimension_scores: Record<QualityDimension, DimensionScore>;
  total_issues: number;
  critical_issues: number;
  high_issues: number;
  medium_issues: number;
  low_issues: number;
  info_issues: number;
  affected_rows: number;
  affected_columns: number;
  issues: QualityIssue[];
  column_summaries: ColumnQualitySummary[];
  execution_time_ms: number;
  scoring_explanation: string;
  generated_at: string;
}

export interface QualityFilters {
  severity?: QualitySeverity;
  dimension?: QualityDimension;
  column?: string;
}

// ─────────────────────────────────────────────────────────────
// Phase 6: Cleaning, Transformations & Dataset Versioning Types
// ─────────────────────────────────────────────────────────────

export type TransformationType =
  | "FILL_MISSING"
  | "DROP_MISSING"
  | "DROP_DUPLICATES"
  | "TRIM_WHITESPACE"
  | "TEXT_CASE"
  | "REPLACE_TEXT"
  | "NORMALIZE_CATEGORIES"
  | "CAST_TYPE"
  | "PARSE_DATE"
  | "EXTRACT_DATE_PARTS"
  | "FILTER_ROWS"
  | "DROP_COLUMNS"
  | "RENAME_COLUMN"
  | "REORDER_COLUMNS"
  | "DERIVED_COLUMN"
  | "ONE_HOT_ENCODE"
  | "LABEL_ENCODE"
  | "SCALE_NUMERIC"
  | "HANDLE_OUTLIERS";

export type PlanStatus =
  | "DRAFT"
  | "VALIDATING"
  | "PREVIEW_READY"
  | "APPROVED"
  | "EXECUTING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";

export interface TransformationStep {
  step_id: string;
  type: TransformationType;
  parameters: Record<string, any>;
  input_columns?: string[];
  output_columns?: string[];
  description: string;
  enabled?: boolean;
}

export interface TransformationPlan {
  plan_id: string;
  dataset_id: string;
  source_version_id: string;
  steps: TransformationStep[];
  status: PlanStatus;
  created_at: string;
  updated_at: string;
}

export interface StepSummary {
  step_id: string;
  type: string;
  description: string;
  rows_affected: number;
  columns_affected: number;
  schema_change?: string | null;
}

export interface TransformationPreview {
  plan_id: string;
  source_version_id: string;
  sample_before: Record<string, any>[];
  sample_after: Record<string, any>[];
  columns_before: string[];
  columns_after: string[];
  rows_before: number;
  rows_after: number;
  rows_affected: number;
  step_summaries: StepSummary[];
  validation_errors: string[];
}

export interface DryRunResult {
  valid: boolean;
  validation_errors: string[];
  source_version_id: string;
  estimated_rows: number;
  estimated_columns: number;
  schema_diff?: Record<string, any>;
  quality_impact_prediction?: Record<string, any>;
}

export interface CleaningRecommendation {
  recommendation_id: string;
  issue_id?: string | null;
  title: string;
  description: string;
  reason: string;
  risk: RiskLevel;
  confidence: number;
  suggested_step: TransformationStep;
}

export interface DatasetVersion {
  version_id: string;
  dataset_id: string;
  version_number: number;
  version_label: string;
  parent_version_id?: string | null;
  storage_path: string;
  duckdb_table_name: string;
  row_count: number;
  column_count: number;
  file_size_bytes: number;
  schema_hash: string;
  data_hash: string;
  pipeline_hash?: string | null;
  status: string;
  created_at: string;
  created_by: string;
  operation_count: number;
}

export interface DimensionComparison {
  before: number;
  after: number;
  delta: number;
}

export interface QualityComparison {
  before_version_id: string;
  after_version_id: string;
  before_score: number;
  after_score: number;
  score_delta: number;
  before_grade: string;
  after_grade: string;
  before_total_issues: number;
  after_total_issues: number;
  issues_delta: number;
  metrics_comparison: {
    dimensions: Record<string, DimensionComparison>;
    rows_before: number;
    rows_after: number;
  };
  improvements: string[];
  regressions: string[];
}

export interface TransformationAudit {
  audit_id: string;
  dataset_id: string;
  source_version_id: string;
  new_version_id: string;
  plan_id: string;
  steps_applied: number;
  rows_before: number;
  rows_after: number;
  rows_affected: number;
  execution_time_ms: number;
  created_at: string;
}

export interface ApplyPlanResponse {
  new_version: DatasetVersion;
  comparison: QualityComparison;
  audit: TransformationAudit;
}

export interface LineageNode {
  id: string;
  label: string;
  version_number: number;
  row_count: number;
  column_count: number;
  created_at: string;
  is_active: boolean;
}

export interface LineageLink {
  source: string;
  target: string;
}

export interface LineageResponse {
  dataset_id: string;
  active_version_id?: string | null;
  nodes: LineageNode[];
  links: LineageLink[];
}

// ─────────────────────────────────────────────────────────────
// Phase 7: Exploratory Data Analysis (EDA) Types
// ─────────────────────────────────────────────────────────────

export type ChartType =
  | "histogram"
  | "box"
  | "boxplot"
  | "violin"
  | "ecdf"
  | "density"
  | "bar"
  | "horizontal_bar"
  | "grouped_bar"
  | "stacked_bar"
  | "percent_stacked_bar"
  | "pareto"
  | "scatter"
  | "bubble"
  | "heatmap"
  | "correlation_matrix"
  | "line"
  | "multi_line"
  | "area"
  | "stacked_area"
  | "time_bar"
  | "donut"
  | "pie"
  | "treemap"
  | "kpi"
  | "kpi_card"
  | "gauge"
  | "radar"
  | "waterfall"
  | "funnel"
  | "sankey"
  | "candlestick"
  | "table"
  | string;

export interface ChartOptions {
  interactive?: boolean;
  color_scheme?: string;
  show_grid?: boolean;
  show_legend?: boolean;
  showLegend?: boolean;
  height_px?: number;
  width_ratio?: string;
  animation_duration_ms?: number;
  xAxisLabel?: string;
  yAxisLabel?: string;
}

export interface StructuredFilter {
  field?: string;
  column?: string;
  operator:
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
    | "is_not_null"
    | "eq"
    | "neq"
    | "gt"
    | "gte"
    | "lt"
    | "lte"
    | "like";
  value?: any;
  value2?: any;
}

export interface ChartSamplingMetadata {
  is_sampled: boolean;
  original_row_count: number;
  displayed_points?: number;
  sample_size?: number;
  sampling_method?: string;
}

export interface ChartAxesConfig {
  x_label?: string | null;
  y_label?: string | null;
  x_rotate?: number | null;
  y_min?: number | null;
  y_max?: number | null;
  log_scale?: boolean;
  zero_baseline?: boolean;
  show_grid?: boolean;
}

export interface ChartLegendConfig {
  show?: boolean;
  position?: "top" | "bottom" | "left" | "right";
}

export interface ChartAnnotation {
  type: "reference_line" | "threshold" | "marker";
  value: number;
  axis?: "x" | "y";
  label?: string | null;
  color?: string | null;
}

export interface ChartInteractions {
  zoom?: boolean;
  pan?: boolean;
  brush?: boolean;
  crossfilter_enabled?: boolean;
}

export interface ChartTopNConfig {
  n: number;
  include_other: boolean;
  other_label?: string;
  enabled?: boolean;
}

export interface VisualizationProvenance {
  dataset_id: string;
  dataset_version_id: string;
  source_type: "dataset" | "sql" | "eda" | "manual";
  source_reference?: string | null;
  created_at: string;
  created_by?: string;
}

export interface ChartSpec {
  spec_version?: string;
  id?: string;
  chart_id?: string;
  chart_type?: ChartType;
  title: string;
  subtitle?: string | null;
  description?: string | null;
  dataset_id?: string;
  version_id?: string;
  dataset_version_id?: string;
  source_type?: "dataset" | "sql" | "eda" | "manual";
  source_reference?: string | null;
  x?: string | null;
  y?: string | null;
  series?: string | null;
  color?: string | null;
  size?: string | null;
  tooltip?: string[] | null;
  filters?: StructuredFilter[];
  sort_direction?: "asc" | "desc" | null;
  sort_by?: "value" | "category" | "chronological" | null;
  aggregation?: "sum" | "avg" | "median" | "min" | "max" | "count" | "count_distinct" | "none" | string;
  top_n?: ChartTopNConfig | null;
  formatting?: Record<string, string>;
  axes?: ChartAxesConfig;
  legend?: ChartLegendConfig;
  annotations?: ChartAnnotation[];
  interactions?: ChartInteractions;
  data?: Record<string, any>[];
  options?: ChartOptions;
  sampling?: ChartSamplingMetadata | null;
  provenance?: VisualizationProvenance | null;
  metadata?: Record<string, any>;
  // Extended configuration fields
  x_axis?: { field: string; type?: "category" | "value" | "time" | string; title?: string; aggregation?: string } | null;
  y_axis?: { field: string; type?: "category" | "value" | "time" | string; title?: string; aggregation?: string } | null;
  series_field?: string | null;
  color_scheme?: string | null;
  rule_id?: string | null;
  // Legacy compatibility fields
  type?: ChartType | string;
  x_field?: string | null;
  y_field?: string | null;
  color_field?: string | null;
  x_label?: string | null;
  y_label?: string | null;
  colorBy?: string;
}

export interface EDAOverview {
  dataset_id: string;
  version_id: string;
  row_count: number;
  column_count: number;
  numeric_columns_count: number;
  categorical_columns_count: number;
  datetime_columns_count: number;
  other_columns_count: number;
  total_missing_cells: number;
  missing_percentage: number;
  duplicate_rows_count: number;
  duplicate_percentage: number;
  storage_size_bytes?: number | null;
  quality_score?: number | null;
  quality_timestamp?: string | null;
  anomalies_detected_count: number;
  analysis_timestamp: string;
}

export interface EDAHistogramBin {
  bin_start: number;
  bin_end: number;
  count: number;
  frequency: number;
}

export interface HistogramData {
  bins: EDAHistogramBin[];
  bin_width: number;
  num_bins: number;
}

export interface BoxPlotData {
  min: number;
  p25: number;
  median: number;
  p75: number;
  max: number;
  iqr: number;
  lower_fence: number;
  upper_fence: number;
  outliers_count: number;
}

export interface NumericColumnAnalysis {
  column: string;
  count: number;
  null_count: number;
  mean: number;
  std: number;
  min: number;
  p25: number;
  median: number;
  p75: number;
  max: number;
  iqr: number;
  skewness: number;
  kurtosis: number;
  variance: number;
  histogram: HistogramData;
  box_plot: BoxPlotData;
  outlier_count_tukey: number;
  outlier_percentage: number;
  parametric?: {
    mean: number;
    std: number;
    skewness: number;
    kurtosis: number;
    variance?: number;
  };
  non_parametric?: {
    median: number;
    iqr: number;
    min: number;
    max: number;
    p25?: number;
    p75?: number;
  };
  outliers?: {
    outlier_count: number;
    outlier_percentage: number;
  };
}

export interface CategoryItem {
  category: string;
  count: number;
  percentage: number;
}

export interface CategoricalColumnAnalysis {
  column: string;
  count: number;
  total_count?: number;
  null_count: number;
  missing_percentage?: number;
  unique_count: number;
  is_high_cardinality: boolean;
  cardinality_class?: string;
  dominant_category?: string | null;
  dominant_category_percentage: number;
  entropy?: number | null;
  shannon_entropy?: number | null;
  top_categories: CategoryItem[];
}

export interface DatetimeTrendBucket {
  period_label: string;
  count: number;
}

export interface DatetimeColumnAnalysis {
  column: string;
  count: number;
  null_count: number;
  min_timestamp?: string | null;
  max_timestamp?: string | null;
  earliest?: string | null;
  latest?: string | null;
  span_days?: number | null;
  detected_frequency?: string | null;
  inferred_frequency?: string | null;
  missing_percentage?: number;
  temporal_trends: DatetimeTrendBucket[];
  day_of_week_distribution: Record<string, number>;
  month_distribution: Record<string, number>;
}

export interface CorrelationPair {
  column_x: string;
  column_y: string;
  column_a?: string;
  column_b?: string;
  correlation: number;
  abs_correlation: number;
  strength: "very_strong" | "strong" | "moderate" | "weak" | "none" | string;
  direction?: "positive" | "negative" | string;
}

export interface CorrelationMatrixResponse {
  method: "pearson" | "spearman" | "kendall" | string;
  columns: string[];
  matrix: number[][];
  ranked_pairs: CorrelationPair[];
  top_correlations?: CorrelationPair[];
}

export interface RegressionLine {
  slope: number;
  intercept: number;
  r_squared: number;
}

export interface ScatterPoint {
  x: number;
  y: number;
}

export interface NumericNumericRelationship {
  column_x: string;
  column_y: string;
  correlation: number;
  regression?: RegressionLine | null;
  sample_points: ScatterPoint[];
  sampling: ChartSamplingMetadata;
}

export interface CategoryGroupStats {
  category: string;
  count: number;
  mean: number;
  median: number;
  min: number;
  max: number;
  p25: number;
  p75: number;
}

export interface NumericCategoricalRelationship {
  numeric_column: string;
  categorical_column: string;
  group_stats: CategoryGroupStats[];
}

export interface ContingencyCell {
  val_x: string;
  val_y: string;
  count: number;
  expected_count: number;
}

export interface CategoricalCategoricalRelationship {
  column_x: string;
  column_y: string;
  cramers_v: number;
  contingency_table: ContingencyCell[];
}

export interface ColumnMissingness {
  column: string;
  null_count: number;
  null_percentage: number;
  semantic_type: string;
}

export interface MissingnessSummary {
  total_missing_cells: number;
  overall_missing_percentage: number;
  complete_rows_count: number;
  incomplete_rows_count: number;
  column_missingness: ColumnMissingness[];
}

export interface ColumnOutlierDetail {
  column: string;
  outlier_count: number;
  outlier_percentage: number;
  lower_fence: number;
  upper_fence: number;
  sample_extreme_values: number[];
}

export interface OutliersSummary {
  total_outlier_count: number;
  columns_with_outliers: ColumnOutlierDetail[];
}

export interface ColumnCardinalityInfo {
  column: string;
  unique_count: number;
  cardinality_ratio: number;
  is_unique: boolean;
  is_high_cardinality: boolean;
  is_identifier_candidate: boolean;
}

export interface CardinalitySummary {
  columns: ColumnCardinalityInfo[];
  identifier_candidates: string[];
  constant_columns: string[];
}

export type FindingCategory =
  | "DISTRIBUTION"
  | "RELATIONSHIP"
  | "MISSINGNESS"
  | "ANOMALY"
  | "CATEGORY"
  | "TIME"
  | "CARDINALITY"
  | "DATA_HEALTH"
  | "distribution"
  | "relationship"
  | "anomaly"
  | "missingness"
  | "time_trend"
  | "category"
  | "general"
  | string;

export type FindingSeverity =
  | "INFO"
  | "LOW"
  | "MEDIUM"
  | "HIGH"
  | "CRITICAL"
  | "critical"
  | "warning"
  | "alert"
  | "insight"
  | "info"
  | string;

export interface EDAFinding {
  id?: string;
  finding_id?: string;
  category: FindingCategory;
  severity: FindingSeverity;
  title: string;
  description: string;
  message?: string;
  evidence?: string;
  columns?: string[];
  affected_columns?: string[];
  impacted_columns?: string[];
  statistics?: Record<string, any>;
  chart_reference?: string | null;
  confidence?: string;
  methodology?: string;
  metric_value?: number | null;
  metric_label?: string | null;
  actionable_recommendation?: string | null;
  recommendation?: string | null;
}

export interface EDAReport {
  report_id: string;
  dataset_id: string;
  version_id: string;
  eda_version: string;
  generated_at: string;
  computation_time_ms: number;
  overview: EDAOverview;
  numeric_analyses: NumericColumnAnalysis[];
  categorical_analyses: CategoricalColumnAnalysis[];
  datetime_analyses: DatetimeColumnAnalysis[];
  correlation?: CorrelationMatrixResponse | null;
  numeric_relationships: NumericNumericRelationship[];
  missingness: MissingnessSummary;
  outliers: OutliersSummary;
  cardinality: CardinalitySummary;
  findings: EDAFinding[];
  charts: ChartSpec[];
}

export interface RelationshipQueryRequest {
  column_x: string;
  column_y: string;
}

export interface RelationshipQueryResponse {
  relationship_type: "numeric_numeric" | "numeric_categorical" | "categorical_categorical" | "unsupported";
  column_x: string;
  column_y: string;
  numeric_numeric?: NumericNumericRelationship | null;
  numeric_categorical?: NumericCategoricalRelationship | null;
  categorical_categorical?: CategoricalCategoricalRelationship | null;
  chart?: ChartSpec | null;
}

// Aliases for component convenience and backwards compatibility
export type EDAResponse = EDAReport;
export type UnivariateNumeric = NumericColumnAnalysis;
export type UnivariateCategorical = CategoricalColumnAnalysis;
export type DatetimeAnalysis = DatetimeColumnAnalysis;
export type CorrelationMatrix = CorrelationMatrixResponse;

// ============================================================
// Phase 8: SQL Studio & Analytics Engine Types
// ============================================================

export interface SQLColumnDescriptor {
  name: string;
  physical_type: string;
  semantic_type: string;
  nullable: boolean;
}

export interface SQLQueryRequest {
  dataset_id: string;
  version_id?: string | null;
  sql: string;
  max_rows?: number;
  timeout_seconds?: number;
  use_cache?: boolean;
}

export interface SQLQueryResponse {
  query_id: string;
  dataset_id: string;
  version_id: string;
  status: "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED" | "CANCELLED" | "TIMEOUT";
  columns: SQLColumnDescriptor[];
  rows: Record<string, any>[];
  row_count: number;
  total_rows_estimate?: number | null;
  scanned_rows?: number | null;
  execution_time_ms: number;
  is_truncated: boolean;
  query_hash: string;
  cached: boolean;
  error_message?: string | null;
  suggested_charts: ChartSpec[];
}

export interface SQLValidationError {
  message: string;
  line?: number | null;
  column?: number | null;
  error_code: string;
}

export interface SQLValidationWarning {
  message: string;
  warning_code: string;
  suggestion?: string | null;
}

export interface SQLValidationResult {
  is_valid: boolean;
  statement_type: "SELECT" | "EXPLAIN" | "WITH" | "UNKNOWN";
  tables: string[];
  columns: string[];
  errors: SQLValidationError[];
  warnings: SQLValidationWarning[];
  suggestions: string[];
}

export interface SQLExplainResult {
  query_id: string;
  dataset_id: string;
  version_id: string;
  plan_text: string;
  plan_tree?: Record<string, any> | null;
  estimated_cardinality?: number | null;
  execution_time_ms: number;
}

export interface QueryHistoryItem {
  query_id: string;
  dataset_id: string;
  version_id: string;
  query_text: string;
  query_hash: string;
  status: "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED" | "CANCELLED" | "TIMEOUT";
  execution_time_ms: number;
  row_count: number;
  error_message?: string | null;
  created_at: string;
}

export interface SavedQuery {
  id: string;
  name: string;
  description?: string | null;
  dataset_id: string;
  version_scope: string;
  sql: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface SchemaColumnInfo {
  name: string;
  physical_type: string;
  semantic_type: string;
  nullable: boolean;
  cardinality?: number | null;
  sample_values: any[];
}

export interface SchemaTableInfo {
  table_name: string;
  table_alias: string;
  dataset_id: string;
  version_id: string;
  row_count: number;
  column_count: number;
  columns: SchemaColumnInfo[];
}

export interface SQLTemplate {
  id: string;
  title: string;
  description: string;
  category: string;
  sql: string;
}

// ─────────────────────────────────────────────────────────────
// Phase 9: Visualization Engine Types
// ─────────────────────────────────────────────────────────────

export enum ChartTier {
  TIER_1_CORE = 1,
  TIER_2_ADVANCED = 2,
  TIER_3_SPECIALIZED = 3,
}

export interface ChartTypeDefinition {
  chart_type: string;
  tier: number;
  display_name: string;
  description: string;
  family: string;
  required_encodings: string[];
  optional_encodings: string[];
  supported_encodings: string[];
  supported_data_types: string[];
  supported_intents: string[];
  supports_aggregation: boolean;
  supports_temporal: boolean;
  supports_grouping: boolean;
  supports_zoom: boolean;
  supports_log_scale: boolean;
  is_supported: boolean;
  recommendation_priority: number;
}

export interface VisualizationRecommendation {
  recommendation_id?: string;
  chart_type: ChartType;
  tier?: number;
  title: string;
  reason?: string;
  rationale?: string;
  confidence?: number;
  score?: number;
  is_recommended?: boolean;
  spec: ChartSpec;
  x_field?: string | null;
  y_field?: string | null;
  series_field?: string | null;
  color_field?: string | null;
  aggregation?: string | null;
  sorting?: string | null;
  warnings?: string[];
  required_fields?: string[];
  optional_fields?: string[];
  priority?: number;
  intent?: string | null;
}

export interface SavedVisualization {
  id: string;
  visualization_id?: string;
  name: string;
  description?: string | null;
  dataset_id: string;
  dataset_version_id: string;
  chart_spec?: ChartSpec;
  spec: ChartSpec;
  source_reference?: string | null;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface VisualizationHistoryEntry {
  id: string;
  visualization_id: string;
  action: "created" | "updated" | "viewed" | "exported" | "deleted";
  dataset_id: string;
  dataset_version_id: string;
  chart_type: string;
  timestamp: string;
}

export interface ValidationErrorItem {
  code: string;
  message: string;
  field?: string | null;
  severity: string;
  suggested_fix?: string | null;
}

export interface ValidationWarningItem {
  code: string;
  message: string;
  field?: string | null;
  suggested_fix?: string | null;
}

export interface VisualizationValidationResult {
  is_valid: boolean;
  errors: (ValidationErrorItem | string)[];
  warnings: (ValidationWarningItem | string)[];
  is_compatible: boolean;
  incompatibility_reason?: string | null;
}

export interface VisualizationEvent {
  type: "select" | "hover" | "filter" | "drilldown" | "reset";
  source_chart_id: string;
  dataset_version_id: string;
  field?: string;
  value?: any;
  filters?: StructuredFilter[];
  metadata?: Record<string, any>;
}

export * from './notifications';


