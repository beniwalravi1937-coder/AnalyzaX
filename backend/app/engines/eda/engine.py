"""
AnalyzaX — Phase 7: Automated EDA Engine
Top-level domain engine that coordinates planner, analyzers, findings, and chart builders.
Strictly deterministic, zero-LLM calculation, completely independent of the presentation layer.
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import polars as pl

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
from backend.app.engines.eda.models import (
    ChartOptions,
    ChartSpec,
    ChartType,
    CorrelationMethod,
    EDAReport,
    NumericCategoricalRelationship,
    NumericNumericRelationship,
    RelationshipQueryResponse,
)
from backend.app.engines.eda.planner import EDAPlanner


class EDAEngine:
    """
    Coordinates end-to-end automated exploratory data analysis for a dataset version.
    """

    @classmethod
    def run_eda(
        cls,
        df: pl.DataFrame,
        dataset_id: str,
        version_id: str,
        quality_score: Optional[float] = None,
        anomalies_count: int = 0,
        storage_size_bytes: Optional[int] = None,
        profile_timestamp: Optional[str] = None,
        quality_timestamp: Optional[str] = None,
    ) -> EDAReport:
        start_time = time.perf_counter()

        # 1. Create Bounded Analysis Plan
        plan = EDAPlanner.create_plan(df, dataset_id, version_id)

        # 2. Dataset Overview
        overview = DatasetAnalyzer.analyze(
            df=df,
            dataset_id=dataset_id,
            version_id=version_id,
            quality_score=quality_score,
            anomalies_count=anomalies_count,
            storage_size_bytes=storage_size_bytes,
            profile_timestamp=profile_timestamp,
            quality_timestamp=quality_timestamp,
        )

        # 3. Univariate Numeric Analyses
        numeric_analyses = []
        for col in plan.selected_numeric_columns:
            res = NumericAnalyzer.analyze(df, col)
            if res:
                numeric_analyses.append(res)

        # 4. Univariate Categorical Analyses
        categorical_analyses = []
        for col in plan.selected_categorical_columns:
            res = CategoricalAnalyzer.analyze(df, col)
            if res:
                categorical_analyses.append(res)

        # 5. Datetime Analyses
        datetime_analyses = []
        for col in plan.selected_datetime_columns:
            res = DatetimeAnalyzer.analyze(df, col)
            if res:
                datetime_analyses.append(res)

        # 6. Correlation Analysis
        correlation = None
        if plan.run_correlation and len(plan.selected_numeric_columns) >= 2:
            correlation = CorrelationAnalyzer.analyze(
                df=df,
                numeric_columns=plan.selected_numeric_columns,
                method=CorrelationMethod.PEARSON,
            )

        # 7. Bivariate Analyses
        numeric_relationships: List[NumericNumericRelationship] = []
        for pair in plan.selected_numeric_pairs:
            col_x, col_y = pair[0], pair[1]
            rel = BivariateAnalyzer.analyze_numeric_numeric(
                df=df,
                col_x=col_x,
                col_y=col_y,
                max_sample_points=plan.max_scatter_points,
            )
            if rel:
                numeric_relationships.append(rel)

        num_cat_relationships: List[NumericCategoricalRelationship] = []
        for pair in plan.selected_num_cat_pairs:
            num_c, cat_c = pair[0], pair[1]
            rel = BivariateAnalyzer.analyze_numeric_categorical(
                df=df,
                num_col=num_c,
                cat_col=cat_c,
            )
            if rel:
                num_cat_relationships.append(rel)

        # 8. Missingness Analysis
        missingness = None
        if plan.run_missingness:
            missingness = MissingnessAnalyzer.analyze(df)

        # 9. Outlier Analysis
        outliers = None
        if plan.run_outliers and plan.selected_numeric_columns:
            outliers = OutliersAnalyzer.analyze(df, plan.selected_numeric_columns)

        # 10. Cardinality Analysis
        cardinality = CardinalityAnalyzer.analyze(df)

        # 11. Findings Generation
        findings = EDAFindingsEngine.generate_findings(
            overview=overview,
            numeric_analyses=numeric_analyses,
            categorical_analyses=categorical_analyses,
            datetime_analyses=datetime_analyses,
            correlation=correlation,
            numeric_relationships=numeric_relationships,
            missingness=missingness,
            outliers=outliers,
            cardinality=cardinality,
        )

        # 12. ChartSpec Visual Specifications
        charts = ChartBuilder.build_all_charts(
            dataset_id=dataset_id,
            version_id=version_id,
            numeric_analyses=numeric_analyses,
            categorical_analyses=categorical_analyses,
            datetime_analyses=datetime_analyses,
            correlation=correlation,
            numeric_relationships=numeric_relationships,
            missingness=missingness,
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        report_id = f"eda_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        return EDAReport(
            report_id=report_id,
            dataset_id=dataset_id,
            version_id=version_id,
            eda_version="eda_v1",
            generated_at=now_iso,
            computation_time_ms=elapsed_ms,
            overview=overview,
            numeric_analyses=numeric_analyses,
            categorical_analyses=categorical_analyses,
            datetime_analyses=datetime_analyses,
            correlation=correlation,
            numeric_relationships=numeric_relationships,
            num_cat_relationships=num_cat_relationships,
            cat_cat_relationships=[],
            missingness=missingness,
            outliers=outliers,
            cardinality=cardinality,
            findings=findings,
            charts=charts,
        )

    @classmethod
    def analyze_interactive_relationship(
        cls,
        df: pl.DataFrame,
        col_x: str,
        col_y: str,
        dataset_id: str,
        version_id: str,
    ) -> RelationshipQueryResponse:
        """
        Dynamically analyzes any arbitrary pair of columns on request.
        """
        if col_x not in df.columns or col_y not in df.columns:
            raise ValueError(f"Columns {col_x} or {col_y} not found in dataset.")

        dtype_x = df[col_x].dtype
        dtype_y = df[col_y].dtype

        is_num_x = dtype_x.is_numeric()
        is_num_y = dtype_y.is_numeric()
        is_temporal_x = dtype_x.is_temporal()

        summary: Dict[str, Any] = {}
        chart: Optional[ChartSpec] = None
        rel_type = "unknown"

        if is_num_x and is_num_y:
            rel_type = "numeric_numeric"
            rel = BivariateAnalyzer.analyze_numeric_numeric(df, col_x, col_y, max_sample_points=1000)
            if rel:
                summary = {
                    "correlation": rel.correlation,
                    "regression": rel.regression.model_dump() if rel.regression else None,
                    "sample_points_count": len(rel.sample_points),
                }
                chart = ChartSpec(
                    chart_id=f"scatter_{col_x}_{col_y}",
                    chart_type=ChartType.SCATTER,
                    title=f"{col_x} vs {col_y}",
                    description=f"Pearson r = {rel.correlation:+.2f}",
                    dataset_id=dataset_id,
                    version_id=version_id,
                    x=col_x,
                    y=col_y,
                    data=[{"x": p.x, "y": p.y} for p in rel.sample_points],
                    options=ChartOptions(x_axis_label=col_x, y_axis_label=col_y),
                    sampling=rel.sampling,
                )

        elif (is_num_x and not is_num_y) or (not is_num_x and is_num_y):
            rel_type = "numeric_categorical"
            num_c = col_x if is_num_x else col_y
            cat_c = col_y if is_num_x else col_x
            num_cat_rel = BivariateAnalyzer.analyze_numeric_categorical(df, num_c, cat_c)
            if num_cat_rel:
                summary = {
                    "numeric_column": num_c,
                    "categorical_column": cat_c,
                    "variance_across_groups": num_cat_rel.variance_across_groups,
                    "groups_count": len(num_cat_rel.group_stats),
                }
                chart = ChartSpec(
                    chart_id=f"bar_{cat_c}_{num_c}",
                    chart_type=ChartType.BAR,
                    title=f"Mean {num_c} by {cat_c}",
                    dataset_id=dataset_id,
                    version_id=version_id,
                    x=cat_c,
                    y="mean",
                    data=[
                        {"category": g.category, "mean": g.mean, "median": g.median, "count": g.count}
                        for g in num_cat_rel.group_stats
                    ],
                    options=ChartOptions(x_axis_label=cat_c, y_axis_label=f"Mean {num_c}"),
                )

        elif not is_num_x and not is_num_y:
            rel_type = "categorical_categorical"
            cat_cat_rel = BivariateAnalyzer.analyze_categorical_categorical(df, col_x, col_y)
            if cat_cat_rel:
                summary = {
                    "cramers_v": cat_cat_rel.cramers_v,
                    "categories_x": cat_cat_rel.categories_x,
                    "categories_y": cat_cat_rel.categories_y,
                }
                # Create contingency heatmap data
                heatmap_data = []
                for i, x_val in enumerate(cat_cat_rel.categories_x):
                    for j, y_val in enumerate(cat_cat_rel.categories_y):
                        cnt = cat_cat_rel.contingency_matrix[i][j]
                        heatmap_data.append({"x": x_val, "y": y_val, "value": cnt})
                chart = ChartSpec(
                    chart_id=f"contingency_{col_x}_{col_y}",
                    chart_type=ChartType.HEATMAP,
                    title=f"Contingency: {col_x} vs {col_y}",
                    description=f"Cramér's V = {cat_cat_rel.cramers_v or 0.0:.2f}",
                    dataset_id=dataset_id,
                    version_id=version_id,
                    x=col_x,
                    y=col_y,
                    data=heatmap_data,
                )

        return RelationshipQueryResponse(
            column_x=col_x,
            column_y=col_y,
            relationship_type=rel_type,
            summary=summary,
            chart=chart,
            findings=[],
        )
