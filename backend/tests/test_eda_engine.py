"""
AnalyzaX — Phase 7: EDA Engine Unit & Integration Tests
Validates deterministic calculations, planners, analyzers, rule-based findings,
and visual ChartSpec generation without any external mocks or non-deterministic calls.
"""

import pytest
import polars as pl

from backend.app.engines.eda import (
    EDAEngine,
    EDAPlanner,
    FindingCategory,
)
from backend.app.engines.eda.analyzers import (
    BivariateAnalyzer,
    CardinalityAnalyzer,
    CategoricalAnalyzer,
    CorrelationAnalyzer,
    DatasetAnalyzer,
    DatetimeAnalyzer,
    MissingnessAnalyzer,
    NumericAnalyzer,
    OutliersAnalyzer,
)
from backend.app.engines.eda.chart_builder import ChartBuilder
from backend.app.engines.eda.findings import EDAFindingsEngine
from backend.app.engines.eda.models import CorrelationMethod
from backend.tests.fixtures.eda_fixture import create_eda_test_df


def test_eda_planner():
    df = create_eda_test_df()
    plan = EDAPlanner.create_plan(df, "ds_test", "v1")

    assert "age" in plan.selected_numeric_columns
    assert "income" in plan.selected_numeric_columns
    assert "orders" in plan.selected_numeric_columns
    assert "revenue" in plan.selected_numeric_columns
    assert "gender" in plan.selected_categorical_columns
    assert "signup_date" in plan.selected_datetime_columns
    assert plan.run_correlation is True
    assert plan.run_missingness is True
    assert plan.run_outliers is True


def test_numeric_analyzer():
    df = create_eda_test_df()
    res = NumericAnalyzer.analyze(df, "orders")

    assert res is not None
    assert res.column == "orders"
    assert res.count == 20
    assert res.null_count == 0
    assert res.min == 1.0
    assert res.max == 22.0
    assert res.mean is not None
    assert res.median is not None
    assert res.histogram is not None
    assert len(res.histogram.bins) > 0
    assert res.box_plot is not None


def test_categorical_analyzer():
    df = create_eda_test_df()
    res = CategoricalAnalyzer.analyze(df, "gender")

    assert res is not None
    assert res.column == "gender"
    assert res.count == 20
    assert res.unique_count == 2
    assert len(res.top_categories) == 2
    assert res.top_categories[0].count == 10
    assert res.dominant_category_percentage == 50.0


def test_datetime_analyzer():
    df = create_eda_test_df()
    res = DatetimeAnalyzer.analyze(df, "signup_date")

    assert res is not None
    assert res.column == "signup_date"
    assert res.min_timestamp == "2023-01-15"
    assert res.max_timestamp == "2023-10-31"
    assert res.span_days is not None
    assert res.span_days > 200
    assert len(res.temporal_trends) > 0


def test_correlation_analyzer():
    df = create_eda_test_df()
    corr = CorrelationAnalyzer.analyze(
        df=df,
        numeric_columns=["orders", "revenue", "age"],
        method=CorrelationMethod.PEARSON,
    )

    assert corr is not None
    assert len(corr.columns) == 3
    assert len(corr.ranked_pairs) > 0

    # Orders and Revenue have a strict linear relationship in fixture (revenue = orders * 105)
    top_pair = corr.ranked_pairs[0]
    assert {top_pair.column_x, top_pair.column_y} == {"orders", "revenue"}
    assert top_pair.correlation >= 0.99
    assert top_pair.strength == "very_strong"


def test_bivariate_numeric_numeric():
    df = create_eda_test_df()
    rel = BivariateAnalyzer.analyze_numeric_numeric(df, "orders", "revenue")

    assert rel is not None
    assert rel.correlation >= 0.99
    assert rel.regression is not None
    assert rel.regression.r_squared >= 0.99
    assert len(rel.sample_points) == 20
    assert rel.sampling.is_sampled is False


def test_bivariate_numeric_categorical():
    df = create_eda_test_df()
    rel = BivariateAnalyzer.analyze_numeric_categorical(df, "income", "gender")

    assert rel is not None
    assert len(rel.group_stats) == 2
    genders = {g.category for g in rel.group_stats}
    assert genders == {"Female", "Male"}


def test_missingness_analyzer():
    df = create_eda_test_df()
    miss = MissingnessAnalyzer.analyze(df)

    assert miss.total_missing_cells == 4  # 2 in city, 2 in income
    assert miss.complete_rows_count == 18
    assert miss.incomplete_rows_count == 2
    assert len(miss.column_missingness) > 0

    # Check city and income are top missing
    col_names = [m.column for m in miss.column_missingness[:2]]
    assert "city" in col_names
    assert "income" in col_names


def test_outliers_analyzer():
    df = create_eda_test_df()
    outliers = OutliersAnalyzer.analyze(df, ["income", "orders", "age"])

    assert outliers.total_outlier_count >= 1
    income_outlier = next((c for c in outliers.columns_with_outliers if c.column == "income"), None)
    assert income_outlier is not None
    assert income_outlier.outlier_count >= 1
    assert 450000.0 in income_outlier.sample_extreme_values


def test_cardinality_analyzer():
    df = create_eda_test_df()
    card = CardinalityAnalyzer.analyze(df)

    assert "customer_id" in card.identifier_candidates
    id_summary = next(c for c in card.columns if c.column == "customer_id")
    assert id_summary.is_identifier_candidate is True
    assert id_summary.unique_count == 20


def test_findings_engine():
    df = create_eda_test_df()
    overview = DatasetAnalyzer.analyze(df, "ds_1", "v1")
    num_res = [NumericAnalyzer.analyze(df, col) for col in ["orders", "revenue", "income"]]
    cat_res = [CategoricalAnalyzer.analyze(df, "is_active")]
    dt_res = [DatetimeAnalyzer.analyze(df, "signup_date")]
    corr = CorrelationAnalyzer.analyze(df, ["orders", "revenue"])
    rel = [BivariateAnalyzer.analyze_numeric_numeric(df, "orders", "revenue")]
    miss = MissingnessAnalyzer.analyze(df)
    outliers = OutliersAnalyzer.analyze(df, ["income"])
    card = CardinalityAnalyzer.analyze(df)

    findings = EDAFindingsEngine.generate_findings(
        overview=overview,
        numeric_analyses=[n for n in num_res if n],
        categorical_analyses=[c for c in cat_res if c],
        datetime_analyses=[d for d in dt_res if d],
        correlation=corr,
        numeric_relationships=[r for r in rel if r],
        missingness=miss,
        outliers=outliers,
        cardinality=card,
    )

    categories = {f.category for f in findings}
    assert FindingCategory.RELATIONSHIP in categories
    assert FindingCategory.ANOMALY in categories
    assert FindingCategory.CATEGORY in categories


def test_chart_builder():
    df = create_eda_test_df()
    num_res = [NumericAnalyzer.analyze(df, "age")]
    cat_res = [CategoricalAnalyzer.analyze(df, "gender")]
    dt_res = [DatetimeAnalyzer.analyze(df, "signup_date")]
    corr = CorrelationAnalyzer.analyze(df, ["age", "orders"])
    rel = [BivariateAnalyzer.analyze_numeric_numeric(df, "age", "orders")]
    miss = MissingnessAnalyzer.analyze(df)

    charts = ChartBuilder.build_all_charts(
        dataset_id="ds_1",
        version_id="v1",
        numeric_analyses=[n for n in num_res if n],
        categorical_analyses=[c for c in cat_res if c],
        datetime_analyses=[d for d in dt_res if d],
        correlation=corr,
        numeric_relationships=[r for r in rel if r],
        missingness=miss,
    )

    chart_types = {c.chart_type.value for c in charts}
    assert "histogram" in chart_types
    assert "box" in chart_types
    assert "bar" in chart_types
    assert "line" in chart_types
    assert "heatmap" in chart_types
    assert "scatter" in chart_types


def test_full_eda_engine_run():
    df = create_eda_test_df()
    report = EDAEngine.run_eda(
        df=df,
        dataset_id="test_ds_1",
        version_id="v1",
        quality_score=92.5,
    )

    assert report.report_id.startswith("eda_")
    assert report.dataset_id == "test_ds_1"
    assert report.version_id == "v1"
    assert report.overview.row_count == 20
    assert report.overview.column_count == 9
    assert report.overview.quality_score == 92.5
    assert len(report.numeric_analyses) >= 4
    assert len(report.categorical_analyses) >= 2
    assert len(report.datetime_analyses) >= 1
    assert report.correlation is not None
    assert len(report.findings) > 0
    assert len(report.charts) > 0
    assert report.computation_time_ms < 500.0
