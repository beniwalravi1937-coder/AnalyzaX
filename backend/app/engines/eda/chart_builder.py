"""
AnalyzaX — Phase 7: Chart Builder
Converts analytical summaries, distributions, correlations, and relationships
into standardized, strongly-typed ChartSpec specifications for the frontend.
"""

from typing import List, Optional

from backend.app.engines.eda.models import (
    ChartOptions,
    ChartSpec,
    ChartType,
    CorrelationMatrix,
    DatetimeAnalysis,
    MissingnessAnalysis,
    NumericCategoricalRelationship,
    NumericNumericRelationship,
    UnivariateCategorical,
    UnivariateNumeric,
)


class ChartBuilder:
    @staticmethod
    def build_all_charts(
        dataset_id: str,
        version_id: str,
        numeric_analyses: List[UnivariateNumeric],
        categorical_analyses: List[UnivariateCategorical],
        datetime_analyses: List[DatetimeAnalysis],
        correlation: Optional[CorrelationMatrix],
        numeric_relationships: List[NumericNumericRelationship],
        missingness: Optional[MissingnessAnalysis],
    ) -> List[ChartSpec]:
        charts: List[ChartSpec] = []

        # 1. Numeric Histograms and Box Plots
        for num in numeric_analyses:
            if num.histogram and num.histogram.bins:
                hist_data = [
                    {
                        "bin_start": b.bin_start,
                        "bin_end": b.bin_end,
                        "count": b.count,
                        "percentage": b.percentage,
                    }
                    for b in num.histogram.bins
                ]
                charts.append(
                    ChartSpec(
                        chart_id=f"hist_{num.column}",
                        chart_type=ChartType.HISTOGRAM,
                        title=f"Distribution of {num.column}",
                        description=f"{num.distribution_shape.replace('_', ' ').capitalize()} distribution ({num.histogram.bin_method} bins)",
                        dataset_id=dataset_id,
                        version_id=version_id,
                        x=num.column,
                        y="count",
                        data=hist_data,
                        options=ChartOptions(
                            x_axis_label=num.column,
                            y_axis_label="Frequency",
                            bin_count=num.histogram.bin_count,
                            bin_method=num.histogram.bin_method,
                        ),
                    )
                )

            if num.box_plot:
                box_data = [
                    {
                        "column": num.column,
                        "min": num.box_plot.min,
                        "q1": num.box_plot.q1,
                        "median": num.box_plot.median,
                        "q3": num.box_plot.q3,
                        "max": num.box_plot.max,
                        "iqr": num.box_plot.iqr,
                        "outlier_points": num.box_plot.outlier_points,
                    }
                ]
                charts.append(
                    ChartSpec(
                        chart_id=f"box_{num.column}",
                        chart_type=ChartType.BOX,
                        title=f"Box Plot: {num.column}",
                        description=f"Median: {num.box_plot.median}, IQR: {num.box_plot.iqr} ({len(num.box_plot.outlier_points)} outliers)",
                        dataset_id=dataset_id,
                        version_id=version_id,
                        x=num.column,
                        data=box_data,
                        options=ChartOptions(
                            x_axis_label=num.column,
                            y_axis_label="Value",
                        ),
                    )
                )

        # 2. Categorical Bar Charts
        for cat in categorical_analyses:
            if cat.top_categories:
                bar_data = [
                    {
                        "category": item.category,
                        "count": item.count,
                        "percentage": item.percentage,
                    }
                    for item in cat.top_categories
                ]
                charts.append(
                    ChartSpec(
                        chart_id=f"bar_{cat.column}",
                        chart_type=ChartType.BAR,
                        title=f"Frequency: {cat.column}",
                        description=f"{cat.cardinality_class.value} cardinality ({cat.unique_count} unique)",
                        dataset_id=dataset_id,
                        version_id=version_id,
                        x=cat.column,
                        y="count",
                        data=bar_data,
                        options=ChartOptions(
                            x_axis_label=cat.column,
                            y_axis_label="Count",
                        ),
                    )
                )

        # 3. Datetime Trend Lines
        for dt in datetime_analyses:
            if dt.temporal_trends:
                line_data = [
                    {
                        "timestamp": pt.timestamp,
                        "count": pt.count,
                        "period": pt.period,
                    }
                    for pt in dt.temporal_trends
                ]
                charts.append(
                    ChartSpec(
                        chart_id=f"line_{dt.column}",
                        chart_type=ChartType.LINE,
                        title=f"Timeline: {dt.column}",
                        description=f"Span: {dt.span_days:.0f} days (Inferred frequency: {dt.inferred_frequency})",
                        dataset_id=dataset_id,
                        version_id=version_id,
                        x="timestamp",
                        y="count",
                        data=line_data,
                        options=ChartOptions(
                            x_axis_label="Date / Time",
                            y_axis_label="Record Count",
                        ),
                    )
                )

        # 4. Correlation Heatmap
        if correlation and len(correlation.columns) >= 2:
            heatmap_data = []
            cols = correlation.columns
            for i in range(len(cols)):
                for j in range(len(cols)):
                    val = correlation.matrix[i][j]
                    heatmap_data.append({
                        "x": cols[i],
                        "y": cols[j],
                        "value": val,
                    })

            charts.append(
                ChartSpec(
                    chart_id="corr_heatmap",
                    chart_type=ChartType.HEATMAP,
                    title=f"Correlation Matrix ({correlation.method.value.capitalize()})",
                    description="Pairwise correlation coefficients across numeric features",
                    dataset_id=dataset_id,
                    version_id=version_id,
                    x="x",
                    y="y",
                    data=heatmap_data,
                    options=ChartOptions(
                        show_legend=True,
                    ),
                )
            )

        # 5. Numeric Scatter Plots (Top Relationships)
        for rel in numeric_relationships[:10]:
            pts = [{"x": pt.x, "y": pt.y} for pt in rel.sample_points]
            regr_info = (
                f", R²={rel.regression.r_squared:.2f}"
                if rel.regression
                else ""
            )
            charts.append(
                ChartSpec(
                    chart_id=f"scatter_{rel.column_x}_{rel.column_y}",
                    chart_type=ChartType.SCATTER,
                    title=f"{rel.column_x} vs {rel.column_y}",
                    description=f"Pearson r = {rel.correlation:+.2f}{regr_info}",
                    dataset_id=dataset_id,
                    version_id=version_id,
                    x=rel.column_x,
                    y=rel.column_y,
                    data=pts,
                    options=ChartOptions(
                        x_axis_label=rel.column_x,
                        y_axis_label=rel.column_y,
                    ),
                    sampling=rel.sampling,
                )
            )

        # 6. Missingness Bar Chart
        if missingness:
            missing_cols = [
                {"column": m.column, "missing_percentage": m.missing_percentage, "missing_count": m.missing_count}
                for m in missingness.column_missingness
                if m.missing_count > 0
            ]
            if missing_cols:
                charts.append(
                    ChartSpec(
                        chart_id="missingness_bars",
                        chart_type=ChartType.BAR,
                        title="Missing Values by Column (%)",
                        description=f"Overall missingness: {missingness.overall_missing_percentage}% ({missingness.incomplete_rows_count} incomplete rows)",
                        dataset_id=dataset_id,
                        version_id=version_id,
                        x="column",
                        y="missing_percentage",
                        data=missing_cols,
                        options=ChartOptions(
                            x_axis_label="Column",
                            y_axis_label="Missing %",
                        ),
                    )
                )

        return charts
