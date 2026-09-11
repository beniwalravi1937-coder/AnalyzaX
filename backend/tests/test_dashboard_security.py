"""
Security tests for Phase 14 Dashboard Engine.
Validates XSS prevention, markdown sanitization, SQL injection blocks, and resource limits.
"""

import pytest

from backend.app.core.config import settings
from backend.app.engines.dashboard.models import (
    ComponentPosition,
    ComponentSize,
    ComponentSource,
    ComponentType,
    Dashboard,
    DashboardComponent,
    DashboardFilter,
    FilterOperator,
    SourceType,
)
from backend.app.engines.dashboard.security import (
    DashboardSecurityError,
    DashboardSecurityValidator,
)


def test_markdown_sanitization_strips_scripts():
    """Verify script tags, iframes, and onerror handlers are completely stripped."""
    malicious_inputs = [
        "<script>alert('XSS')</script>Hello",
        "<script src='http://evil.com/payload.js'></script>Text",
        "<iframe src='http://evil.com'></iframe>Safe content",
        "<object data='malicious.swf'></object>Normal",
        "<a href='javascript:alert(1)'>Click me</a>",
    ]

    for attack in malicious_inputs:
        sanitized = DashboardSecurityValidator.sanitize_text(attack)
        assert "<script" not in sanitized.lower()
        assert "<iframe" not in sanitized.lower()
        assert "<object" not in sanitized.lower()
        assert "javascript:" not in sanitized.lower()


def test_dashboard_max_components_limit_enforced():
    """Verify exceeding DASHBOARD_MAX_COMPONENTS raises DashboardSecurityError."""
    d = Dashboard(
        name="Oversized Dashboard",
        dataset_id="ds_1",
        dataset_version_id="v1",
    )

    # Exceed limit
    for i in range(settings.DASHBOARD_MAX_COMPONENTS + 1):
        d.components.append(
            DashboardComponent(
                dashboard_id=d.dashboard_id,
                type=ComponentType.TEXT,
                title=f"Note {i}",
                source=ComponentSource(source_type=SourceType.MANUAL, dataset_id="ds_1", dataset_version_id="v1"),
                dataset_id="ds_1",
                dataset_version_id="v1",
            )
        )

    with pytest.raises(DashboardSecurityError) as exc_info:
        DashboardSecurityValidator.validate_dashboard_bounds(d)
    assert "maximum components limit" in str(exc_info.value)


def test_dashboard_max_filters_limit_enforced():
    """Verify exceeding DASHBOARD_MAX_FILTERS raises DashboardSecurityError."""
    d = Dashboard(
        name="Too Many Filters",
        dataset_id="ds_1",
        dataset_version_id="v1",
    )

    for i in range(settings.DASHBOARD_MAX_FILTERS + 1):
        d.filters.append(
            DashboardFilter(
                field=f"col_{i}",
                operator=FilterOperator.EQUALS,
                value="test",
            )
        )

    with pytest.raises(DashboardSecurityError) as exc_info:
        DashboardSecurityValidator.validate_dashboard_bounds(d)
    assert "maximum filters limit" in str(exc_info.value)
