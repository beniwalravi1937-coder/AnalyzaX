# AnalyzaX — Caching, Performance & Query Optimization Architecture (Phase 23)

## 1. Executive Summary

Phase 23 establishes the enterprise-grade caching, out-of-core scaling, and query optimization architecture for AnalyzaX. The system guarantees sub-second analytical response times for repeated queries, protects analytical backends against cache stampedes, isolates multi-tenant workloads, and supports large datasets without out-of-memory crashes.

---

## 2. Core Architectural Principles

1. **Deterministic Cache Key Generation**:
   All cache keys are structured hierarchically:
   `{namespace}:{workspace_id}:{dataset_id}:{version_id}:{operation}:{param_hash}:{engine_version}`
   - **Tenant Isolation**: `workspace_id` is mandatory, preventing cross-tenant leakage.
   - **Version Isolation**: Dataset and model version IDs guarantee that modifying or transforming a dataset produces an isolated cache key.
   - **Deterministic Digesting**: Query parameters, filters, and aggregations are sorted and hashed using SHA-256 (16-char hex).
   - **Engine Versioning**: Internal analytical model updates invalidate stale cache representations.

2. **Thread-Safe LRU & TTL Cache Service (`CacheService`)**:
   - In-memory thread-safe store with adaptive capacity eviction (`DEFAULT_MAX_ENTRIES = 5000`).
   - True LRU access tracking (refreshing last-access timestamps on hits).
   - Configurable TTL support (24 hours for deterministic immutable versions, 60 seconds for dynamic catalogs).
   - Safe fallback: If caching encounters unexpected errors, computation proceeds directly against authoritative engines without failing user requests.

3. **Single-Flight Stampede Protection (`SingleFlight`)**:
   - Suppresses duplicate concurrent in-flight computations for identical cache keys.
   - When 50 concurrent requests miss the same analytical cache key (e.g., complex correlation matrix or dataset profile), exactly 1 leader worker executes the heavy calculation.
   - The remaining 49 followers wait on thread coordination events and receive the shared computed result.
   - Immune to race conditions via dedicated `_SingleFlightCall` reference retention.

4. **Multi-Tier Invalidation Protocol**:
   - **Namespace Invalidation**: `invalidate_namespace("profile")` sweeps all keys for a specific analytical domain.
   - **Pattern Invalidation**: `invalidate_pattern(dataset_id)` atomically sweeps all profiles, quality scores, EDA summaries, and statistics across all versions when a dataset is deleted.

5. **DuckDB Query & Out-of-Core Execution**:
   - DuckDB operates as an embedded vectorized columnar engine with strict thread and memory limits:
     - `threads`: Configured via settings (default 4).
     - `max_memory`: Bound to prevent host memory exhaustion (default 4GB).
     - `temp_directory`: Spill-to-disk directory for out-of-core operations exceeding RAM.
   - Result caching for expensive read-only SQL queries with automatic hash-based deduplication.
   - Streaming row generation and pagination prevents buffering multi-gigabyte query outputs in memory.

6. **FastAPI & HTTP Transport Optimization**:
   - **GZip Compression**: Dynamic streaming GZip compression (`minimum_size=1024` bytes) via `GZipMiddleware` reduces JSON bandwidth consumption by up to 85% for large dataframes and correlation matrices.
   - **Operational Telemetry**:
     - `GET /api/v1/admin/cache`: Live cache hit ratio, entry count, miss count, and memory utilization.
     - `POST /api/v1/admin/cache/clear`: Administrative cache clearance by namespace or pattern.
     - `GET /api/v1/admin/observability`: Unified dashboard consolidating system health, database pools, and cache telemetry.

---

## 3. Cache Namespaces

| Namespace | Typical TTL | Operations Cached | Invalidation Event |
|---|---|---|---|
| `profile` | 24 Hours | Full profile, column summaries, quantiles | Dataset version deleted, transformed |
| `quality` | 24 Hours | Quality grade, dimension scores, issue audits | Dataset version deleted, transformed |
| `eda` | 24 Hours | Correlation matrices, histograms, scatter samples | Dataset version deleted, transformed |
| `stats` | 24 Hours | Hypothesis tests, ANOVA, regression summaries | Dataset version deleted |
| `sql` | 1 Hour | Deterministic SELECT query results, table previews | Dataset table drop / update |
| `catalog` | 1 Minute | Plan tiers, pricing catalog | Admin configuration update |

---

## 4. Verification & Testing

- **Unit & Concurrency Tests (`backend/tests/test_caching_and_performance.py`)**:
  - Deterministic key generation and multi-tenant isolation.
  - LRU capacity eviction and TTL expiration.
  - Single-flight concurrency stampede deduplication.
  - Pattern and namespace invalidation.
- **API Tests (`backend/tests/test_performance_api.py`)**:
  - Administrative cache telemetry retrieval (`/api/v1/admin/cache`).
  - Cache clearing by namespace and pattern.
  - Unified observability endpoint integration.
  - GZip compression headers on payloads > 1024 bytes.
- **Analytical Regression**:
  - 44/44 automated tests passing across Profiling, Quality, EDA, Statistics, SQL, Usage/Quotas, and Performance.
