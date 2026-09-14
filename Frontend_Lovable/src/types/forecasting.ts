/**
 * AnalyzaX — Phase 12: Forecasting TypeScript Domain Types.
 * Matches backend Pydantic schemas for temporal validation, frequency detection,
 * model backtesting, metrics, prediction intervals, diagnostics, and ChartSpecs.
 */

import { ChartSpec } from "@/types";

export type ForecastFrequency =
  | "MINUTELY"
  | "HOURLY"
  | "DAILY"
  | "BUSINESS_DAY"
  | "WEEKLY"
  | "MONTHLY"
  | "QUARTERLY"
  | "YEARLY"
  | "CUSTOM";

export type RegularityStatus =
  | "REGULAR"
  | "MOSTLY_REGULAR"
  | "IRREGULAR"
  | "INSUFFICIENT_DATA";

export type QualitySeverity = "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface ForecastQualityIssue {
  issue_id: string;
  issue_type: string;
  severity: QualitySeverity;
  description: string;
  affected_rows: number;
  time_range?: string;
  evidence?: Record<string, any>;
  recommendation?: string;
}

export interface TemporalValidationReport {
  is_valid: boolean;
  time_column: string;
  target_column: string;
  inferred_frequency: ForecastFrequency;
  pandas_frequency_str: string;
  regularity: RegularityStatus;
  confidence: number;
  observation_count: number;
  expected_observation_count: number;
  missing_timestamp_count: number;
  duplicate_timestamp_count: number;
  min_timestamp: string;
  max_timestamp: string;
  target_missing_count: number;
  target_zero_count: number;
  target_mean: number;
  target_variance: number;
  issues: ForecastQualityIssue[];
  warnings: string[];
}

export type TrendDirection = "UPWARD" | "DOWNWARD" | "FLAT";

export interface TrendFinding {
  detected: boolean;
  direction: TrendDirection;
  slope: number;
  p_value: number;
  r_squared: number;
  description: string;
}

export interface SeasonalityFinding {
  detected: boolean;
  candidate_period?: number;
  frequency_label?: string;
  seasonal_strength: number;
  confidence: number;
  evidence?: Record<string, any>;
  description: string;
}

export interface ACFResult {
  lags: number[];
  acf_values: number[];
  pacf_values: number[];
  confidence_bound: number;
}

export interface DecompositionResult {
  method: string;
  period: number;
  timestamps: string[];
  observed: number[];
  trend: (number | null)[];
  seasonal: (number | null)[];
  residual: (number | null)[];
}

export interface TemporalAnalysisSummary {
  trend: TrendFinding;
  seasonality: SeasonalityFinding;
  acf?: ACFResult;
  decomposition?: DecompositionResult;
  anomalies_detected: number;
}

export interface ForecastPoint {
  timestamp: string;
  value: number;
  lower_bound?: number;
  upper_bound?: number;
  horizon_step: number;
}

export interface ForecastMetrics {
  mae: number;
  mse: number;
  rmse: number;
  mase?: number;
  smape: number;
  wape: number;
  mape?: number;
}

export interface BacktestFoldResult {
  fold_index: number;
  train_end: string;
  test_start: string;
  test_end: string;
  actuals: number[];
  predictions: number[];
  metrics: ForecastMetrics;
}

export interface BacktestResult {
  folds: BacktestFoldResult[];
  mean_metrics: ForecastMetrics;
  std_metrics?: Record<string, number>;
}

export interface ResidualDiagnostics {
  mean: number;
  std: number;
  ljung_box_stat?: number;
  ljung_box_pvalue?: number;
  normality_stat?: number;
  normality_pvalue?: number;
  autocorrelation_detected: boolean;
  residuals: number[];
  residual_timestamps: string[];
}

export interface ForecastModelDefinition {
  model_id: string;
  display_name: string;
  description: string;
  supports_seasonality: boolean;
  supports_trend: boolean;
  supports_prediction_intervals: boolean;
  default_parameters: Record<string, any>;
  parameter_schema: Record<string, any>;
  recommendation_priority: number;
}

export type ForecastJobStatus =
  | "QUEUED"
  | "RUNNING"
  | "CANCELLING"
  | "CANCELLED"
  | "COMPLETED"
  | "FAILED"
  | "TIMEOUT";

export interface ForecastModelRun {
  run_id: string;
  model_id: string;
  model_name: string;
  parameters: Record<string, any>;
  training_status: string;
  training_duration_ms: number;
  sample_count: number;
  backtest_result: BacktestResult;
  future_forecasts: ForecastPoint[];
  residual_diagnostics?: ResidualDiagnostics;
  artifact_reference?: string;
  warnings: string[];
}

export type FindingCategory =
  | "DATA_QUALITY"
  | "TREND"
  | "SEASONALITY"
  | "AUTOCORRELATION"
  | "MODEL_PERFORMANCE"
  | "MODEL_DIAGNOSTICS"
  | "FORECAST_UNCERTAINTY"
  | "ANOMALY"
  | "INSUFFICIENT_DATA"
  | "RESOURCE"
  | "MODEL_WARNING";

export interface ForecastFinding {
  finding_id: string;
  category: FindingCategory;
  severity: QualitySeverity;
  title: string;
  description: string;
  evidence?: Record<string, any>;
  related_columns: string[];
  methodology?: string;
  limitations?: string;
}

export interface ForecastExperimentRequest {
  dataset_id: string;
  dataset_version_id: string;
  time_column: string;
  target_column: string;
  group_columns?: string[];
  frequency?: ForecastFrequency;
  forecast_horizon: number;
  training_window_type?: string;
  training_window_size?: number;
  validation_folds: number;
  models: string[];
  primary_metric: string;
  confidence_level: number;
  model_parameters?: Record<string, Record<string, any>>;
  options?: Record<string, any>;
}

export interface ForecastExperiment {
  experiment_id: string;
  dataset_id: string;
  dataset_version_id: string;
  time_column: string;
  target_column: string;
  frequency: ForecastFrequency;
  forecast_horizon: number;
  validation_folds: number;
  models: string[];
  primary_metric: string;
  confidence_level: number;
  status: ForecastJobStatus;
  progress_stage?: string;
  progress_percent: number;
  created_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface ForecastResult {
  result_id: string;
  experiment_id: string;
  dataset_id: string;
  dataset_version_id: string;
  time_column: string;
  target_column: string;
  frequency: ForecastFrequency;
  pandas_frequency_str: string;
  forecast_horizon: number;
  primary_metric: string;
  confidence_level: number;
  historical_timestamps: string[];
  historical_values: number[];
  models: ForecastModelRun[];
  best_model_id: string;
  validation_report: TemporalValidationReport;
  temporal_analysis: TemporalAnalysisSummary;
  findings: ForecastFinding[];
  visualizations: ChartSpec[];
  warnings: string[];
  limitations: string[];
  provenance: Record<string, any>;
  created_at: string;
}

export interface FuturePredictRequest {
  run_id?: string;
  periods: number;
  confidence_level?: number;
}

export interface FuturePredictResult {
  prediction_id: string;
  run_id: string;
  model_id: string;
  model_name: string;
  forecast_points: ForecastPoint[];
  confidence_level: number;
  created_at: string;
}
