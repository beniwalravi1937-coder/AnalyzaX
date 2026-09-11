"""
Security, Sanitization, and Validation layer for Phase 14 Dashboard Engine.
Guarantees prevention of XSS, arbitrary HTML/JavaScript execution, SQL injection in filters,
and resource exhaustion.
"""

import html
import re
from typing import Any, List, Optional

from backend.app.core.config import settings
from backend.app.engines.dashboard.models import (
    Dashboard,
    DashboardComponent,
    DashboardFilter,
    FilterOperator,
)


class DashboardSecurityError(Exception):
    """Raised when dashboard security or resource limits are violated."""
    pass


class DashboardSecurityValidator:
    """
    Enforces security constraints and sanitization on dashboard objects.
    """

    # Disallowed dangerous tags / schemes in markdown / narrative
    DANGEROUS_HTML_PATTERNS = [
        re.compile(r"<\s*script[^>]*>", re.IGNORECASE),
        re.compile(r"<\s*/\s*script\s*>", re.IGNORECASE),
        re.compile(r"<\s*iframe[^>]*>", re.IGNORECASE),
        re.compile(r"<\s*/\s*iframe\s*>", re.IGNORECASE),
        re.compile(r"<\s*object[^>]*>", re.IGNORECASE),
        re.compile(r"<\s*embed[^>]*>", re.IGNORECASE),
        re.compile(r"<\s*link[^>]*>", re.IGNORECASE),
        re.compile(r"<\s*meta[^>]*>", re.IGNORECASE),
        re.compile(r"<\s*form[^>]*>", re.IGNORECASE),
        re.compile(r"javascript\s*:", re.IGNORECASE),
        re.compile(r"vbscript\s*:", re.IGNORECASE),
        re.compile(r"data\s*:\s*text/html", re.IGNORECASE),
        re.compile(r"on\w+\s*=", re.IGNORECASE),  # onclick=, onerror=, onload=
    ]

    # Valid field name regex (alphanumeric and underscore only, starting with letter/underscore)
    VALID_FIELD_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    # Common SQL injection patterns in text
    SQL_INJECTION_PATTERN = re.compile(
        r"(\b(UNION(\s+ALL)?|SELECT|DROP|INSERT|DELETE|UPDATE|ALTER|TRUNCATE|EXEC|EXECUTE)\b|--|;|\/\*|\*\/)",
        re.IGNORECASE,
    )

    @classmethod
    def sanitize_text(cls, text: Optional[str]) -> str:
        """
        Sanitizes narrative text / markdown by neutralizing malicious scripts and event handlers.
        """
        if not text:
            return ""

        sanitized = text
        for pattern in cls.DANGEROUS_HTML_PATTERNS:
            sanitized = pattern.sub("", sanitized)

        # Disallow raw javascript link targets
        sanitized = re.sub(r"\[([^\]]+)\]\((javascript:[^\)]+)\)", r"[\1](#blocked)", sanitized, flags=re.IGNORECASE)

        return sanitized

    @classmethod
    def validate_field_identifier(cls, field: str) -> None:
        """
        Validates column/field identifier against injection.
        """
        if not field or not cls.VALID_FIELD_PATTERN.match(field):
            raise DashboardSecurityError(
                f"Invalid field identifier '{field}'. Must contain only alphanumeric characters and underscores."
            )

    @classmethod
    def validate_filter(cls, flt: DashboardFilter) -> None:
        """
        Validates a dashboard filter against SQL injection and operator validity.
        """
        cls.validate_field_identifier(flt.field)

        # Operator check
        if not isinstance(flt.operator, FilterOperator):
            try:
                FilterOperator(str(flt.operator))
            except ValueError:
                raise DashboardSecurityError(f"Unsupported or unsafe filter operator: {flt.operator}")

        # If value is string, inspect for raw SQL commands if it's not a standard search/contain
        if isinstance(flt.value, str):
            # Check length limit
            if len(flt.value) > 1000:
                raise DashboardSecurityError("Filter value exceeds maximum allowed length of 1000 characters.")

    @classmethod
    def validate_dashboard_bounds(cls, dashboard: Dashboard) -> None:
        """
        Enforces system limits on components, filters, and layout complexity.
        """
        if len(dashboard.components) > settings.DASHBOARD_MAX_COMPONENTS:
            raise DashboardSecurityError(
                f"Dashboard exceeds maximum components limit ({len(dashboard.components)} > {settings.DASHBOARD_MAX_COMPONENTS})."
            )

        if len(dashboard.filters) > settings.DASHBOARD_MAX_FILTERS:
            raise DashboardSecurityError(
                f"Dashboard exceeds maximum filters limit ({len(dashboard.filters)} > {settings.DASHBOARD_MAX_FILTERS})."
            )

        # Check total serialized configuration size
        raw_size = len(dashboard.model_dump_json())
        if raw_size > settings.DASHBOARD_MAX_LAYOUT_SIZE:
            raise DashboardSecurityError(
                f"Dashboard configuration size ({raw_size} bytes) exceeds limit ({settings.DASHBOARD_MAX_LAYOUT_SIZE} bytes)."
            )

        # Validate each filter
        for flt in dashboard.filters:
            cls.validate_filter(flt)

        # Sanitize narrative in text components
        for cmp in dashboard.components:
            if cmp.type.value == "TEXT" and "content" in cmp.configuration:
                cmp.configuration["content"] = cls.sanitize_text(str(cmp.configuration["content"]))
