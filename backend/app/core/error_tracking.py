"""
AnalyzaX — Phase 22: Error Tracking Abstraction.
Captures unhandled exceptions and operational failures with rich context
(request ID, job ID, release version, stack trace) without leaking sensitive data.
"""

import collections
import threading
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.core.logging import (
    ctx_correlation_id,
    ctx_job_id,
    ctx_request_id,
    logger,
    redact_sensitive_dict,
    redact_sensitive_string,
)


class TrackedError(BaseModel):
    error_id: str
    timestamp: str
    exception_type: str
    error_code: Optional[str] = None
    message: str
    stack_trace: str
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    job_id: Optional[str] = None
    environment: str
    release_version: str
    context: Dict[str, Any] = Field(default_factory=dict)


class ErrorTracker:
    """Centralized error tracker buffering recent errors and providing diagnostic inspection."""

    def __init__(self, max_buffer_size: int = 100) -> None:
        self._max_buffer_size = max_buffer_size
        self._buffer: List[TrackedError] = []
        self._lock = threading.Lock()
        self._error_counts: Dict[str, int] = collections.defaultdict(int)

    def capture_exception(
        self,
        exc: Exception,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        job_id: Optional[str] = None,
    ) -> TrackedError:
        """Captures an exception, redacting secrets and storing contextual diagnostics."""
        exc_type = type(exc).__name__
        raw_msg = str(exc)
        safe_msg = redact_sensitive_string(raw_msg)
        safe_trace = redact_sensitive_string(traceback.format_exc())
        safe_ctx = redact_sensitive_dict(context or {})

        req_id = ctx_request_id.get()
        corr_id = ctx_correlation_id.get()
        j_id = job_id or ctx_job_id.get()

        import uuid

        error_id = f"err_{uuid.uuid4().hex[:10]}"

        tracked = TrackedError(
            error_id=error_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            exception_type=exc_type,
            error_code=error_code,
            message=safe_msg,
            stack_trace=safe_trace,
            request_id=req_id,
            correlation_id=corr_id,
            job_id=j_id,
            environment=getattr(settings, "APP_ENV", "development"),
            release_version=getattr(settings, "RELEASE_VERSION", "1.0.0"),
            context=safe_ctx,
        )

        with self._lock:
            self._error_counts[exc_type] += 1
            self._buffer.append(tracked)
            if len(self._buffer) > self._max_buffer_size:
                self._buffer.pop(0)

        logger.error(
            f"ErrorTracker [{error_id}] {exc_type}: {safe_msg} (request_id={req_id}, job_id={j_id})"
        )

        return tracked

    def list_errors(self, limit: int = 50) -> List[TrackedError]:
        """Returns recent tracked errors in reverse chronological order."""
        with self._lock:
            return list(reversed(self._buffer[-limit:]))

    def get_summary(self) -> Dict[str, Any]:
        """Returns summary aggregation of captured errors."""
        with self._lock:
            return {
                "total_captured": sum(self._error_counts.values()),
                "by_type": dict(self._error_counts),
                "recent_count": len(self._buffer),
            }


error_tracker = ErrorTracker()
