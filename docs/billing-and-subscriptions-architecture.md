# AnalyzaX — Billing, Subscriptions, Payments & Revenue Management Architecture (Phase 21)

This document defines the architectural specification, data model, lifecycle state machines, security constraints, and provider abstractions for **Phase 21: Advanced Billing, Subscriptions, Payments & Revenue Management**.

---

## 1. Executive Summary & Design Principles

The Billing System bridges external payment processing networks (Stripe, LemonSqueezy, mock sandbox) with the AnalyzaX Usage, Quotas, and Entitlements Engine (Phase 20). It guarantees:

1. **Exact Integer Minor-Unit Arithmetic:** All monetary prices, invoice amounts, taxes, and payments are strictly tracked in integer minor units (e.g. cents: `$29.00` = `2900`). Floating-point currency calculations are forbidden.
2. **Authoritative External Sync with Internal Entitlement Drive:** The payment provider is the source of truth for payment collection, but the internal `WorkspacePlan` drives access instantaneously upon webhook receipt.
3. **Downgrade Safety:** Downgrading or canceling a plan *never silently deletes* datasets, historical lineage, ML models, or dashboards. Excess assets enter an over-limit, read-only state.
4. **Idempotent Webhook Intake:** Every webhook event is deduplicated via an O(1) hash and external event ID check. Duplicate webhook deliveries are acknowledged with `200 OK` without triggering side-effects.
5. **Cryptographic Webhook Signatures:** Raw request body bytes and signature headers are verified via HMAC-SHA256 with replay-attack protection (5-minute timestamp tolerance).
6. **Zero Sensitive Data Storage:** Raw card numbers, CVVs, and banking secrets are never stored, logged, or processed by AnalyzaX backend or frontend. Customer checkout and payment updates are handled via hosted payment sessions and Customer Portals.

---

## 2. Architectural Flow & Pipeline

```
[User / Admin] 
      │ Selects Plan & Interval (Monthly / Annual)
      ▼
[Billing REST API] (/api/v1/billing/checkout)
      │ Enforces BILLING_CHECKOUT permission & verifies catalog price
      ▼
[Billing Checkout Service]
      │ Resolves or provisions BillingCustomer (1:1 with Workspace)
      ▼
[Payment Provider] (Sandbox / Stripe)
      │ Generates signed hosted Checkout Session URL (cs_xxx)
      ▼
[User Completes Payment on Provider]
      │
      ▼
[Provider Webhook Delivery] (POST /api/v1/billing/webhooks/{provider})
      │ 1. Verifies HMAC-SHA256 signature
      │ 2. Deduplicates event ID (idempotency check)
      │ 3. Records event receipt
      ▼
[Billing Webhook Service]
      │ Normalizes to NormalizedWebhookEvent
      ▼
[Billing Sync Service]
      │ Synchronizes Subscription, Invoice, and Payment
      ▼
[Usage Plan Service] (Phase 20)
      │ Updates WorkspacePlan (e.g. FREE -> PRO)
      ▼
[Quota & Entitlement Engine]
      │ Immediately expands storage limits, project allowances, & quotas
      ▼
[Notifications & Activity]
        Dispatches in-app notification & audit log
```

---

## 3. Data Models & Entities

### 3.1 BillingCustomer
- `billing_customer_id`: Internal unique ID (`bcust_...`).
- `workspace_id`: Foreign key to `Workspace` (Strict 1:1 invariant).
- `provider`: Provider identifier (`sandbox`, `stripe`).
- `external_customer_id`: Provider customer ID (`cus_...`).
- `email`: Customer billing contact email.

### 3.2 BillingPrice
- `billing_price_id`: Canonical internal price ID (`bprice_pro_monthly`).
- `plan_code`: Target product tier (`PRO`, `TEAM`, `ENTERPRISE`).
- `currency`: ISO-4217 currency (`USD`).
- `amount_minor_units`: Exact integer minor units (`2900` = $29.00).
- `interval`: `month` or `year`.
- `active`: Boolean flag.

### 3.3 Subscription
- `subscription_id`: Internal ID (`sub_...`).
- `workspace_id`: Workspace association.
- `external_subscription_id`: Provider subscription ID.
- `plan_code`: Active plan tier (`FREE`, `PRO`, `TEAM`, `ENTERPRISE`).
- `status`: `TRIALING`, `ACTIVE`, `PAST_DUE`, `UNPAID`, `CANCELED`, `PAUSED`.
- `current_period_start`: ISO-8601 start date.
- `current_period_end`: ISO-8601 renewal/expiration date.
- `cancel_at_period_end`: Boolean (graceful period-end termination).

### 3.4 Invoice & Payment
- `invoice_id`: Internal invoice tracking ID.
- `subtotal_minor`, `tax_minor`, `total_minor`, `amount_paid_minor`: Exact integer minor units.
- `status`: `DRAFT`, `OPEN`, `PAID`, `VOID`, `UNCOLLECTIBLE`.
- `hosted_invoice_url`, `invoice_pdf_url`: Hosted provider links.

---

## 4. Webhook Security & Idempotency Specification

### Signature Verification Algorithm
```python
expected_sig = hmac.new(
    webhook_secret.encode("utf-8"),
    f"{timestamp}.{raw_body}".encode("utf-8"),
    hashlib.sha256
).hexdigest()
```
- Rejects requests if `abs(current_time - timestamp) > 300` seconds.
- Rejects requests where constant-time HMAC comparison fails.

### Idempotency Matrix
| Inbound Delivery | Prior Status | Action Taken | HTTP Response |
| :--- | :--- | :--- | :--- |
| First Delivery | None | Records receipt, parses, applies state transition, marks `PROCESSED` | `200 OK {"status": "processed"}` |
| Duplicate Delivery | `PROCESSED` | Increments attempt count, skips state transitions | `200 OK {"status": "duplicate_ignored"}` |
| Re-delivery on Error | `FAILED` | Retries transition logic | `200 OK` on success, `400/500` on failure |

---

## 5. Subscription Lifecycle State Machine

```
   [Checkout]
       │
       ▼
   (ACTIVE) ───[Period-End Cancel]───► (ACTIVE: cancel_at_period_end=True)
       │                                     │                │
   [Payment Failed]                     [Resume]       [Period Expires]
       ▼                                     │                ▼
   (PAST_DUE) ◄──────────────────────────────┘           (CANCELED)
       │                                                      │
   [Grace Period Expired]                                     ▼
       ▼                                               [Downgrade to FREE]
   (UNPAID) ─────────────────────────────────────────► (Datasets Preserved)
```

---

## 6. Verification & Automated Quality Gates

Phase 21 is covered by 5 automated test suites:
1. `backend/tests/test_billing_domain.py`: Minor units arithmetic, price validation, subscription properties.
2. `backend/tests/test_billing_provider.py`: Sandbox provider checkout, portal, webhook HMAC signing/verification.
3. `backend/tests/test_billing_service.py`: Customer mapping, checkout safety, entitlement sync, downgrade safety.
4. `backend/tests/test_billing_webhooks.py`: Signature verification, replay defense, idempotency deduplication.
5. `backend/tests/test_billing_api.py`: Full golden path, overview, checkout, sandbox completion, invoices, cancel, resume, and ledger reconciliation.
