"""
AnalyzaX — Phase 22: HTTP Metrics Telemetry Middleware.
Records request counts, response codes, and latency distributions in metrics_collector.
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from backend.app.core.metrics import metrics_collector


class MetricsMiddleware(BaseHTTPMiddleware):
    """Measures request duration and outcome status codes for telemetry reporting."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            metrics_collector.record_http_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=status_code,
                duration_ms=duration_ms,
            )
