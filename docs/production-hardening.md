# AnalyzaX — Production Hardening, Operations & Infrastructure Architecture (Phase 22)

This document provides the canonical architectural and operational reference for the production deployment, security hardening, monitoring, and disaster recovery subsystems introduced in **Phase 22**.

---

## 1. Architectural Foundations & Operational Pipelines

Phase 22 establishes enterprise-grade operational discipline across 7 core pillars:

```
[Inbound Traffic] ───► [Nginx Edge / TLS]
                             │ (Reverse proxy, Gzip, Rate limiting, 500MB upload body)
                             ▼
                    [FastAPI Middleware Pipeline]
                             │
                             ├─► [1. RateLimitMiddleware] (Endpoint-specific sliding window)
                             ├─► [2. SecurityHeadersMiddleware] (HSTS, CSP, X-Frame-Options, Nosniff)
                             ├─► [3. MetricsMiddleware] (Latency, status codes, Prometheus export)
                             ├─► [4. CorrelationMiddleware] (X-Request-ID, X-Correlation-ID propagation)
                             └─► [5. Exception Handlers] (Centralized JSON errors with request IDs)
                                       │
                                       ▼
                       [Application Services & Engines]
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
   [Versioned Migrations]     [Background Jobs / DLQ]    [Durable Storage Isolation]
   (Locking, Schema Tracking)  (LocalDurableQueue, Pool)   (Path validation, Signed URLs)
```

---

## 2. Configuration Auditing & Fail-Fast Validator

The centralized `ProductionConfigValidator` (`backend/app/core/config_validator.py`) enforces that no instance can launch in production with development defaults or insecure configurations.

### Production Quality Gates
| Gate ID | Check | Strict Requirement |
|---|---|---|
| `GATE-01` | `DEBUG_DISABLED` | `DEBUG=False` mandatory in production. |
| `GATE-02` | `SECRET_KEY_COMPLEXITY` | Minimum 32 characters; rejects default, insecure substrings. |
| `GATE-03` | `DATABASE_URL_SECURE` | Non-empty; rejects default passwords (`postgres`, `password`, `changeme`). |
| `GATE-04` | `CORS_ORIGINS_RESTRICTED` | Disallows wildcard `*` origins in production. |
| `GATE-05` | `STORAGE_ROOT_PERMISSIONS` | Verifies write permissions on `DATA_STORAGE_ROOT`. |
| `GATE-06` | `RATE_LIMITING_ENABLED` | `RATE_LIMIT_ENABLED=True` with configured RPM thresholds. |
| `GATE-07` | `SECURITY_HEADERS_ENABLED`| `SECURITY_HEADERS_ENABLED=True` with HSTS and CSP. |

Operators can run the validator directly from the command line:
```bash
python -m backend.app.core.config_validator --env production
```

---

## 3. Defensive Security Headers Matrix

All responses issued by FastAPI automatically contain hardened OWASP headers (`SecurityHeadersMiddleware`):

| HTTP Header | Production Value | Protection Objective |
|---|---|---|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Enforces HTTPS exclusively across modern browsers. |
| `X-Content-Type-Options` | `nosniff` | Prevents MIME-type confusion and content sniffing attacks. |
| `X-Frame-Options` | `DENY` | Completely prevents clickjacking in external iframes. |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Protects sensitive URL path parameters across cross-origin requests. |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | Disables access to sensitive browser device hardware APIs. |
| `Content-Security-Policy` | `default-src 'self'; script-src 'self' ...` | Prevents unauthorized inline script injections and external assets. |

---

## 4. Multi-Tier Rate Limiting

The `RateLimitMiddleware` enforces client-level sliding window rate limits:

| Category | Endpoints | Default Limit | Purpose |
|---|---|---|---|
| **Auth** | `/api/v1/auth/*` | 10 RPM | Prevents credential stuffing and brute force attacks. |
| **AI Analyst** | `/api/v1/ai-analyst/*` | 20 RPM | Protects upstream LLM tokens and prevents abuse. |
| **SQL Engine** | `/api/v1/sql/*` | 30 RPM | Protects DuckDB from execution starvation. |
| **Exports** | `/api/v1/exports/*` | 15 RPM | Limits heavy PDF / Excel rendering compute loads. |
| **Uploads** | `/api/v1/datasets/upload` | 20 RPM | Manages network saturation and storage throughput. |
| **General** | Default | 120 RPM | Protects all general presentation and metadata APIs. |

*Exemptions:* Container orchestrator probes (`/health/live`, `/health/ready`, `/health`) and Prometheus scraping (`/metrics`) are explicitly exempt from rate limiting to prevent false-positive alert floods.

---

## 5. Health, Liveness & Readiness Probes

### 1. Process Liveness (`/health/live`)
- **Consumer:** Kubernetes / Docker Swarm / Load Balancer liveness checks.
- **Rule:** Never calls external dependencies or databases. Guarantees that external network blips or database restarts do not cause cascading container restarts.
- **Response:** `200 OK` with `status: "alive"`.

### 2. Dependency Readiness (`/health/ready`)
- **Consumer:** Service routing proxies.
- **Rule:** Probes critical local dependencies (DuckDB engine responsive, storage directory writable). Evaluates optional dependencies without rejecting traffic unless in strict production mode.
- **Response:** `200 OK` (or `503 Service Unavailable` if critical engines are down) with structured dependency latency metrics.

### 3. Comprehensive System Health (`/health`)
- **Consumer:** Diagnostic operators and monitoring tools.
- **Response:** Releases versions, environment, uptime, DuckDB status, and database status.

---

## 6. Telemetry & Prometheus Metric Catalog

Standard Prometheus scraper format is exposed at `/metrics`. Internal diagnostic JSON summaries are exposed at `/api/v1/admin/metrics`.

| Metric Name | Type | Description |
|---|---|---|
| `analyzax_uptime_seconds` | Gauge | Uptime of the active process. |
| `analyzax_http_requests_total` | Counter | Total HTTP requests categorized by method, path category, and status. |
| `analyzax_http_request_duration_ms_avg` | Gauge | Average request latency over the active process lifetime. |
| `analyzax_db_queries_total` | Counter | Database queries executed. |
| `analyzax_db_query_duration_ms_avg` | Gauge | Average query latency in milliseconds. |
| `analyzax_jobs_total` | Counter | Background jobs by type, status (completed/failed/retried). |
| `analyzax_errors_total` | Counter | Captured application errors by error code and release version. |

---

## 7. Versioned Migrations & Distributed Locking

The migration engine (`backend/app/core/migrations/`):
1. Acquires a distributed lock (`.migration.lock` / PostgreSQL advisory lock `884729103`).
2. Discovers numbered migration scripts in sequence (`001_initial_metadata.py`, `002_jobs_ledger.py`).
3. Executes pending migrations atomically and logs duration in `schema_migrations.json`.
4. Guarantees idempotency — running `migrate()` consecutively is a safe no-op.
5. Supports safe rollback via `rollback(version)` when downgrade hooks exist.

---

## 8. Durable Storage Provider & Path Isolation

The `LocalStorageProvider` (`backend/app/engines/storage/local_provider.py`):
- Enforces strict tenant containment: paths must reside within `DATA_STORAGE_ROOT`.
- Detects and rejects path traversal attacks (`../`, `..\\`, absolute root escapes) with `ValueError`.
- Generates HMAC-SHA256 signed download URLs with configurable expiry.
- Accompanied by `S3StorageProvider` for enterprise S3 / MinIO object storage.

---

## 9. Background Job Workers & Dead-Letter Queue (DLQ)

The background job subsystem (`backend/app/engines/jobs/`):
- Uses `LocalDurableQueue` with thread-safe priority heap and atomic JSON persistence under `data/jobs/`.
- `JobWorkerPool` runs bounded concurrency workers.
- Supports error classification:
  - `TransientJobError`: Automatically retries with exponential backoff.
  - `PermanentJobError`: Immediately fails and moves to Dead-Letter Queue (`data/jobs/dlq/`) for administrative inspection.
- Guarantees cooperative cancellation and graceful shutdown on `SIGTERM` / `SIGINT`.

---

## 10. Multi-Stage Docker & Non-Root Containers

### Backend Image
- Multi-stage build (`python:3.11-slim` builder + runtime).
- Runs under non-root user `analyzax` (`UID 10001`, `GID 10001`).
- Built-in `HEALTHCHECK` querying `/health/live`.
- Persists data to isolated Docker volume `analyzax_data`.

### Frontend Image
- Multi-stage build (`node:22-alpine` deps + builder + runner).
- Runs under non-root user `nextjs` (`UID 10001`, `GID 10001`).
- Built-in `HEALTHCHECK` querying port 3000.

### Reverse Proxy (Nginx)
- Dedicated Nginx 1.25 Alpine reverse proxy routing `/api`, `/ws`, `/health`, `/metrics`, and UI traffic.
- Configured with Gzip compression, rate limit zones, and 500MB upload limits.
