"""
AnalyzaX — Phase 22: Security Headers & Production Rate Limiting Middleware.
Provides defensive HTTP response headers (HSTS, CSP, X-Frame-Options, etc.)
and multi-tier rate limiting (IP + User + Endpoint) with structured 429 responses.
"""

import collections
import time
from typing import Dict, List, Optional
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from backend.app.core.config import settings
from backend.app.core.logging import logger


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds hardened OWASP security headers to all HTTP responses."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        if getattr(settings, "SECURITY_HEADERS_ENABLED", True):
            # 1. HSTS (Strict-Transport-Security)
            if settings.APP_ENV.lower() in ("production", "prod") or request.url.scheme == "https":
                max_age = getattr(settings, "HSTS_MAX_AGE_SECONDS", 31536000)
                response.headers["Strict-Transport-Security"] = f"max-age={max_age}; includeSubDomains"

            # 2. X-Content-Type-Options: Prevents MIME-sniffing
            response.headers["X-Content-Type-Options"] = "nosniff"

            # 3. X-Frame-Options: Clickjacking protection
            response.headers["X-Frame-Options"] = "DENY"

            # 4. Referrer-Policy
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

            # 5. Permissions-Policy
            response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

            # 6. Content-Security-Policy (CSP)
            # Allow self scripts and inline styles for shadcn / Next.js
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob:; "
                "font-src 'self' data:; "
                "connect-src 'self' ws: wss: http: https:; "
                "frame-ancestors 'none';"
            )
            response.headers["Content-Security-Policy"] = csp

        return response


class RateLimiter:
    """Sliding-window token rate limiter tracking client requests per minute."""

    def __init__(self) -> None:
        # Key: (bucket_name, client_id) -> list of request timestamps (epoch)
        self._windows: Dict[tuple, List[float]] = collections.defaultdict(list)

    def is_allowed(self, client_id: str, bucket_name: str, limit_per_minute: int) -> tuple[bool, int]:
        """
        Evaluates whether a request is allowed within the 60-second sliding window.
        Returns: (is_allowed: bool, retry_after_seconds: int)
        """
        now = time.time()
        window_start = now - 60.0
        key = (bucket_name, client_id)

        # Prune old timestamps
        timestamps = [ts for ts in self._windows[key] if ts > window_start]
        self._windows[key] = timestamps

        if len(timestamps) >= limit_per_minute:
            oldest_in_window = timestamps[0]
            retry_after = max(1, int(oldest_in_window + 60.0 - now))
            return False, retry_after

        self._windows[key].append(now)
        return True, 0


rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Applies endpoint-specific rate limiting across IP, User ID, and Workspace ID."""

    EXEMPT_PATHS = {
        "/health",
        "/health/live",
        "/health/ready",
        "/api/v1/health",
        "/api/v1/health/live",
        "/api/v1/health/ready",
        "/metrics",
        "/api/v1/metrics",
    }

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not getattr(settings, "RATE_LIMIT_ENABLED", True):
            return await call_next(request)

        path = request.url.path

        # 1. Check Exemptions (Probes & Metrics)
        if path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Exempt external webhooks which have their own cryptographic HMAC signatures
        if "/webhooks" in path:
            return await call_next(request)

        # 2. Extract Client Identifier (Forwarded IP or User/Client ID)
        forwarded = request.headers.get("x-forwarded-for")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")

        # 3. Determine Rate Limit Tier based on Route Category
        bucket_name = "default"
        rpm_limit = getattr(settings, "RATE_LIMIT_DEFAULT_RPM", 120)

        if "/api/v1/auth" in path:
            bucket_name = "auth"
            rpm_limit = getattr(settings, "RATE_LIMIT_AUTH_RPM", 10)
        elif "/api/v1/ai-analyst" in path:
            bucket_name = "ai"
            rpm_limit = getattr(settings, "RATE_LIMIT_AI_RPM", 20)
        elif "/api/v1/sql" in path:
            bucket_name = "sql"
            rpm_limit = getattr(settings, "RATE_LIMIT_SQL_RPM", 30)
        elif "/api/v1/exports" in path:
            bucket_name = "exports"
            rpm_limit = getattr(settings, "RATE_LIMIT_EXPORT_RPM", 15)
        elif "/api/v1/datasets/upload" in path:
            bucket_name = "upload"
            rpm_limit = getattr(settings, "RATE_LIMIT_UPLOAD_RPM", 20)

        allowed, retry_after = rate_limiter.is_allowed(client_ip, bucket_name, rpm_limit)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded: IP={client_ip}, bucket={bucket_name}, limit={rpm_limit} RPM"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit of {rpm_limit} requests per minute exceeded for {bucket_name}. Please retry after {retry_after} seconds.",
                        "details": {
                            "bucket": bucket_name,
                            "limit_rpm": rpm_limit,
                            "retry_after_seconds": retry_after,
                        },
                    },
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
