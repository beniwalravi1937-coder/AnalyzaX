"""
AnalyzaX — Phase 22: Request & Correlation ID Middleware.
Injects unique request tracking IDs, populates contextvars for structured logging,
and guarantees end-to-end tracing headers on all API responses.
"""

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from backend.app.core.logging import (
    ctx_correlation_id,
    ctx_request_id,
    logger,
)


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware attaching request_id and correlation_id to context and response headers."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 1. Resolve or generate request_id
        req_id = request.headers.get("x-request-id") or f"req_{uuid.uuid4().hex[:12]}"
        corr_id = (
            request.headers.get("x-correlation-id")
            or request.headers.get("x-trace-id")
            or req_id
        )

        # 2. Set Context Variables for Structured Logging
        t_req = ctx_request_id.set(req_id)
        t_corr = ctx_correlation_id.set(corr_id)

        # Attach to request state for handler access
        request.state.request_id = req_id
        request.state.correlation_id = corr_id

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # 3. Add response headers
            response.headers["X-Request-ID"] = req_id
            response.headers["X-Correlation-ID"] = corr_id
            response.headers["X-Response-Time"] = f"{duration_ms}ms"

            # Optional access log for non-health requests
            if not request.url.path.startswith("/health") and not request.url.path.startswith("/api/v1/health"):
                logger.info(
                    f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)"
                )

            return response
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"Unhandled error in {request.method} {request.url.path} ({duration_ms}ms): {exc}",
                exc_info=True,
            )
            raise
        finally:
            ctx_request_id.reset(t_req)
            ctx_correlation_id.reset(t_corr)
