/**
 * AnalyzaX — Phase 11: Machine Learning TypeScript Contracts & Domain Models.
 */

export type MLTaskType =
  | "regression"
  | "binary_classification"
  | "multiclass_classification"
  | "clustering";

export type MLJobStatus =
  | "QUEUED"
  | "RUNNING"
  | "CANCELLING"
  | "CANCELLED"
  | "COMPLETED"
  | "FAILED"
  | "TIMEOUT";

export type SuitabilitySeverity = "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface SuitabilityIssue {
  code: string;
  severity: SuitabilitySeverity;
  column?: string;
  title: string;
  message: string;
  action_recommendation?: string;
}

export interface SuitabilityReport {
  is_suitable: boolean;
  summary: string;
  issues: SuitabilityIssue[];
  dataset_row_count: number;
  dataset_col_count: number;
  recommended_task?: MLTaskType;
  recommended_target?: string;
  recommended_features: string[];
  excluded_features: Record<string, string>;
  class_distribution?: Record<string, number>;
  imbalance_ratio?: number;
}

export interface PreprocessingConfig {
  numeric_impute: "median" | "mean" | "constant";
  numeric_impute_value?: number;
  numeric_scale: "standard" | "minmax" | "robust" | "passthrough";
  categorical_impute: "most_frequent" | "constant";
  categorical_impute_value?: string;
  categorical_encode: "one_hot" | "ordinal";
  extract_date_features: boolean;
  date_features: string[];
}

export interface SplitConfig {
  train_size: number;
  val_size: number;
  test_size: number;
  random_seed: number;
  stratify: boolean;
}

export interface SplitSummary {
  train_rows: number;
  val_rows: number;
  test_rows: number;
  total_rows: number;
  stratified: boolean;
}

export interface CrossValidationConfig {
  enabled: boolean;
  n_splits: number;
  shuffle: boolean;
  random_seed: number;
  stratified: boolean;
}

export interface HyperparameterDefinition {
  name: string;
  display_name: string;
  param_type: "int" | "float" | "string" | "bool" | "choice";
  default: any;
  min_val?: number;
  max_val?: number;
  allowed_values?: any[];
  description: string;
}

export interface MLModelDefinition {
  model_id: string;
  display_name: string;
  description: string;
  task_types: MLTaskType[];
  default_parameters: Record<string, any>;
  parameter_schema: HyperparameterDefinition[];
  supports_probability: boolean;
  supports_feature_importance: boolean;
  supports_coefficients: boolean;
  resource_class: string;
  recommendation_priority: number;
}

export interface HyperparameterSearchConfig {
  enabled: boolean;
  search_method: "grid" | "random";
  param_grid: Record<string, any[]>;
  n_iter: number;
  scoring?: string;
}

export interface FeatureImportanceItem {
  feature: string;
  source_column: string;
  importance: number;
  coefficient?: number;
}

export interface ConfusionMatrixData {
  labels: string[];
  matrix: number[][];
  normalized_matrix: number[][];
  per_class_metrics: Record<string, { precision: number; recall: number; f1: number; support: number }>;
}

export interface ResidualDiagnostics {
  actual_vs_predicted: Array<{ actual: number; predicted: number; residual: number }>;
  residuals: number[];
  mean_residual: number;
  std_residual: number;
  residual_skew: number;
  largest_errors: Array<{ row_index: number; actual: number; predicted: number; error: number }>;
}

export interface CurveData {
  class_label: string;
  auc?: number;
  points: Array<Record<string, number>>;
}

export interface ClusterSummaryItem {
  cluster_id: number;
  size: number;
  percentage: number;
  center: Record<string, number>;
}

export interface MLFinding {
  finding_id: string;
  experiment_id: string;
  category: string;
  severity: string;
  title: string;
  description: string;
  evidence?: string;
  metrics: Record<string, any>;
  related_columns: string[];
  related_model?: string;
  confidence: number;
  methodology: string;
  limitations: string[];
}

export interface MLModelRun {
  model_run_id: string;
  model_id: string;
  model_name: string;
  task_type: MLTaskType;
  parameters: Record<string, any>;
  status: MLJobStatus;
  duration_ms: number;
  sample_counts: Record<string, number>;
  metrics: Record<string, any>;
  cv_metrics?: {
    metric: string;
    folds: number;
    mean: number;
    std: number;
    scores: number[];
  };
  test_metrics?: Record<string, any>;
  baseline_comparison?: {
    baseline_model: string;
    metric: string;
    baseline_value: number;
    model_value: number;
    delta: number;
    outperforms_baseline: boolean;
  };
  feature_importance: FeatureImportanceItem[];
  confusion_matrix?: ConfusionMatrixData;
  residual_diagnostics?: ResidualDiagnostics;
  roc_curves?: CurveData[];
  pr_curves?: CurveData[];
  cluster_summaries?: ClusterSummaryItem[];
  artifact_reference?: string;
  warnings: string[];
}

export interface MLExperimentRequest {
  dataset_id: string;
  dataset_version_id: string;
  task_type: MLTaskType;
  target_column?: string;
  feature_columns: string[];
  preprocessing?: PreprocessingConfig;
  split?: SplitConfig;
  cross_validation?: CrossValidationConfig;
  models: string[];
  model_parameters?: Record<string, Record<string, any>>;
  hyperparameter_search?: HyperparameterSearchConfig;
  primary_metric?: string;
  random_seed?: number;
  mode?: "beginner" | "advanced";
}

export interface MLExperiment {
  experiment_id: string;
  dataset_id: string;
  dataset_version_id: string;
  task_type: MLTaskType;
  target_column?: string;
  feature_columns: string[];
  models: string[];
  primary_metric: string;
  random_seed: number;
  status: MLJobStatus;
  created_at: string;
  completed_at?: string;
  duration_ms?: number;
  config_hash: string;
  error_message?: string;
}

export interface MLResult {
  result_id: string;
  experiment_id: string;
  dataset_id: string;
  dataset_version_id: string;
  task_type: MLTaskType;
  status: MLJobStatus;
  target?: string;
  features: string[];
  sample_summary: SplitSummary;
  preprocessing_steps: Array<{
    step_id: string;
    operation: string;
    input_columns: string[];
    output_columns: string[];
    parameters: Record<string, any>;
  }>;
  model_runs: MLModelRun[];
  best_model_run_id?: string;
  primary_metric: string;
  findings: MLFinding[];
  visualizations: any[];
  warnings: string[];
  limitations: string[];
  provenance: Record<string, any>;
  created_at: string;
}

export interface PredictionRequest {
  rows?: Array<Record<string, any>>;
  dataset_id?: string;
  dataset_version_id?: string;
}

export interface PredictionResult {
  prediction_id: string;
  model_run_id: string;
  dataset_id?: string;
  dataset_version_id?: string;
  row_count: number;
  task_type: MLTaskType;
  predictions: Array<number | string>;
  probabilities?: Array<Record<string, number>>;
  columns: string[];
  status: string;
  created_at: string;
  provenance: Record<string, any>;
}
