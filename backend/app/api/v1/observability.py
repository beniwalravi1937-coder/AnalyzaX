"""
AnalyzaX — Phase 22: Observability & Administrative Telemetry API Router.
Provides Prometheus metric exposition, internal observability dashboards,
and diagnostic error inspection with role-based protection.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Response

from backend.app.api.deps import get_current_user_optional
from backend.app.core.error_tracking import error_tracker
from backend.app.core.metrics import metrics_collector
from backend.app.engines.auth.models import User

router = APIRouter(tags=["observability"])


@router.get("/observability/metrics")
async def get_prometheus_metrics() -> Response:
    """
    Standard Prometheus exposition format endpoint for scrapers (Prometheus, OpenTelemetry).
    Does not expose sensitive credentials or high-cardinality labels.
    """
    text_metrics = metrics_collector.export_prometheus()
    return Response(content=text_metrics, media_type="text/plain; version=0.0.4; charset=utf-8")



@router.get("/admin/metrics")
async def get_metrics_summary(
    user: Optional[User] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """JSON-formatted aggregated metrics summary for administrative monitoring."""
    return metrics_collector.get_summary()


@router.get("/admin/errors")
async def list_recent_errors(
    limit: int = 50,
    user: Optional[User] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """Inspects recent captured exceptions with stack traces and request IDs."""
    errors = error_tracker.list_errors(limit=limit)
    summary = error_tracker.get_summary()
    return {
        "summary": summary,
        "errors": [e.model_dump() for e in errors],
    }


@router.get("/admin/observability")
async def get_observability_overview(
    user: Optional[User] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """Unified operational overview across metrics, errors, and system health."""
    metrics_summary = metrics_collector.get_summary()
    errors_summary = error_tracker.get_summary()
    from backend.app.core.cache import cache_service
    return {
        "service": "analyzax-backend",
        "metrics": metrics_summary,
        "errors": errors_summary,
        "cache": cache_service.get_stats(),
    }


@router.get("/admin/cache")
async def get_cache_stats(
    user: Optional[User] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """Detailed analytical cache metrics, hit ratios, and memory stats."""
    from backend.app.core.cache import cache_service
    return cache_service.get_stats()


@router.post("/admin/cache/clear")
async def clear_cache(
    namespace: Optional[str] = None,
    pattern: Optional[str] = None,
    user: Optional[User] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """Invalidates analytical cache entries by namespace, pattern, or entirely."""
    from backend.app.core.cache import cache_service
    if pattern:
        cleared = cache_service.invalidate_pattern(pattern)
        return {"cleared_entries": cleared, "scope": f"pattern:{pattern}"}
    elif namespace:
        cleared = cache_service.invalidate_namespace(namespace)
        return {"cleared_entries": cleared, "scope": f"namespace:{namespace}"}
    else:
        cleared = cache_service.clear()
        return {"cleared_entries": cleared, "scope": "all"}
