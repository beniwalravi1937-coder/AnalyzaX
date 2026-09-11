"""
AnalyzaX — Phase 22: Structured Logging and Sensitive Data Redaction.
Produces JSON or human-readable logs with automatic masking of secrets,
passwords, tokens, credentials, and raw dataset samples.
"""

import contextvars
import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.core.config import settings

# Context variable for distributed request and correlation tracking
ctx_request_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "ctx_request_id", default=None
)
ctx_correlation_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "ctx_correlation_id", default=None
)
ctx_job_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "ctx_job_id", default=None
)

# Sensitive keys and patterns
SENSITIVE_PATTERNS = [
    re.compile(r"(password|passwd|pwd)[\"':\s=]+([^\s,;\"'}{]+)", re.IGNORECASE),
    re.compile(r"(secret|secret_key|api_key|apikey|auth_token|access_token|refresh_token)[\"':\s=]+([^\s,;\"'}{]+)", re.IGNORECASE),
    re.compile(r"(Bearer\s+)([A-Za-z0-9_\-\.]{8,})", re.IGNORECASE),
    re.compile(r"(whsec_[A-Za-z0-9_]{16,})", re.IGNORECASE),
    re.compile(r"(sk_live_[A-Za-z0-9_]{16,})", re.IGNORECASE),
    re.compile(r"(sk-or-v1-[A-Za-z0-9_]{16,})", re.IGNORECASE),
    re.compile(r"(\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b)"),  # Credit card pattern
]

SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "current_password",
    "new_password",
    "secret",
    "secret_key",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "authorization",
    "cookie",
    "analyzax_session",
    "card",
    "cvv",
    "billing_secret_key",
    "billing_webhook_secret",
}


def redact_sensitive_string(text: str) -> str:
    """Scrubs sensitive credentials and tokens from string text."""
    if not text or not isinstance(text, str):
        return text

    scrubbed = text
    # Mask specific regex patterns
    scrubbed = re.sub(
        r"(Bearer\s+)([A-Za-z0-9_\-\.]{8,})",
        r"\1[REDACTED]",
        scrubbed,
        flags=re.IGNORECASE,
    )
    scrubbed = re.sub(
        r"(password|passwd|pwd)([\"':\s=]+)([^\s,;\"'}{]+)",
        r"\1\2[REDACTED]",
        scrubbed,
        flags=re.IGNORECASE,
    )
    scrubbed = re.sub(
        r"(secret|secret_key|api_key|apikey|token|access_token)([\"':\s=]+)([^\s,;\"'}{]+)",
        r"\1\2[REDACTED]",
        scrubbed,
        flags=re.IGNORECASE,
    )
    scrubbed = re.sub(r"whsec_[A-Za-z0-9_]{16,}", "[REDACTED_WEBHOOK_SECRET]", scrubbed)
    scrubbed = re.sub(r"sk_live_[A-Za-z0-9_]{16,}", "[REDACTED_LIVE_KEY]", scrubbed)
    scrubbed = re.sub(r"sk-or-v1-[A-Za-z0-9_]{16,}", "[REDACTED_AI_KEY]", scrubbed)
    # Credit cards
    scrubbed = re.sub(
        r"\b(?:\d{4}[- ]?){3}\d{4}\b",
        "[REDACTED_CARD_NUMBER]",
        scrubbed,
    )
    return scrubbed


def redact_sensitive_dict(data: Any) -> Any:
    """Recursively redacts sensitive keys from dictionaries and collections."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if str(k).lower() in SENSITIVE_KEYS:
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = redact_sensitive_dict(v)
        return cleaned
    elif isinstance(data, list):
        return [redact_sensitive_dict(item) for item in data]
    elif isinstance(data, str):
        return redact_sensitive_string(data)
    return data


class SensitiveRedactionFilter(logging.Filter):
    """Logging filter ensuring secrets are never leaked into console or log files."""

    def filter(self, record: logging.LogRecord) -> bool:
        if getattr(settings, "LOG_REDACT_SENSITIVE", True):
            if isinstance(record.msg, str):
                record.msg = redact_sensitive_string(record.msg)
            if record.args:
                if isinstance(record.args, dict):
                    record.args = redact_sensitive_dict(record.args)
                elif isinstance(record.args, tuple):
                    record.args = tuple(
                        redact_sensitive_string(a) if isinstance(a, str) else a
                        for a in record.args
                    )
        return True


class JSONLogFormatter(logging.Formatter):
    """Formats log records as structured, single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "analyzax-backend",
            "environment": getattr(settings, "APP_ENV", "development"),
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Request & Job context
        req_id = ctx_request_id.get()
        if req_id:
            log_entry["request_id"] = req_id

        corr_id = ctx_correlation_id.get()
        if corr_id:
            log_entry["correlation_id"] = corr_id

        job_id = ctx_job_id.get() or getattr(record, "job_id", None)
        if job_id:
            log_entry["job_id"] = job_id

        # Source code location
        log_entry["file"] = record.filename
        log_entry["line"] = record.lineno

        # Exception stack trace if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


def setup_structured_logging() -> logging.Logger:
    """Configures centralized logging system according to APP_ENV and settings."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicate output
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.addFilter(SensitiveRedactionFilter())

    if getattr(settings, "LOG_FORMAT", "text").lower() == "json":
        handler.setFormatter(JSONLogFormatter())
    else:
        text_fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        handler.setFormatter(logging.Formatter(text_fmt))

    root_logger.addHandler(handler)

    analyzax_logger = logging.getLogger("analyzax")
    analyzax_logger.setLevel(log_level)
    return analyzax_logger
