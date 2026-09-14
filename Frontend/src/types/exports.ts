/**
 * Phase 15: Advanced Export, Reporting & Presentation Engine
 * TypeScript type definitions synchronized with backend models.
 */

// ─────────────────────────────────────────────────────────────
// Enums
// ─────────────────────────────────────────────────────────────

export type ExportFormat = "CSV" | "JSON" | "XLSX" | "HTML_REPORT" | "MARKDOWN_REPORT";

export type ExportSourceType =
  | "DATASET"
  | "SQL_RESULT"
  | "PROFILE"
  | "QUALITY_REPORT"
  | "EDA_RESULT"
  | "VISUALIZATION_DATA"
  | "STATISTICS_RESULT"
  | "ML_RESULT"
  | "FORECAST_RESULT"
  | "DASHBOARD"
  | "AI_ANALYST_SESSION";

export type ExportStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED" | "EXPIRED";

export type ReportTemplate =
  | "EXECUTIVE_SUMMARY"
  | "DATA_QUALITY"
  | "EDA_DEEP_DIVE"
  | "ML_EXPERIMENT"
  | "FORECAST_BRIEF"
  | "FULL_ANALYSIS"
  | "CUSTOM";

export type ReportSectionType =
  | "MARKDOWN"
  | "TABLE"
  | "KPI_GRID"
  | "STATISTICS_SUMMARY"
  | "ML_METRICS"
  | "FORECAST_HORIZON"
  | "CHART_REF";

// ─────────────────────────────────────────────────────────────
// Provenance
// ─────────────────────────────────────────────────────────────

export interface ExportProvenance {
  dataset_id: string;
  dataset_version_id: string;
  source_engine?: string;
  source_result_id?: string;
  is_stale: boolean;
  stale_reason?: string;
  exported_at: string;
  platform_version: string;
}

// ─────────────────────────────────────────────────────────────
// Export Job
// ─────────────────────────────────────────────────────────────

export interface ExportJob {
  job_id: string;
  dataset_id: string;
  version_id: string;
  source_type: ExportSourceType;
  source_id?: string;
  format: ExportFormat;
  status: ExportStatus;
  file_path?: string;
  file_name?: string;
  file_size_bytes?: number;
  row_count?: number;
  content_type?: string;
  created_at: string;
  completed_at?: string;
  error_message?: string;
  provenance?: ExportProvenance;
  options: Record<string, unknown>;
}

// ─────────────────────────────────────────────────────────────
// Export Request
// ─────────────────────────────────────────────────────────────

export interface ExportRequest {
  dataset_id: string;
  version_id?: string;
  source_type: ExportSourceType;
  source_id?: string;
  format: ExportFormat;
  options?: Record<string, unknown>;
}

// ─────────────────────────────────────────────────────────────
// Report Models
// ─────────────────────────────────────────────────────────────

export interface ReportSection {
  section_id: string;
  title: string;
  content_type: ReportSectionType;
  content: Record<string, unknown>;
  order: number;
}

export interface ReportDefinition {
  report_id: string;
  dataset_id: string;
  version_id: string;
  title: string;
  subtitle?: string;
  template: ReportTemplate;
  sections: ReportSection[];
  created_at: string;
  updated_at: string;
  provenance?: ExportProvenance;
}

export interface ReportGenerateRequest {
  dataset_id: string;
  version_id?: string;
  template: ReportTemplate;
  title?: string;
  subtitle?: string;
  sections?: ReportSection[];
  format: ExportFormat;
}

export interface ReportTemplateMeta {
  template: string;
  name: string;
  description: string;
  section_count: number;
}

// ─────────────────────────────────────────────────────────────
// UI Helpers
// ─────────────────────────────────────────────────────────────

export const FORMAT_LABELS: Record<ExportFormat, string> = {
  CSV: "CSV",
  JSON: "JSON",
  XLSX: "Excel (XLSX)",
  HTML_REPORT: "HTML Report",
  MARKDOWN_REPORT: "Markdown Report",
};

export const SOURCE_TYPE_LABELS: Record<ExportSourceType, string> = {
  DATASET: "Dataset",
  SQL_RESULT: "SQL Result",
  PROFILE: "Profile",
  QUALITY_REPORT: "Quality Report",
  EDA_RESULT: "EDA Result",
  VISUALIZATION_DATA: "Visualization Data",
  STATISTICS_RESULT: "Statistics Result",
  ML_RESULT: "ML Result",
  FORECAST_RESULT: "Forecast Result",
  DASHBOARD: "Dashboard",
  AI_ANALYST_SESSION: "AI Analyst Session",
};

export const STATUS_LABELS: Record<ExportStatus, string> = {
  PENDING: "Pending",
  PROCESSING: "Processing",
  COMPLETED: "Completed",
  FAILED: "Failed",
  EXPIRED: "Expired",
};

export const TABULAR_FORMATS: ExportFormat[] = ["CSV", "JSON", "XLSX"];
export const REPORT_FORMATS: ExportFormat[] = ["HTML_REPORT", "MARKDOWN_REPORT"];
