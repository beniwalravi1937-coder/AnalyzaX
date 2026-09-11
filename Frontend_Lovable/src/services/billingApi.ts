/**
 * Phase 21: Billing, Subscriptions, Payments & Revenue Management API Client
 */

import { getAuthToken } from "./authApi";
import {
  BillingConfig,
  BillingOverviewResponse,
  BillingPrice,
  BillingReconciliationReport,
  CheckoutSessionRequest,
  CheckoutSessionResponse,
  InvoiceListResponse,
  Payment,
  PortalSessionResponse,
  Subscription,
} from "../types/billing";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

function getHeaders(workspaceId?: string): Record<string, string> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (workspaceId) {
    headers["X-Workspace-Id"] = workspaceId;
  }
  return headers;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errorJson = await res.json();
      errorDetail =
        errorJson.error?.message ||
        errorJson.detail?.message ||
        errorJson.detail ||
        errorDetail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export async function getBillingConfig(): Promise<BillingConfig> {
  const res = await fetch(`${API_BASE}/api/v1/billing/config`, {
    headers: getHeaders(),
  });
  return handleResponse<BillingConfig>(res);
}

export async function getBillingPrices(): Promise<BillingPrice[]> {
  const res = await fetch(`${API_BASE}/api/v1/billing/prices`, {
    headers: getHeaders(),
  });
  return handleResponse<BillingPrice[]>(res);
}

export async function getBillingOverview(workspaceId?: string): Promise<BillingOverviewResponse> {
  const url = new URL(`${API_BASE}/api/v1/billing/overview`);
  if (workspaceId) {
    url.searchParams.set("workspace_id", workspaceId);
  }
  const res = await fetch(url.toString(), {
    headers: getHeaders(workspaceId),
  });
  return handleResponse<BillingOverviewResponse>(res);
}

export async function createCheckoutSession(
  payload: CheckoutSessionRequest,
  workspaceId?: string
): Promise<CheckoutSessionResponse> {
  const url = new URL(`${API_BASE}/api/v1/billing/checkout`);
  if (workspaceId) {
    url.searchParams.set("workspace_id", workspaceId);
  }
  const res = await fetch(url.toString(), {
    method: "POST",
    headers: getHeaders(workspaceId),
    body: JSON.stringify(payload),
  });
  return handleResponse<CheckoutSessionResponse>(res);
}

export async function completeSandboxCheckout(
  planCode: string,
  interval: string = "month",
  workspaceId?: string
): Promise<{ status: string; message: string; subscription: Subscription }> {
  const url = new URL(`${API_BASE}/api/v1/billing/checkout/complete-sandbox`);
  if (workspaceId) {
    url.searchParams.set("workspace_id", workspaceId);
  }
  const res = await fetch(url.toString(), {
    method: "POST",
    headers: getHeaders(workspaceId),
    body: JSON.stringify({ plan_code: planCode, interval }),
  });
  return handleResponse<{ status: string; message: string; subscription: Subscription }>(res);
}

export async function changeSubscription(
  newPlanCode: string,
  newInterval?: string,
  workspaceId?: string
): Promise<Subscription> {
  const url = new URL(`${API_BASE}/api/v1/billing/subscription/change`);
  if (workspaceId) {
    url.searchParams.set("workspace_id", workspaceId);
  }
  const res = await fetch(url.toString(), {
    method: "POST",
    headers: getHeaders(workspaceId),
    body: JSON.stringify({
      new_plan_code: newPlanCode,
      new_interval: newInterval,
    }),
  });
  return handleResponse<Subscription>(res);
}

export async function cancelSubscription(
  cancelAtPeriodEnd: boolean = true,
  reason?: string,
  workspaceId?: string
): Promise<Subscription> {
  const url = new URL(`${API_BASE}/api/v1/billing/subscription/cancel`);
  if (workspaceId) {
    url.searchParams.set("workspace_id", workspaceId);
  }
  const res = await fetch(url.toString(), {
    method: "POST",
    headers: getHeaders(workspaceId),
    body: JSON.stringify({
      cancel_at_period_end: cancelAtPeriodEnd,
      reason,
    }),
  });
  return handleResponse<Subscription>(res);
}

export async function resumeSubscription(workspaceId?: string): Promise<Subscription> {
  const url = new URL(`${API_BASE}/api/v1/billing/subscription/resume`);
  if (workspaceId) {
    url.searchParams.set("workspace_id", workspaceId);
  }
  const res = await fetch(url.toString(), {
    method: "POST",
    headers: getHeaders(workspaceId),
  });
  return handleResponse<Subscription>(res);
}

export async function listInvoices(
  limit: number = 20,
  offset: number = 0,
  workspaceId?: string
): Promise<InvoiceListResponse> {
  const url = new URL(`${API_BASE}/api/v1/billing/invoices`);
  url.searchParams.set("limit", limit.toString());
  url.searchParams.set("offset", offset.toString());
  if (workspaceId) {
    url.searchParams.set("workspace_id", workspaceId);
  }
  const res = await fetch(url.toString(), {
    headers: getHeaders(workspaceId),
  });
  return handleResponse<InvoiceListResponse>(res);
}

export async function listPayments(workspaceId?: string): Promise<Payment[]> {
  const url = new URL(`${API_BASE}/api/v1/billing/payments`);
  if (workspaceId) {
    url.searchParams.set("workspace_id", workspaceId);
  }
  const res = await fetch(url.toString(), {
    headers: getHeaders(workspaceId),
  });
  return handleResponse<Payment[]>(res);
}

export async function createPortalSession(
  returnUrl?: string,
  workspaceId?: string
): Promise<PortalSessionResponse> {
  const url = new URL(`${API_BASE}/api/v1/billing/portal`);
  if (returnUrl) {
    url.searchParams.set("return_url", returnUrl);
  }
  if (workspaceId) {
    url.searchParams.set("workspace_id", workspaceId);
  }
  const res = await fetch(url.toString(), {
    method: "POST",
    headers: getHeaders(workspaceId),
  });
  return handleResponse<PortalSessionResponse>(res);
}

export async function reconcileBilling(workspaceId?: string): Promise<BillingReconciliationReport> {
  const url = new URL(`${API_BASE}/api/v1/billing/reconcile`);
  if (workspaceId) {
    url.searchParams.set("workspace_id", workspaceId);
  }
  const res = await fetch(url.toString(), {
    method: "POST",
    headers: getHeaders(workspaceId),
  });
  return handleResponse<BillingReconciliationReport>(res);
}
