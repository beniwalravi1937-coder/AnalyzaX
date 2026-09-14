/**
 * Types for Phase 21: Advanced Billing, Subscriptions, Payments & Revenue Management.
 */

export type SubscriptionStatus =
  | 'trialing'
  | 'active'
  | 'past_due'
  | 'unpaid'
  | 'canceled'
  | 'incomplete'
  | 'incomplete_expired'
  | 'paused';

export type BillingInterval = 'month' | 'year';

export type InvoiceStatus = 'draft' | 'open' | 'paid' | 'void' | 'uncollectible';

export type PaymentStatus = 'pending' | 'succeeded' | 'failed' | 'refunded';

export interface BillingCustomer {
  billing_customer_id: string;
  workspace_id: string;
  provider: string;
  external_customer_id: string;
  email: string;
  name?: string | null;
  status: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface BillingPrice {
  billing_price_id: string;
  plan_code: string;
  provider: string;
  external_price_id: string;
  currency: string;
  amount_minor_units: number;
  interval: BillingInterval;
  interval_count: number;
  active: boolean;
  amount_display: string;
  metadata?: {
    display_name?: string;
    savings_percent?: number;
    [key: string]: any;
  };
  created_at: string;
  updated_at: string;
}

export interface Subscription {
  subscription_id: string;
  workspace_id: string;
  billing_customer_id: string;
  provider: string;
  external_subscription_id: string;
  plan_code: string;
  billing_price_id: string;
  status: SubscriptionStatus;
  currency: string;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  canceled_at?: string | null;
  trial_start?: string | null;
  trial_end?: string | null;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Invoice {
  invoice_id: string;
  workspace_id: string;
  billing_customer_id: string;
  provider: string;
  external_invoice_id: string;
  external_subscription_id?: string | null;
  status: InvoiceStatus;
  currency: string;
  subtotal_minor: number;
  tax_minor?: number | null;
  total_minor: number;
  amount_paid_minor: number;
  amount_due_minor: number;
  period_start: string;
  period_end: string;
  hosted_invoice_url?: string | null;
  invoice_pdf_url?: string | null;
  total_display: string;
  created_at: string;
  updated_at: string;
}

export interface Payment {
  payment_id: string;
  workspace_id: string;
  billing_customer_id: string;
  invoice_id?: string | null;
  provider: string;
  external_payment_id: string;
  amount_minor_units: number;
  currency: string;
  status: PaymentStatus;
  amount_display: string;
  created_at: string;
}

export interface BillingOverviewResponse {
  workspace_id: string;
  plan_code: string;
  customer?: BillingCustomer | null;
  subscription?: Subscription | null;
  prices: BillingPrice[];
  recent_invoices: Invoice[];
  can_manage_billing: boolean;
  is_grace_period: boolean;
  downgrade_warning?: string | null;
}

export interface CheckoutSessionRequest {
  plan_code: string;
  interval?: BillingInterval;
  success_url?: string;
  cancel_url?: string;
}

export interface CheckoutSessionResponse {
  session_id: string;
  checkout_url: string;
  expires_at: string;
  plan_code: string;
  interval: string;
  amount_minor_units: number;
  currency: string;
  provider: string;
}

export interface PortalSessionResponse {
  portal_url: string;
  expires_at: string;
}

export interface InvoiceListResponse {
  invoices: Invoice[];
  total: number;
  has_more: boolean;
}

export interface BillingConfig {
  enabled: boolean;
  provider: string;
  currency: string;
  portal_supported: boolean;
  grace_period_days: number;
}

export interface BillingReconciliationReport {
  workspace_id?: string | null;
  audited_at: string;
  total_subscriptions_audited: number;
  mismatches_found: number;
  discrepancies: Array<Record<string, any>>;
  is_healthy: boolean;
}
