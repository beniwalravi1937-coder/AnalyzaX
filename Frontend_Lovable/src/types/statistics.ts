export type AnalysisStatus =
  | "QUEUED"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED"
  | "WARNING"
  | "INSUFFICIENT_DATA"
  | "NUMERICAL_FAILURE";

export type MissingDataPolicy = "LISTWISE" | "PAIRWISE" | "METHOD_DEFAULT";

export interface StatisticValue {
  name: string;
  value: number;
  unit?: string | null;
  description?: string | null;
}

export interface PValue {
  value: number;
  formatted: string;
  comparison?: string;
  adjusted?: boolean;
  adjustment_method?: string | null;
}

export interface Diagnostic {
  diagnostic_type: string;
  status: string;
  metric: string;
  value: number;
  threshold?: number | null;
  evidence: string;
  description: string;
}

export interface StatisticalWarning {
  code: string;
  severity: string;
  message: string;
}

export interface StatisticalLimitation {
  code: string;
  message: string;
}

export interface MissingDataReport {
  original_observations: number;
  used_observations: number;
  excluded_observations: number;
  missing_policy: string;
  exclusion_reason?: string | null;
}

export interface ConfidenceInterval {
  level: number;
  lower: number;
  upper: number;
  metric_name: string;
  standard_error?: number | null;
  margin_of_error?: number | null;
  estimate?: number | null;
  parameter?: string | null;
  method?: string | null;
}

export interface EffectSize {
  metric_name: string;
  value: number;
  interpretation: string; // "negligible" | "small" | "medium" | "large"
  confidence_interval?: ConfidenceInterval | null;
}

export interface AssumptionCheck {
  check_id: string;
  assumption: string;
  status: "NOT_CHECKED" | "PASS" | "WARNING" | "VIOLATION" | "NOT_APPLICABLE" | "INSUFFICIENT_DATA";
  severity: "info" | "low" | "medium" | "high" | "critical";
  method: string;
  statistic?: number | null;
  p_value?: number | null;
  evidence: string;
  description: string;
  recommendation?: string | null;
}

export interface StatisticalFinding {
  finding_id: string;
  category: string;
  severity: "info" | "low" | "medium" | "high" | "critical";
  title: string;
  description: string;
  columns: string[];
  method: string;
  statistics?: Record<string, unknown>;
  effect_size?: Record<string, unknown> | null;
  confidence_interval?: Record<string, unknown> | null;
  p_value?: number | null;
  adjusted_p_value?: number | null;
  evidence: string;
  confidence: number;
  limitations: string[];
}

export interface StatisticalAnalysisRequest {
  analysis_id?: string;
  dataset_id: string;
  dataset_version_id: string;
  analysis_type: string;
  method: string;
  target_columns: string[];
  group_columns?: string[];
  inputs?: {
    outcome_columns?: string[];
    predictor_columns?: string[];
    group_column?: string;
    paired_columns?: string[];
    categorical_columns?: string[];
    numeric_columns?: string[];
    weight_column?: string;
  };
  parameters?: Record<string, unknown>;
  missing_data_policy?: MissingDataPolicy | string;
  multiple_testing?: {
    method: "NONE" | "BONFERRONI" | "HOLM" | "BENJAMINI_HOCHBERG" | string;
    comparison_count?: number;
  };
  options?: Record<string, unknown>;
}

export interface StatisticalAnalysisResponse {
  analysis_id: string;
  status: AnalysisStatus | string;
  result_id?: string;
  dataset_id?: string;
  dataset_version_id?: string;
}

export interface VisualizationItem {
  visualization_id: string;
  chart_spec: Record<string, unknown>;
}

export interface StatisticalProvenance {
  statistics_engine_version?: string;
  engine_version?: string;
  dataset_id?: string;
  dataset_version_id?: string;
  analysis_type?: string;
  method?: string;
  target_columns?: string[];
  group_columns?: string[];
  timestamp?: string;
  deterministic_libraries?: string[];
  software_versions?: Record<string, string>;
  [key: string]: unknown;
}

export interface StatisticalResult {
  schema_version?: string;
  result_id: string;
  analysis_id?: string;
  dataset_id: string;
  dataset_version_id: string;
  analysis_type: string;
  method: string;
  status: AnalysisStatus | string;
  inputs: {
    target_columns: string[];
    group_columns?: string[];
    outcome_columns?: string[];
    predictor_columns?: string[];
    group_column?: string;
    paired_columns?: string[];
    categorical_columns?: string[];
    numeric_columns?: string[];
    weight_column?: string;
  };
  parameters: Record<string, unknown>;
  missing_data_report: MissingDataReport;
  sample?: {
    available_rows: number;
    analyzed_rows: number;
    excluded_rows: number;
    missing_rows: number;
    groups?: Record<string, number>;
  };
  statistics: Record<string, any>;
  p_values: Record<string, number | null>;
  effect_sizes: EffectSize[];
  confidence_intervals: ConfidenceInterval[];
  assumptions: AssumptionCheck[];
  diagnostics: Record<string, any>;
  interpretation: {
    what_was_tested?: string;
    method_used?: string;
    observed_summary?: string;
    evidence_strength?: string;
    effect_magnitude?: string;
    assumptions_impact?: string;
    causality_caveat?: string;
    limitations?: string[];
  };
  findings: StatisticalFinding[];
  warnings: string[];
  limitations: string[];
  provenance: StatisticalProvenance;
  chart_specs: Record<string, any>[];
  visualizations?: VisualizationItem[];
  created_at: string;
}

export interface MethodCatalogItem {
  method: string;
  name: string;
  category: string;
  description: string;
  required_inputs: Record<string, string>;
  supported_data_types: string[];
  assumptions: string[];
  supports_effect_size: boolean;
  supports_confidence_interval: boolean;
  supports_visualization: boolean;
}

export interface MethodRecommendation {
  recommended_method: string;
  recommended_name: string;
  alternative_methods: string[];
  rationale: string[];
  required_assumptions: string[];
  warnings: string[];
}

export interface ValidationResponse {
  is_valid: boolean;
  issues: string[];
  warnings: string[];
  missing_data_report?: MissingDataReport | null;
}
