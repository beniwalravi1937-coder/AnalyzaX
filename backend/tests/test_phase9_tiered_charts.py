"""
Phase 9 Tiered Chart Support Verification Tests (VIZ-T01 through VIZ-T10)

Tests:
- VIZ-T01: Complete Tier 1 Chart Types registered and supported.
- VIZ-T02: Tier 1 Recommendation Rules generate deterministic recommendations.
- VIZ-T03: Tier 1 Validation, Preview, and Data Preparation.
- VIZ-T04: Tier 2 Advanced Charts reuse the exact same ChartSpec and validator.
- VIZ-T05: Tier 3 Specialized Charts registered with capability metadata and marked deferred.
- VIZ-T06: Tier Hierarchy & Complexity Guardrails (Histogram > Boxplot > Violin; Bar > Pie/Donut).
- VIZ-T07: Analytical Suitability takes precedence over chart tier.
- VIZ-T08: Centralized Chart Registry exposed via API.
- VIZ-T09: Unsupported Chart Types clearly rejected with UNSUPPORTED_CHART_TIER.
- VIZ-T10: Extensibility of Central Registry without changing unrelated engines.
"""

import pytest
import polars as pl
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.engines.visualization.models import (
    AggregationType,
    ChartSpec,
    ChartType,
    VisualizationIntent,
)
from backend.app.engines.visualization.registry import (
    CHART_REGISTRY,
    ChartTier,
    ChartTypeDefinition,
    get_chart_definition,
    is_chart_supported,
    list_charts_by_tier,
)
from backend.app.engines.visualization.recommender import (
    ColumnContext,
    VisualizationRecommender,
)
from backend.app.engines.visualization.validation import ChartSpecValidator
from backend.app.engines.visualization.data_preparer import VisualizationDataPreparer


def test_viz_t01_tier_1_core_charts_registered():
    """
    VIZ-T01: Verify all mandatory Tier 1 Core Production charts are registered,
    marked as supported, and have valid required encodings.
    """
    tier1_types = [
        "bar",
        "horizontal_bar",
        "grouped_bar",
        "stacked_bar",
        "percent_stacked_bar",
        "line",
        "multi_line",
        "area",
        "stacked_area",
        "scatter",
        "histogram",
        "box",
        "heatmap",
        "correlation_matrix",
        "kpi",
        "table",
    ]

    tier1_defs = list_charts_by_tier(ChartTier.TIER_1_CORE)
    registered_keys = [d.chart_type for d in tier1_defs]

    for expected in tier1_types:
        assert expected in registered_keys, f"Tier 1 chart '{expected}' missing from registry"
        defn = get_chart_definition(expected)
        assert defn is not None
        assert defn.tier == ChartTier.TIER_1_CORE
        assert defn.is_supported is True
        assert len(defn.supported_encodings) > 0
        assert len(defn.supported_data_types) > 0


def test_viz_t02_tier_1_deterministic_recommendations():
    """
    VIZ-T02: Verify Tier 1 charts are deterministically recommended
    for their matching analytical signatures.
    """
    recommender = VisualizationRecommender()

    # 1. Single numeric -> Histogram & Box Plot (Tier 1)
    cols_num = {
        "age": ColumnContext(
            name="age",
            physical_type="int64",
            semantic_type="numeric",
            cardinality=70,
            null_count=0,
            null_percentage=0.0,
            min_value=18.0,
            max_value=90.0,
            mean=45.0,
            std=15.0,
        )
    }
    recs_num = recommender.recommend(columns=cols_num, row_count=500)
    chart_types = [r.chart_type.value for r in recs_num]
    assert "histogram" in chart_types
    assert "box" in chart_types

    # 2. Categorical + Numeric -> Bar (Tier 1)
    cols_cat_num = {
        "department": ColumnContext(
            name="department",
            physical_type="string",
            semantic_type="categorical",
            cardinality=6,
            null_count=0,
            null_percentage=0.0,
        ),
        "salary": ColumnContext(
            name="salary",
            physical_type="float64",
            semantic_type="numeric",
            cardinality=450,
            null_count=0,
            null_percentage=0.0,
        ),
    }
    recs_cat = recommender.recommend(columns=cols_cat_num, row_count=500)
    assert any(r.chart_type.value == "bar" for r in recs_cat)

    # 3. Two continuous numerics -> Scatter (Tier 1)
    cols_scatter = {
        "height": ColumnContext(
            name="height",
            physical_type="float64",
            semantic_type="numeric",
            cardinality=200,
        ),
        "weight": ColumnContext(
            name="weight",
            physical_type="float64",
            semantic_type="numeric",
            cardinality=220,
        ),
    }
    recs_scatter = recommender.recommend(columns=cols_scatter, row_count=500)
    assert any(r.chart_type.value == "scatter" for r in recs_scatter)


def test_viz_t03_tier_1_validation_and_data_prep(tmp_path):
    """
    VIZ-T03: Verify Tier 1 charts pass validation and execute server-side data preparation.
    """
    validator = ChartSpecValidator()
    preparer = VisualizationDataPreparer()

    df = pl.DataFrame({
        "category": ["A", "B", "C", "A", "B"],
        "amount": [10.0, 20.0, 30.0, 15.0, 25.0],
    })
    p_path = str(tmp_path / "test_data.parquet")
    df.write_parquet(p_path)

    spec = ChartSpec(
        chart_id="t1_bar_test",
        chart_type=ChartType.BAR,
        title="Amount by Category",
        dataset_id="ds_1",
        dataset_version_id="v1",
        x="category",
        y="amount",
        aggregation="sum",
    )

    val_res = validator.validate(spec, schema_columns={"category": "string", "amount": "float64"})
    assert val_res.is_valid is True

    prepared_spec = preparer.prepare_data(p_path, spec)
    assert prepared_spec.data is not None
    assert len(prepared_spec.data) == 3
    cat_map = {row["x"]: row["y"] for row in prepared_spec.data}
    assert cat_map["A"] == 25.0
    assert cat_map["B"] == 45.0
    assert cat_map["C"] == 30.0


def test_viz_t04_tier_2_advanced_charts_use_unified_engine():
    """
    VIZ-T04: Verify Tier 2 advanced charts (Donut, Treemap, Bubble, Violin)
    reuse the exact same ChartSpec, validation, and registry engine.
    """
    tier2_types = ["donut", "treemap", "bubble", "violin", "pareto", "waterfall", "funnel"]
    for t2 in tier2_types:
        defn = get_chart_definition(t2)
        assert defn is not None, f"Tier 2 chart '{t2}' missing from registry"
        assert defn.tier == ChartTier.TIER_2_ADVANCED
        assert defn.is_supported is True

    validator = ChartSpecValidator()
    # Test valid Donut spec
    donut_spec = ChartSpec(
        chart_id="t2_donut",
        chart_type=ChartType.DONUT,
        title="Proportions",
        dataset_id="ds_1",
        dataset_version_id="v1",
        x="status",
        y="count",
        aggregation="sum",
    )
    res = validator.validate(donut_spec, schema_columns={"status": "string", "count": "int64"})
    assert res.is_valid is True


def test_viz_t05_tier_3_specialized_charts_registered_as_deferred():
    """
    VIZ-T05: Verify Tier 3 specialized charts (Sankey, Radar, Candlestick, Maps)
    are registered with capability metadata, but marked is_supported=False in Phase 9.
    """
    tier3_types = ["sankey", "radar", "candlestick", "choropleth"]
    for t3 in tier3_types:
        defn = get_chart_definition(t3)
        assert defn is not None, f"Tier 3 chart '{t3}' missing from registry"
        assert defn.tier == ChartTier.TIER_3_SPECIALIZED
        assert defn.is_supported is False
        assert defn.recommendation_priority <= 20


def test_viz_t06_t07_analytical_suitability_and_hierarchy():
    """
    VIZ-T06 & VIZ-T07:
    Verify recommendation order prioritizes analytical suitability and tier:
    - Numeric distribution: Histogram [Tier 1] > Box Plot [Tier 1] > Violin [Tier 2]
    - Categorical comparison: Bar [Tier 1] > Donut [Tier 2]
    The system must NOT recommend Violin over Histogram merely for complexity.
    """
    recommender = VisualizationRecommender()

    # 1. Test Distribution Hierarchy
    cols_dist = {
        "score": ColumnContext(
            name="score",
            physical_type="float64",
            semantic_type="numeric",
            cardinality=100,
        )
    }
    recs_dist = recommender.recommend(
        columns=cols_dist,
        row_count=500,
        intent=VisualizationIntent.DISTRIBUTION,
    )

    types_ordered = [r.chart_type.value for r in recs_dist]
    assert "histogram" in types_ordered
    assert "box" in types_ordered
    assert "violin" in types_ordered

    hist_idx = types_ordered.index("histogram")
    box_idx = types_ordered.index("box")
    violin_idx = types_ordered.index("violin")

    # Histogram outranks Box Plot, and Box Plot outranks Violin
    assert hist_idx < box_idx < violin_idx
    # Verify tiers
    hist_rec = next(r for r in recs_dist if r.chart_type.value == "histogram")
    box_rec = next(r for r in recs_dist if r.chart_type.value == "box")
    violin_rec = next(r for r in recs_dist if r.chart_type.value == "violin")
    assert hist_rec.tier == 1
    assert box_rec.tier == 1
    assert violin_rec.tier == 2

    # 2. Test Categorical Comparison Hierarchy
    cols_comp = {
        "tier_name": ColumnContext(
            name="tier_name",
            physical_type="string",
            semantic_type="categorical",
            cardinality=4,
        ),
        "count": ColumnContext(
            name="count",
            physical_type="int64",
            semantic_type="numeric",
            cardinality=4,
        ),
    }
    recs_comp = recommender.recommend(
        columns=cols_comp,
        row_count=100,
        intent=VisualizationIntent.COMPARISON,
    )
    comp_types = [r.chart_type.value for r in recs_comp]
    bar_idx = comp_types.index("bar")
    donut_idx = comp_types.index("donut")
    # Bar Chart (Tier 1) strictly outranks Donut (Tier 2) for comparison
    assert bar_idx < donut_idx


def test_viz_t08_t09_registry_api_and_unsupported_tier_validation():
    """
    VIZ-T08 & VIZ-T09:
    - Centralized registry exposes all definitions and capability flags.
    - Unsupported chart types are rejected with UNSUPPORTED_CHART_TIER.
    """
    validator = ChartSpecValidator()

    # Attempt to validate a Tier 3 chart (Sankey)
    sankey_spec = ChartSpec(
        chart_id="unsupported_sankey",
        chart_type=ChartType.SANKEY,
        title="Flows",
        dataset_id="ds_1",
        dataset_version_id="v1",
        x="source",
        y="target",
    )
    res = validator.validate(sankey_spec)
    assert res.is_valid is False
    assert any(e.code == "UNSUPPORTED_CHART_TIER" for e in res.errors)
    assert "specialized chart whose renderer is deferred" in res.errors[0].message


@pytest.mark.asyncio
async def test_viz_t08_registry_api_endpoint():
    """
    VIZ-T08: Verify GET /api/v1/visualizations/registry returns full list of definitions.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/visualizations/registry")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 20
        # Check that definitions include tier, display_name, required_encodings
        first = data[0]
        assert "chart_type" in first
        assert "tier" in first
        assert "display_name" in first
        assert "required_encodings" in first
        assert "is_supported" in first

        # Test filtering by tier
        tier1_resp = await client.get("/api/v1/visualizations/registry?tier=1")
        assert tier1_resp.status_code == 200
        tier1_data = tier1_resp.json()
        assert all(d["tier"] == 1 for d in tier1_data)
        assert len(tier1_data) >= 16


def test_viz_t10_extensibility_without_modifying_unrelated_code():
    """
    VIZ-T10: Adding a new chart type to the registry is isolated and does not
    require altering validators or other core engines.
    """
    # Temporarily register a custom chart definition
    custom_def = ChartTypeDefinition(
        chart_type="custom_contour",
        tier=ChartTier.TIER_2_ADVANCED,
        display_name="Custom Contour",
        description="2D density contour map.",
        family="distribution",
        supported_encodings=["x", "y"],
        required_encodings=["x", "y"],
        optional_encodings=[],
        supported_data_types=["numeric"],
        supported_intents=["distribution"],
        is_supported=True,
        recommendation_priority=25,
    )

    CHART_REGISTRY["custom_contour"] = custom_def
    try:
        # Check that get_chart_definition recognizes it
        found = get_chart_definition("custom_contour")
        assert found is not None
        assert found.display_name == "Custom Contour"

        # Check that validator accepts valid encodings for this new chart
        validator = ChartSpecValidator()
        spec = ChartSpec(
            chart_id="custom_1",
            chart_type="custom_contour",
            title="Density Contours",
            dataset_id="ds_1",
            dataset_version_id="v1",
            x="feature_a",
            y="feature_b",
        )
        res = validator.validate(spec, schema_columns={"feature_a": "float64", "feature_b": "float64"})
        assert res.is_valid is True

        # Check that missing required encoding fails validation automatically
        invalid_spec = ChartSpec(
            chart_id="custom_invalid",
            chart_type="custom_contour",
            title="Density Contours",
            dataset_id="ds_1",
            dataset_version_id="v1",
            x="feature_a",
        )
        res_inv = validator.validate(invalid_spec, schema_columns={"feature_a": "float64"})
        assert res_inv.is_valid is False
        assert any(e.code == "MISSING_REQUIRED_ENCODING" for e in res_inv.errors)
    finally:
        # Cleanup
        CHART_REGISTRY.pop("custom_contour", None)
