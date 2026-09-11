/**
 * AnalyzaX — Phase 25: AI Copilot, Proactive Insights & Metric Governance Types.
 */

export type AggregationType = "SUM" | "AVG" | "COUNT" | "MIN" | "MAX" | "CUSTOM";
export type MetricStatus = "ACTIVE" | "DRAFT" | "DEPRECATED" | "ARCHIVED";

export interface MetricDefinition {
  metric_id: string;
  workspace_id: string;
  project_id?: string | null;
  name: string;
  description: string;
  expression: string;
  aggregation: AggregationType;
  unit?: string | null;
  dimensions: string[];
  synonyms: string[];
  owner_id: string;
  status: MetricStatus;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface MetricVersionRecord {
  version: number;
  expression: string;
  changed_by: string;
  change_summary: string;
  created_at: string;
}

export interface MetricCalculationResult {
  metric_id: string;
  metric_name: string;
  value: number;
  row_count: number;
  execution_time_ms: number;
}

export type InsightType =
  | "TREND_CHANGE"
  | "ANOMALY"
  | "SEGMENT_DIFFERENCE"
  | "CORRELATION"
  | "DATA_QUALITY"
  | "FORECAST_DEVIATION"
  | "STATISTICAL_SIGNAL"
  | "MODEL_SIGNAL"
  | "CONCENTRATION"
  | "DISTRIBUTION_SHIFT"
  | "TIME_SERIES_CHANGE";

export type InsightSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type InsightStatus = "CURRENT" | "STALE" | "DISMISSED" | "ACTIONED";

export interface InsightEvidence {
  evidence_id: string;
  evidence_type: string;
  description: string;
  metrics: Record<string, any>;
  created_at: string;
}

export interface RecommendedAction {
  action_id: string;
  title: string;
  description: string;
  action_type: string;
  tool_id: string;
  parameters: Record<string, any>;
}

export interface Insight {
  insight_id: string;
  workspace_id: string;
  project_id?: string | null;
  dataset_id: string;
  dataset_version_id: string;
  insight_type: InsightType;
  title: string;
  summary: string;
  severity: InsightSeverity;
  importance_score: number;
  affected_columns: string[];
  affected_dimensions: string[];
  evidence: InsightEvidence[];
  recommended_actions: RecommendedAction[];
  status: InsightStatus;
  created_at: string;
  updated_at: string;
}

export interface CopilotContext {
  workspace_id: string;
  project_id?: string | null;
  dataset_id?: string | null;
  dataset_version_id?: string | null;
  active_dashboard_id?: string | null;
  active_query?: string | null;
  selected_columns: string[];
  selected_metrics: string[];
  user_id?: string | null;
}

export interface NextAnalysisRecommendation {
  recommendation_id: string;
  type: string;
  title: string;
  reason: string;
  expected_value: string;
  required_inputs: string[];
  tool_plan: string[];
  risk: string;
  estimated_cost: number;
}

export interface AIWorkflowStep {
  step_id: string;
  title: string;
  tool_id: string;
  parameters: Record<string, any>;
  status: string;
  risk_level: string;
  requires_confirmation: boolean;
  result_reference?: Record<string, any> | null;
  error?: string | null;
}

export interface AIWorkflow {
  workflow_id: string;
  user_id: string;
  workspace_id: string;
  project_id?: string | null;
  goal: string;
  status: "PLANNED" | "WAITING_FOR_APPROVAL" | "RUNNING" | "PAUSED" | "COMPLETED" | "FAILED" | "CANCELLED";
  steps: AIWorkflowStep[];
  current_step_index: number;
  created_at: string;
  updated_at: string;
  approved_at?: string | null;
}

export interface DashboardPlanComponent {
  component_type: string;
  title: string;
  chart_spec?: Record<string, any> | null;
  metric_name?: string | null;
  dimensions: string[];
  layout: Record<string, any>;
}

export interface DashboardPlan {
  plan_id: string;
  title: string;
  description: string;
  dataset_id: string;
  version_id: string;
  components: DashboardPlanComponent[];
  filters: Record<string, any>[];
  requires_approval: boolean;
  created_at: string;
}

export interface AnalyticalStory {
  story_id: string;
  title: string;
  question: string;
  context: Record<string, any>;
  observations: string[];
  evidence: InsightEvidence[];
  findings: string[];
  explanations: string;
  limitations: string[];
  recommendations: string[];
  charts: Record<string, any>[];
  created_at: string;
}

export interface CopilotResponse {
  response_id: string;
  session_id: string;
  message: string;
  intent: string;
  insights: Insight[];
  visualizations: Record<string, any>[];
  recommendations: NextAnalysisRecommendation[];
  actions: Record<string, any>[];
  evidence: InsightEvidence[];
  workflow?: AIWorkflow | null;
  dashboard_plan?: DashboardPlan | null;
  analytical_story?: AnalyticalStory | null;
  provenance: Record<string, any>;
  created_at: string;
}
