# AnalyzaX — Advanced Usage Metering, Quotas, Entitlements & Plan Management Architecture

## 1. Executive Summary & Core Philosophy

**Phase 20** implements an enterprise-grade, authoritative metering and plan management engine across AnalyzaX. It establishes fine-grained governance over computational workloads, physical storage allocations, analytical queries, and collaboration seats without relying on untrusted client-side limits.

### Non-Negotiable Guarantees
1. **Server-Side Authority:** The backend is the sole source of truth for access decisions. Frontend UI gates are purely assistive presentations.
2. **Immutable Plan Catalog & Fine-Grained Entitlements:** Four standardized tiers (`FREE`, `PRO`, `TEAM`, `ENTERPRISE`) define explicit quota boundaries across datasets, storage, ML, forecasting, SQL, AI assistance, exports, projects, and workspace seats.
3. **Structured 429 Quota Enforcement:** Over-limit requests fail explicitly with structured `QuotaExceededException` (HTTP 429) containing detailed telemetry (current consumption, requested amount, limit, remaining balance, reset timestamp, and plan upgrade hints).
4. **Append-Only Idempotent Ledger:** Every metered event is recorded into an append-only transaction ledger with deduplication via `idempotency_key`, preventing double-charging on network retries.
5. **Two-Phase Reservation Lifecycle:** Asynchronous and multi-step jobs (e.g. Model Training, AutoML, Forecasting) utilize an atomic `reserve_quota` → `finalize_quota` (or `release_quota` on failure) pattern to guarantee concurrency safety under high contention.
6. **Downgrade Safety Guarantee:** A plan downgrade or quota exhaustion **never silently deletes datasets, versions, models, or lineage**. Excess resources transition into a protected, read-only state.
7. **Periodic Reconciliation:** An automated auditing engine verifies rolled-up balance caches against raw append-only event logs to detect and rectify anomalies.

---

## 2. Authority & Evaluation Pipeline

The lifecycle of every resource request traverses this deterministic pipeline:

```
[Incoming Request] (e.g., Run Forecast, Query SQL, Upload Dataset, AI Chat)
         │
         ▼
[Application Service] (e.g. ForecastingService, AiAnalystService)
         │
         ├──► 1. Check Feature Entitlement (Is FORECASTING enabled on Workspace's Plan?)
         │        └─ If False ──► Raise QuotaExceededException(429)
         │
         ├──► 2. Check Quota / Reserve (Current Consumed + Active Reservations + Requested <= Limit)
         │        └─ If Exceeded ──► Raise QuotaExceededException(429)
         │        └─ If Allowed  ──► Acquire UsageReservation(res_id, expires_at)
         │
         ▼
[Execute Domain Computation] (DuckDB / Polars / SciPy / Scikit-Learn Engine)
         │
         ├──► On Success ──► Finalize Reservation ──► Append UsageEvent ──► Update Balance Cache
         │
         └──► On Error   ──► Release Reservation ──► Quota Unlocked (No consumption recorded)
```

---

## 3. Product Plan Catalog & Entitlement Matrix

| Feature / Resource Metric | Canonical Key | FREE | PRO | TEAM | ENTERPRISE |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Max Dataset Upload Size** | `max_dataset_size_mb` | 50 MB | 500 MB | 2,000 MB | Unlimited (10 GB) |
| **Total Workspace Storage** | `storage_limit_bytes` | 1 GB | 20 GB | 100 GB | 1,000 GB (1 TB) |
| **Monthly Dataset Uploads** | `dataset_upload` | 10 uploads | 100 uploads | 500 uploads | Unlimited |
| **Active Projects** | `max_projects` | 3 | 25 | 100 | Unlimited |
| **Workspace Members** | `max_workspace_members` | 3 | 10 | 25 | Unlimited |
| **AI Analyst Messages** | `ai_analyst` | 100 / mo | 1,000 / mo | 5,000 / mo | Unlimited |
| **SQL Query Executions** | `sql_analytics` | 1,000 / mo | Unlimited | Unlimited | Unlimited |
| **Max SQL Result Rows** | `sql_max_result_rows` | 10,000 | 100,000 | 500,000 | 2,000,000 |
| **ML Model Training** | `machine_learning` | 20 runs / mo | 200 runs / mo | 1,000 runs / mo | Unlimited |
| **Time-Series Forecasts** | `forecasting` | 20 runs / mo | 200 runs / mo | 1,000 runs / mo | Unlimited |
| **Statistical Analyses** | `advanced_statistics` | 50 runs / mo | 500 runs / mo | 2,500 runs / mo | Unlimited |
| **Exports & Reports** | `exports` | 10 / mo | 100 / mo | 500 / mo | Unlimited |
| **Public Shareable Links** | `public_links` | Disabled | Enabled | Enabled | Enabled |

---

## 4. Architectural Components

```
backend/app/
├── engines/usage/
│   ├── models.py         # Plan, PlanEntitlement, WorkspacePlan, UsageEvent, UsageReservation, QuotaDecision
│   ├── metrics.py        # MetricKey definitions, registry, unit metadata
│   ├── catalog.py        # Canonical plan catalog definitions (FREE, PRO, TEAM, ENTERPRISE)
│   └── repository.py     # Thread-safe repository, atomic JSON persistence, reservations & aggregations
│
├── services/usage/
│   ├── plan_service.py   # Workspace plan assignment, catalog lookups, comparison matrix builder
│   ├── usage_service.py  # Append-only recording, idempotency, storage calculation, history & reconciliation
│   └── quota_service.py  # Check/enforce quota, atomic reservation lifecycle, warning thresholds
│
└── api/v1/
    ├── plans.py          # GET /api/v1/plans, GET /api/v1/plans/matrix, GET /api/v1/plans/current, POST /workspaces/{id}/plan
    └── usage.py          # GET /api/v1/usage/summary, GET /api/v1/usage/history, GET /api/v1/usage/reconcile
```

---

## 5. REST API Specifications

### `GET /api/v1/usage/summary`
Returns active plan, quota health indicators, usage breakdown, and point-in-time resource consumption.

### `GET /api/v1/usage/history`
Returns paginated, immutable usage events for the specified workspace and metric filter.

### `GET /api/v1/plans`
Returns the active product plan catalog.

### `GET /api/v1/plans/matrix`
Returns side-by-side feature comparison specifications across all tiers.

### `GET /api/v1/plans/current`
Returns active workspace plan details and all entitled feature limits.

### `POST /api/v1/workspaces/{workspace_id}/plan`
Changes workspace tier (`FREE`, `PRO`, `TEAM`, `ENTERPRISE`). Emits notification and preserves all existing datasets.

---

## 6. Frontend Usage Studio

Located at `/settings/usage`, the Usage Studio provides:
- **Active Plan Banner:** Current tier badge, billing/quota reset countdown.
- **Point-in-Time Resource Cards:** Physical storage, projects, and team members with percentage progress bars.
- **Monthly Analytical Quota Meters:** Dynamic color-coded meters (Green <70%, Amber 70-89%, Red 90%+) for AI, ML, Forecasting, SQL, Statistics, and Exports.
- **Entitlements Comparison Table:** Side-by-side matrix of all plan capabilities with active tier highlighting.
- **Append-Only Audit Log:** Live chronological table of discrete consumed events.
- **Tier Switching Modal:** Instant plan upgrade with live state refresh.
- **FeatureGate Component:** Reusable presentation gate for guarding premium UI widgets and triggering upgrade flows.
