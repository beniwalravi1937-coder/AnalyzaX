"""
Unit tests for Phase 14 Dashboard Filters, Cross-Filtering, and Analytical Safety Boundaries.
"""

import pytest

from backend.app.engines.dashboard.hydration import DashboardHydrator
from backend.app.engines.dashboard.models import (
    ComponentPosition,
    ComponentSize,
    ComponentSource,
    ComponentType,
    DashboardComponent,
    DashboardFilter,
    FilterOperator,
    FilterScope,
    SourceType,
)
from backend.app.engines.dashboard.security import (
    DashboardSecurityError,
    DashboardSecurityValidator,
)


def test_dashboard_filter_operators_valid():
    """Verify all 13 supported operators pass validation."""
    operators = [
        FilterOperator.EQUALS,
        FilterOperator.NOT_EQUALS,
        FilterOperator.IN,
        FilterOperator.NOT_IN,
        FilterOperator.GREATER_THAN,
        FilterOperator.GREATER_THAN_OR_EQUAL,
        FilterOperator.LESS_THAN,
        FilterOperator.LESS_THAN_OR_EQUAL,
        FilterOperator.BETWEEN,
        FilterOperator.CONTAINS,
        FilterOperator.STARTS_WITH,
        FilterOperator.IS_NULL,
        FilterOperator.IS_NOT_NULL,
    ]
    for op in operators:
        flt = DashboardFilter(
            field="region",
            operator=op,
            value="North",
        )
        DashboardSecurityValidator.validate_filter(flt)


def test_dashboard_filter_sql_injection_rejection():
    """Verify malicious SQL injection in field names is blocked."""
    with pytest.raises(DashboardSecurityError):
        DashboardSecurityValidator.validate_field_identifier("region; DROP TABLE users;--")

    with pytest.raises(DashboardSecurityError):
        DashboardSecurityValidator.validate_field_identifier("sales OR 1=1")


def test_statistics_filter_safety():
    """
    CRITICAL: A filter applied to a statistical result MUST NOT claim filtered statistics.
    It must flag that recomputation is required.
    """
    hydrator = DashboardHydrator()
    cmp = DashboardComponent(
        dashboard_id="dsh_1",
        type=ComponentType.STATISTICS,
        title="Two-Sample T-Test",
        configuration={
            "result": {
                "method": "Two-Sample t-test",
                "statistic": 2.45,
                "p_value": 0.018,
                "decision": "Reject Null Hypothesis",
            }
        },
        source=ComponentSource(
            source_type=SourceType.STATISTICAL_RESULT,
            dataset_id="ds_1",
            dataset_version_id="v1",
            engine="statistics",
        ),
        dataset_id="ds_1",
        dataset_version_id="v1",
    )

    # 1. Without filters -> READY, no recomputation needed
    resp_unfiltered = hydrator.hydrate_single_component(cmp, None, filters=[])
    assert resp_unfiltered.requires_recomputation is False

    # 2. With filters -> requires_recomputation is TRUE with explanation
    resp_filtered = hydrator.hydrate_single_component(
        cmp,
        None,
        filters=[DashboardFilter(field="region", operator=FilterOperator.EQUALS, value="South")],
    )
    assert resp_filtered.requires_recomputation is True
    assert "Filtering this view changes the analysis population" in resp_filtered.recomputation_reason


def test_ml_result_filter_safety():
    """
    CRITICAL: Filtering an ML result does not automatically retrain the model.
    Model metrics remain tied to the certified experiment.
    """
    hydrator = DashboardHydrator()
    cmp = DashboardComponent(
        dashboard_id="dsh_1",
        type=ComponentType.ML_RESULT,
        title="Random Forest Classifier",
        configuration={
            "result": {
                "model_type": "Random Forest",
                "primary_metric": "f1_score",
                "metric_value": 0.89,
            }
        },
        source=ComponentSource(
            source_type=SourceType.ML_RESULT,
            dataset_id="ds_1",
            dataset_version_id="v1",
            engine="ml",
        ),
        dataset_id="ds_1",
        dataset_version_id="v1",
    )

    resp_filtered = hydrator.hydrate_single_component(
        cmp,
        None,
        filters=[DashboardFilter(field="channel", operator=FilterOperator.EQUALS, value="Web")],
    )
    assert resp_filtered.requires_recomputation is True
    assert "training/evaluation experiment" in resp_filtered.recomputation_reason


def test_forecasting_filter_safety():
    """
    CRITICAL: Filtering forecast components does not silently invent new forecasts.
    """
    hydrator = DashboardHydrator()
    cmp = DashboardComponent(
        dashboard_id="dsh_1",
        type=ComponentType.FORECAST,
        title="6-Month Sales Forecast",
        configuration={
            "result": {
                "model_id": "fc_arima_01",
                "horizon": 6,
                "metrics": {"mape": 4.2},
            }
        },
        source=ComponentSource(
            source_type=SourceType.FORECAST_RESULT,
            dataset_id="ds_1",
            dataset_version_id="v1",
            engine="forecasting",
        ),
        dataset_id="ds_1",
        dataset_version_id="v1",
    )

    resp_filtered = hydrator.hydrate_single_component(
        cmp,
        None,
        filters=[DashboardFilter(field="category", operator=FilterOperator.EQUALS, value="Electronics")],
    )
    assert resp_filtered.requires_recomputation is True
    assert "alter the generated forecast horizon" in resp_filtered.recomputation_reason
