"""
AnalyzaX — Phase 22: Application Metrics & Telemetry.
Bounded-cardinality in-memory metrics collector supporting Prometheus exposition format
and JSON administrative diagnostics. Prevents high-cardinality metric explosion.
"""

import collections
import math
import threading
import time
from typing import Any, Dict, List, Optional


class MetricsCollector:
    """Thread-safe application metrics registry with bounded cardinality."""

    def __init__(self) -> None:
        self._lock = threading.Lock()

        # HTTP Metrics: Key: (method, endpoint_group, status_code) -> count
        self._http_requests: Dict[tuple, int] = collections.defaultdict(int)
        # Latency samples (capped circular buffer for percentile calculations)
        self._http_latencies: List[float] = []
        self._max_latency_samples = 2000

        # Database Metrics
        self._db_queries_total: int = 0
        self._db_errors_total: int = 0
        self._db_latencies: List[float] = []

        # Background Job Metrics: Key: (job_type, status) -> count
        self._job_counts: Dict[tuple, int] = collections.defaultdict(int)
        self._job_retries_total: int = 0
        self._job_durations: List[float] = []

        # AI & External Provider Metrics: Key: (provider, status) -> count
        self._ai_requests: Dict[tuple, int] = collections.defaultdict(int)
        self._ai_latencies: List[float] = []

        # Billing Metrics: Key: (event_type, status) -> count
        self._billing_events: Dict[tuple, int] = collections.defaultdict(int)

        # Storage Metrics: Key: (operation, status) -> count
        self._storage_operations: Dict[tuple, int] = collections.defaultdict(int)

        # Cache Metrics: Key: namespace -> count
        self._cache_hits: Dict[str, int] = collections.defaultdict(int)
        self._cache_misses: Dict[str, int] = collections.defaultdict(int)

        # Queue Metrics
        self._queue_depth: int = 0

        self._start_time = time.time()

    def record_http_request(
        self, method: str, endpoint: str, status_code: int, duration_ms: float
    ) -> None:
        """Records HTTP request and latency using normalized endpoint groups to bound cardinality."""
        # Normalize endpoint (e.g., /api/v1/datasets/ds_123/profile -> /api/v1/datasets/:id/profile)
        parts = endpoint.strip("/").split("/")
        norm_parts = []
        for p in parts:
            if len(p) > 20 or p.startswith(("ds_", "ws_", "proj_", "usr_", "sub_", "job_", "cs_")):
                norm_parts.append(":id")
            else:
                norm_parts.append(p)
        norm_endpoint = "/" + "/".join(norm_parts) if norm_parts else "/"

        status_group = f"{status_code // 100}xx"

        with self._lock:
            self._http_requests[(method.upper(), norm_endpoint, str(status_code))] += 1
            self._http_latencies.append(duration_ms)
            if len(self._http_latencies) > self._max_latency_samples:
                self._http_latencies.pop(0)

    def record_db_query(self, duration_ms: float, error: bool = False) -> None:
        """Records database query execution."""
        with self._lock:
            self._db_queries_total += 1
            if error:
                self._db_errors_total += 1
            self._db_latencies.append(duration_ms)
            if len(self._db_latencies) > 500:
                self._db_latencies.pop(0)

    def record_job(
        self, job_type: str, status: str, duration_sec: Optional[float] = None, retry: bool = False
    ) -> None:
        """Records background job execution state."""
        with self._lock:
            self._job_counts[(job_type.lower(), status.lower())] += 1
            if retry:
                self._job_retries_total += 1
            if duration_sec is not None:
                self._job_durations.append(duration_sec)
                if len(self._job_durations) > 500:
                    self._job_durations.pop(0)

    def record_ai_request(self, provider: str, status: str, duration_ms: float) -> None:
        """Records AI external provider latency and outcomes."""
        with self._lock:
            self._ai_requests[(provider.lower(), status.lower())] += 1
            self._ai_latencies.append(duration_ms)
            if len(self._ai_latencies) > 500:
                self._ai_latencies.pop(0)

    def record_billing_event(self, event_type: str, status: str) -> None:
        """Records billing transactions and webhooks."""
        with self._lock:
            self._billing_events[(event_type.lower(), status.lower())] += 1

    def record_storage_op(self, operation: str, status: str) -> None:
        """Records storage and upload operations."""
        with self._lock:
            self._storage_operations[(operation.lower(), status.lower())] += 1

    def record_cache_hit(self, namespace: str) -> None:
        """Records a cache hit for a given namespace."""
        with self._lock:
            self._cache_hits[namespace.lower()] += 1

    def record_cache_miss(self, namespace: str) -> None:
        """Records a cache miss for a given namespace."""
        with self._lock:
            self._cache_misses[namespace.lower()] += 1

    def record_queue_depth(self, depth: int) -> None:
        """Updates the current depth of active background jobs queue."""
        with self._lock:
            self._queue_depth = max(0, depth)

    def _calc_percentiles(self, samples: List[float]) -> Dict[str, float]:
        if not samples:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "avg": 0.0, "max": 0.0}
        sorted_s = sorted(samples)
        n = len(sorted_s)
        p50 = sorted_s[math.floor(n * 0.50)]
        p95 = sorted_s[min(math.floor(n * 0.95), n - 1)]
        p99 = sorted_s[min(math.floor(n * 0.99), n - 1)]
        avg = round(sum(sorted_s) / n, 2)
        return {
            "p50": round(p50, 2),
            "p95": round(p95, 2),
            "p99": round(p99, 2),
            "avg": avg,
            "max": round(sorted_s[-1], 2),
        }

    def get_summary(self) -> Dict[str, Any]:
        """Returns JSON-serializable telemetry dictionary."""
        with self._lock:
            uptime_seconds = round(time.time() - self._start_time, 1)
            http_total = sum(self._http_requests.values())
            http_errors = sum(
                count for (m, e, code), count in self._http_requests.items() if int(code) >= 400
            )

            http_breakdown = [
                {"method": m, "endpoint": e, "status": c, "count": cnt}
                for (m, e, c), cnt in sorted(self._http_requests.items(), key=lambda x: x[1], reverse=True)[:50]
            ]

            jobs_breakdown = [
                {"type": jtype, "status": st, "count": cnt}
                for (jtype, st), cnt in sorted(self._job_counts.items(), key=lambda x: x[1], reverse=True)
            ]

            ai_breakdown = [
                {"provider": prov, "status": st, "count": cnt}
                for (prov, st), cnt in self._ai_requests.items()
            ]

            billing_breakdown = [
                {"event": ev, "status": st, "count": cnt}
                for (ev, st), cnt in self._billing_events.items()
            ]

            storage_breakdown = [
                {"operation": op, "status": st, "count": cnt}
                for (op, st), cnt in self._storage_operations.items()
            ]

            total_hits = sum(self._cache_hits.values())
            total_misses = sum(self._cache_misses.values())
            total_lookups = total_hits + total_misses
            hit_ratio = round((total_hits / total_lookups) * 100, 2) if total_lookups > 0 else 0.0

            cache_breakdown = {
                "total_hits": total_hits,
                "total_misses": total_misses,
                "hit_ratio_percent": hit_ratio,
                "namespaces": {
                    ns: {
                        "hits": self._cache_hits.get(ns, 0),
                        "misses": self._cache_misses.get(ns, 0),
                    }
                    for ns in set(self._cache_hits.keys()).union(self._cache_misses.keys())
                },
            }

            return {
                "uptime_seconds": uptime_seconds,
                "http": {
                    "total_requests": http_total,
                    "total_errors": http_errors,
                    "error_rate": round(http_errors / http_total, 4) if http_total > 0 else 0.0,
                    "latency_ms": self._calc_percentiles(self._http_latencies),
                    "routes": http_breakdown,
                },
                "database": {
                    "total_queries": self._db_queries_total,
                    "total_errors": self._db_errors_total,
                    "latency_ms": self._calc_percentiles(self._db_latencies),
                },
                "jobs": {
                    "total_retries": self._job_retries_total,
                    "current_queue_depth": self._queue_depth,
                    "summary": jobs_breakdown,
                    "duration_sec": self._calc_percentiles(self._job_durations),
                },
                "ai": {
                    "summary": ai_breakdown,
                    "latency_ms": self._calc_percentiles(self._ai_latencies),
                },
                "billing": {
                    "summary": billing_breakdown,
                },
                "storage": {
                    "summary": storage_breakdown,
                },
                "cache": cache_breakdown,
            }

    def export_prometheus(self) -> str:
        """Formats collected metrics as Prometheus text exposition format."""
        summary = self.get_summary()
        lines: List[str] = [
            "# HELP analyzax_uptime_seconds Process uptime in seconds",
            "# TYPE analyzax_uptime_seconds counter",
            f"analyzax_uptime_seconds {summary['uptime_seconds']}",
            "# HELP analyzax_http_requests_total Total HTTP requests",
            "# TYPE analyzax_http_requests_total counter",
        ]

        with self._lock:
            for (m, e, c), cnt in self._http_requests.items():
                lines.append(
                    f'analyzax_http_requests_total{{method="{m}",endpoint="{e}",status="{c}"}} {cnt}'
                )

            lines.extend([
                "# HELP analyzax_http_latency_milliseconds HTTP latency percentiles",
                "# TYPE analyzax_http_latency_milliseconds gauge",
                f'analyzax_http_latency_milliseconds{{quantile="0.5"}} {summary["http"]["latency_ms"]["p50"]}',
                f'analyzax_http_latency_milliseconds{{quantile="0.95"}} {summary["http"]["latency_ms"]["p95"]}',
                f'analyzax_http_latency_milliseconds{{quantile="0.99"}} {summary["http"]["latency_ms"]["p99"]}',
                "# HELP analyzax_db_queries_total Total database queries",
                "# TYPE analyzax_db_queries_total counter",
                f"analyzax_db_queries_total {self._db_queries_total}",
                "# HELP analyzax_db_errors_total Total database query errors",
                "# TYPE analyzax_db_errors_total counter",
                f"analyzax_db_errors_total {self._db_errors_total}",
                "# HELP analyzax_jobs_total Background jobs processed by type and status",
                "# TYPE analyzax_jobs_total counter",
            ])

            for (jtype, st), cnt in self._job_counts.items():
                lines.append(
                    f'analyzax_jobs_total{{job_type="{jtype}",status="{st}"}} {cnt}'
                )

            lines.extend([
                "# HELP analyzax_job_queue_depth Active jobs waiting or running in queue",
                "# TYPE analyzax_job_queue_depth gauge",
                f"analyzax_job_queue_depth {self._queue_depth}",
                "# HELP analyzax_cache_hits_total Total cache hits by namespace",
                "# TYPE analyzax_cache_hits_total counter",
            ])
            for ns, hits in self._cache_hits.items():
                lines.append(f'analyzax_cache_hits_total{{namespace="{ns}"}} {hits}')

            lines.extend([
                "# HELP analyzax_cache_misses_total Total cache misses by namespace",
                "# TYPE analyzax_cache_misses_total counter",
            ])
            for ns, misses in self._cache_misses.items():
                lines.append(f'analyzax_cache_misses_total{{namespace="{ns}"}} {misses}')

        return "\n".join(lines) + "\n"


metrics_collector = MetricsCollector()
