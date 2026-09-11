/**
 * AnalyzaX — Phase 13: AI Analyst Domain Contracts
 * Fully typed synchronized TypeScript definitions for natural-language analytics.
 */

export type AnalystIntent =
  | "DATASET_OVERVIEW"
  | "DATA_QUALITY"
  | "DESCRIPTIVE_ANALYSIS"
  | "DISTRIBUTION"
  | "COMPARISON"
  | "RANKING"
  | "TREND"
  | "CORRELATION"
  | "RELATIONSHIP"
  | "GROUP_ANALYSIS"
  | "STATISTICAL_TEST"
  | "REGRESSION"
  | "MACHINE_LEARNING"
  | "FORECASTING"
  | "ANOMALY_EXPLORATION"
  | "VISUALIZATION"
  | "SQL_ANALYSIS"
  | "EXPLANATION"
  | "FOLLOW_UP"
  | "MODEL_COMPARISON"
  | "FORECAST_COMPARISON"
  | "DATA_CLEANING_REQUEST"
  | "UNSUPPORTED_REQUEST";

export type ToolPermission =
  | "READ_ONLY"
  | "DERIVED_RESULT"
  | "PROPOSAL_ONLY"
  | "USER_CONFIRMATION_REQUIRED";

export interface ToolDefinition {
  tool_id: string;
  display_name: string;
  description: string;
  purpose: string;
  input_schema: Record<string, any>;
  output_schema: Record<string, any>;
  required_context: string[];
  permission: ToolPermission;
  timeout_seconds: number;
  supports_async: boolean;
  deterministic: boolean;
  side_effect_level: string;
}

export interface AnalysisStep {
  step_id: string;
  description: string;
  tool_id: string;
  parameters: Record<string, any>;
  depends_on: string[];
  status: "pending" | "running" | "completed" | "failed" | "skipped";
}

export interface AnalysisPlan {
  plan_id: string;
  user_question: string;
  intent: AnalystIntent;
  steps: AnalysisStep[];
  required_tools: string[];
  assumptions: string[];
  expected_outputs: string[];
  status: "created" | "in_progress" | "completed" | "partial_failure" | "failed";
}

export interface ToolCall {
  call_id: string;
  tool_id: string;
  arguments: Record<string, any>;
  reasoning_summary?: string;
  requested_by: string;
  created_at: string;
}

export interface ToolResult {
  call_id: string;
  tool_id: string;
  status: "completed" | "failed" | "rejected";
  result?: Record<string, any>;
  metadata: Record<string, any>;
  warnings: string[];
  errors: string[];
  provenance: Record<string, any>;
  execution_time_ms: number;
}

export interface AnalysisReference {
  reference_id: string;
  tool_id: string;
  result_id?: string;
  dataset_id: string;
  dataset_version_id: string;
  relevant_fields: string[];
  summary?: string;
  created_at: string;
}

export interface CleaningProposal {
  proposal_id: string;
  dataset_id: string;
  dataset_version_id: string;
  operation_type: string;
  parameters: Record<string, any>;
  rationale: string;
  impact_summary: string;
  requires_confirmation: boolean;
  status: "proposed" | "approved" | "rejected" | "applied";
}

export interface AnalystMessage {
  message_id: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  intent?: AnalystIntent;
  plan?: AnalysisPlan;
  tool_calls: ToolCall[];
  tool_results: ToolResult[];
  visualizations: Record<string, any>[];
  citations: AnalysisReference[];
  cleaning_proposal?: CleaningProposal;
  warnings: string[];
  limitations: string[];
  follow_up_questions: string[];
  provenance: Record<string, any>;
  created_at: string;
}

export interface AnalystSession {
  session_id: string;
  title: string;
  dataset_id?: string;
  dataset_version_id?: string;
  messages: AnalystMessage[];
  active_columns: string[];
  recent_result_references: AnalysisReference[];
  context_summary?: string;
  created_at: string;
  updated_at: string;
}

export interface AnalystChatRequest {
  session_id?: string;
  dataset_id?: string;
  dataset_version_id?: string;
  message: string;
  options?: Record<string, any>;
}

export interface AnalystChatResponse {
  response_id: string;
  session_id: string;
  status: "completed" | "clarification_needed" | "failed" | "rejected";
  message: string;
  intent: AnalystIntent;
  plan?: AnalysisPlan;
  tool_calls: ToolCall[];
  tool_results: ToolResult[];
  visualizations: Record<string, any>[];
  citations: AnalysisReference[];
  cleaning_proposal?: CleaningProposal;
  warnings: string[];
  limitations: string[];
  follow_up_questions: string[];
  provenance: Record<string, any>;
  created_at: string;
}
