"""
Tests for Phase 9 Visualization Recommendation Rules and Guardrails.
"""

import pytest
from backend.app.engines.visualization.models import (
    ChartType,
    VisualizationIntent,
)
from backend.app.engines.visualization.rules import (
    CategoricalBivariateRule,
    CategoricalComparisonRule,
    ColumnContext,
    CompositionRule,
    EvaluationContext,
    NumericDistributionRule,
    NumericRelationshipRule,
    QualityGuardrailFilter,
    TemporalTrendRule,
)


@pytest.fixture
def sales_context():
    cols = {
        "date": ColumnContext(
            name="date",
            physical_type="date",
            semantic_type="datetime",
            cardinality=30,
        ),
        "region": ColumnContext(
            name="region",
            physical_type="string",
            semantic_type="categorical",
            cardinality=4,  # low cardinality
        ),
        "product_sku": ColumnContext(
            name="product_sku",
            physical_type="string",
            semantic_type="categorical",
            cardinality=150,  # high cardinality
        ),
        "revenue": ColumnContext(
            name="revenue",
            physical_type="float64",
            semantic_type="numeric",
            cardinality=500,
            null_percentage=12.0,  # missing values
        ),
        "units": ColumnContext(
            name="units",
            physical_type="int64",
            semantic_type="numeric",
            cardinality=50,
        ),
        "transaction_id": ColumnContext(
            name="transaction_id",
            physical_type="string",
            semantic_type="id",
            cardinality=1000,
            is_identifier=True,
        ),
        "status": ColumnContext(
            name="status",
            physical_type="string",
            semantic_type="categorical",
            cardinality=1,
            is_constant=True,
        ),
    }
    return EvaluationContext(
        columns=cols,
        row_count=1000,
    )


def test_temporal_trend_rule(sales_context):
    rule = TemporalTrendRule()
    recs = rule.evaluate(sales_context)

    # Should recommend Line Chart and Area Chart
    types = [r.chart_type for r in recs]
    assert ChartType.LINE in types
    assert ChartType.AREA in types

    line_rec = next(r for r in recs if r.chart_type == ChartType.LINE)
    assert line_rec.x_field == "date"
    assert line_rec.y_field == "revenue"
    assert line_rec.confidence >= 0.90


def test_categorical_comparison_and_top_n(sales_context):
    rule = CategoricalComparisonRule()
    recs = rule.evaluate(sales_context)

    # Low cardinality (region) should recommend standard Bar Chart
    region_bar = next((r for r in recs if r.x_field == "region" and r.chart_type == ChartType.BAR), None)
    assert region_bar is not None
    assert region_bar.aggregation == "sum"

    # High cardinality (product_sku with 150 unique) should recommend Top 10 Bar Chart
    sku_bar = next((r for r in recs if r.x_field == "product_sku" and "Top 10" in r.title), None)
    assert sku_bar is not None
    assert "High cardinality" in sku_bar.warnings[0]


def test_numeric_distribution_and_relationship(sales_context):
    dist_rule = NumericDistributionRule()
    dist_recs = dist_rule.evaluate(sales_context)
    assert any(r.chart_type == ChartType.HISTOGRAM for r in dist_recs)
    assert any(r.chart_type == ChartType.BOX for r in dist_recs)

    rel_rule = NumericRelationshipRule()
    rel_recs = rel_rule.evaluate(sales_context)
    assert any(r.chart_type == ChartType.SCATTER for r in rel_recs)


def test_composition_rule_restricts_pie_to_low_cardinality(sales_context):
    comp_rule = CompositionRule()
    recs = comp_rule.evaluate(sales_context)

    # Region has 4 categories (2 <= card <= 7) -> Donut should be recommended
    donut_recs = [r for r in recs if r.chart_type == ChartType.DONUT]
    assert len(donut_recs) > 0
    assert donut_recs[0].x_field == "region"

    # Product_sku has 150 categories (> 7) -> Donut MUST NOT be recommended!
    assert not any(r.chart_type == ChartType.DONUT and r.x_field == "product_sku" for r in recs)


def test_quality_guardrails_penalizes_identifier_and_constant(sales_context):
    # If a rule erroneously suggested transaction_id or status
    from backend.app.engines.visualization.models import VisualizationRecommendation
    import uuid

    raw_recs = [
        VisualizationRecommendation(
            recommendation_id=str(uuid.uuid4()),
            chart_type=ChartType.BAR,
            title="Revenue by Transaction ID",
            reason="Test",
            confidence=0.90,
            x_field="transaction_id",
            y_field="revenue",
            required_fields=["transaction_id", "revenue"],
        ),
        VisualizationRecommendation(
            recommendation_id=str(uuid.uuid4()),
            chart_type=ChartType.BAR,
            title="Revenue by Status",
            reason="Test",
            confidence=0.85,
            x_field="status",
            y_field="revenue",
            required_fields=["status", "revenue"],
        ),
    ]

    guardrail = QualityGuardrailFilter()
    filtered = guardrail.apply(raw_recs, sales_context)

    # Confidences should be severely penalized (< 0.40) or discarded
    for r in filtered:
        if "transaction_id" in r.required_fields:
            assert r.confidence <= 0.40
            assert any("identifier" in w for w in r.warnings)
        if "status" in r.required_fields:
            assert r.confidence <= 0.40
            assert any("constant" in w for w in r.warnings)
