"""
AnalyzaX Core Logging Module.
Re-exports the structured logging engine and application logger.
"""

from backend.app.core.structured_logging import (
    ctx_correlation_id,
    ctx_job_id,
    ctx_request_id,
    redact_sensitive_dict,
    redact_sensitive_string,
    setup_structured_logging,
)

logger = setup_structured_logging()

__all__ = [
    "logger",
    "setup_structured_logging",
    "ctx_request_id",
    "ctx_correlation_id",
    "ctx_job_id",
    "redact_sensitive_string",
    "redact_sensitive_dict",
]
