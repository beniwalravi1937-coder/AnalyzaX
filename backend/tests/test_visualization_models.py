"""
Tests for Phase 9 Visualization Models and ChartSpec Contract.
"""

import pytest
from backend.app.engines.visualization.models import (
    AggregationType,
    ChartAxesConfig,
    ChartEncoding,
    ChartSpec,
    ChartType,
    SortBy,
    SortDirection,
    StructuredFilter,
    VisualizationIntent,
    VisualizationProvenance,
    VisualizationRecommendation,
)


def test_chart_spec_creation_and_defaults():
    spec = ChartSpec(
        chart_id="test_chart_1",
        chart_type=ChartType.BAR,
        title="Revenue by Region",
        dataset_id="ds_123",
        dataset_version_id="v1",
        x="region",
        y="revenue",
        aggregation="sum",
    )

    assert spec.spec_version == "v1"
    assert spec.chart_type == ChartType.BAR
    assert spec.x == "region"
    assert spec.y == "revenue"
    assert spec.aggregation == "sum"
    assert spec.axes.zero_baseline is True
    assert spec.axes.show_grid is True
    assert spec.interactions.zoom is True


def test_structured_filter_model():
    filt = StructuredFilter(
        field="revenue",
        operator="greater_than_or_equal",
        value=1000.0,
    )
    assert filt.field == "revenue"
    assert filt.operator == "greater_than_or_equal"
    assert filt.value == 1000.0

    between_filt = StructuredFilter(
        field="date",
        operator="between",
        value="2026-01-01",
        value2="2026-01-31",
    )
    assert between_filt.value2 == "2026-01-31"


def test_recommendation_model():
    rec = VisualizationRecommendation(
        recommendation_id="rec_1",
        chart_type=ChartType.LINE,
        title="Revenue Trend",
        reason="Temporal trends over date",
        confidence=0.95,
        x_field="date",
        y_field="revenue",
        required_fields=["date", "revenue"],
        priority=1,
        intent="trend",
    )
    assert rec.confidence == 0.95
    assert rec.priority == 1
    assert "date" in rec.required_fields
