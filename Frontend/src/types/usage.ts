/**
 * Phase 20: Advanced Usage Metering, Quotas, Entitlements & Plan Management Types
 */

export type PlanTier = "FREE" | "PRO" | "TEAM" | "ENTERPRISE";

export type PlanStatus = "ACTIVE" | "ARCHIVED" | "DEPRECATED";

export type QuotaPeriod = "MONTHLY" | "CURRENT" | "ANNUAL" | "DAILY";

export type QuotaHealthStatus = "NORMAL" | "WARNING" | "CRITICAL" | "EXCEEDED";

export interface PlanEntitlementDetail {
  entitlement_id: string;
  plan_id: string;
  feature_key: string;
  enabled: boolean;
  value: number | string | boolean | null;
  unit?: string | null;
  limit_type: string;
  period: string;
  policy: string;
}

export interface Plan {
  plan_id: string;
  plan_code: string;
  name: string;
  description: string;
  tier: PlanTier;
  version: number;
  status: PlanStatus;
  is_default: boolean;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface WorkspacePlanAssignment {
  workspace_id: string;
  workspace_plan_id: string;
  plan_id: string;
  plan_code: string;
  status: string;
  effective_from: string;
  effective_until?: string | null;
  downgrade_warning?: string | null;
  entitlements: Record<string, PlanEntitlementDetail>;
}

export interface MetricUsageDetail {
  metric_key: string;
  display_name: string;
  description: string;
  category: string;
  used: number;
  limit: number | null;
  remaining: number | null;
  percentage: number;
  unit: string;
  period: QuotaPeriod;
  status: QuotaHealthStatus;
  is_exceeded: boolean;
}

export interface FeatureEntitlementDetail {
  feature_key: string;
  display_name: string;
  category: string;
  enabled: boolean;
  limit_value: number | string | boolean | null;
  unit?: string | null;
}

export interface UsageSummaryResponse {
  workspace_id: string;
  plan: Plan;
  plan_code: string;
  period_start: string;
  period_end: string;
  days_remaining: number;
  metrics: MetricUsageDetail[];
  features: FeatureEntitlementDetail[];
  quotas: MetricUsageDetail[];
  resources: MetricUsageDetail[];
}

export interface UsageHistoryItem {
  usage_event_id: string;
  metric_key: string;
  quantity: number;
  unit: string;
  operation_type: string;
  resource_type?: string | null;
  resource_id?: string | null;
  user_id?: string | null;
  occurred_at: string;
}

export interface UsageHistoryResponse {
  workspace_id: string;
  total: number;
  next_cursor?: string | null;
  has_more: boolean;
  events: UsageHistoryItem[];
}

export interface PlanComparisonItem {
  feature_key: string;
  display_name: string;
  category: string;
  free_value: string;
  pro_value: string;
  team_value: string;
  enterprise_value: string;
}

export interface PlanComparisonResponse {
  plans: Plan[];
  comparisons: PlanComparisonItem[];
}

export interface UsageReconciliationReport {
  workspace_id: string;
  period_key: string;
  reconciled_at: string;
  metrics_audited: number;
  discrepancies_found: number;
  discrepancies: Array<Record<string, any>>;
  is_healthy: boolean;
}

export interface PlanChangeResponse {
  success: boolean;
  workspace_id: string;
  plan_code: string;
  status: string;
  downgrade_warning?: string | null;
  message: string;
}
