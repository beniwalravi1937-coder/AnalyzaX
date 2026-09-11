from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from backend.app.core.logging import logger


class AnalyzaXException(Exception):
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class DuckDBInitializationError(AnalyzaXException):
    def __init__(self, message: str = "Failed to initialize DuckDB analytical engine"):
        super().__init__(
            message=message,
            code="DUCKDB_INIT_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class DatabaseConnectionError(AnalyzaXException):
    def __init__(self, message: str = "Failed to connect to metadata database"):
        super().__init__(
            message=message,
            code="DATABASE_CONNECTION_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class QuotaExceededException(AnalyzaXException):
    def __init__(
        self,
        message: str,
        metric: Optional[str] = None,
        feature: Optional[str] = None,
        current_usage: float = 0.0,
        requested: float = 1.0,
        limit: Optional[float] = None,
        remaining: Optional[float] = None,
        period: Optional[str] = None,
        reset_at: Optional[str] = None,
        plan: str = "FREE",
    ):
        super().__init__(
            message=message,
            code="QUOTA_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={
                "category": "USAGE_LIMIT",
                "metric": metric,
                "feature": feature,
                "current_usage": current_usage,
                "requested": requested,
                "limit": limit,
                "remaining": remaining,
                "period": period,
                "reset_at": reset_at,
                "plan": plan,
            },
        )
        self.metric = metric
        self.feature = feature
        self.current_usage = current_usage
        self.requested = requested
        self.limit = limit
        self.remaining = remaining
        self.period = period
        self.reset_at = reset_at
        self.plan = plan


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AnalyzaXException)
    async def analyzax_exception_handler(request: Request, exc: AnalyzaXException):
        logger.error(f"AnalyzaXException: [{exc.code}] {exc.message} - Path: {request.url.path}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(
            f"HTTPException: {exc.status_code} - {exc.detail} - Path: {request.url.path}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": str(exc.detail),
                },
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled Exception on {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected internal server error occurred.",
                },
            },
        )
