"""
AnalyzaX — Phase 8: Result Set Chart Advisor
Inspects SQL result column types and distributions to automatically generate
rich, interactive ChartSpec visualizations using the existing SVG rendering engine.
"""

from typing import Any, Dict, List, Optional
from backend.app.engines.eda.models import (
    ChartOptions,
    ChartSamplingMetadata,
    ChartSpec,
    ChartType,
)
from backend.app.engines.sql.models import SQLColumnDescriptor


class SQLChartAdvisor:
    """
    Recommends and constructs ChartSpec specifications from SQL execution results.
    """

    @classmethod
    def advise(
        cls,
        dataset_id: str,
        version_id: str,
        columns: List[SQLColumnDescriptor],
        rows: List[Dict[str, Any]],
        limit_data: int = 50,
    ) -> List[ChartSpec]:
        """
        Produces 1 to 3 relevant chart specifications based on column signatures.
        """
        if not rows or not columns or len(rows) < 2:
            return []

        specs: List[ChartSpec] = []
        num_cols = [c.name for c in columns if c.semantic_type == "numeric"]
        cat_cols = [c.name for c in columns if c.semantic_type == "categorical"]
        date_cols = [c.name for c in columns if c.semantic_type == "datetime"]

        # Subsample data points if row count is large
        data_sample = rows[:limit_data]
        is_sampled = len(rows) > limit_data
        sampling_meta = ChartSamplingMetadata(
            is_sampled=is_sampled,
            original_row_count=len(rows),
            displayed_points=len(data_sample),
            sampling_method="top_rows",
        )

        # Pattern 1: 1 Categorical + 1 Numeric -> Bar Chart
        if cat_cols and num_cols:
            c_name = cat_cols[0]
            n_name = num_cols[0]
            bar_data = [
                {"category": str(r.get(c_name, "Unknown")), "value": r.get(n_name, 0)}
                for r in data_sample
                if r.get(c_name) is not None
            ]
            specs.append(
                ChartSpec(
                    chart_id=f"sql_bar_{c_name}_{n_name}",
                    chart_type=ChartType.BAR,
                    title=f"{n_name} by {c_name}",
                    description=f"Bar chart visualizing {n_name} across distinct {c_name} values",
                    dataset_id=dataset_id,
                    version_id=version_id,
                    x="category",
                    y="value",
                    data=bar_data,
                    options=ChartOptions(
                        show_legend=False,
                        x_axis_label=c_name,
                        y_axis_label=n_name,
                    ),
                    sampling=sampling_meta,
                )
            )

        # Pattern 2: 1 Datetime + 1 Numeric -> Line Chart
        if date_cols and num_cols:
            d_name = date_cols[0]
            n_name = num_cols[0]
            line_data = [
                {"timestamp": str(r.get(d_name)), "value": r.get(n_name, 0)}
                for r in data_sample
                if r.get(d_name) is not None
            ]
            specs.append(
                ChartSpec(
                    chart_id=f"sql_line_{d_name}_{n_name}",
                    chart_type=ChartType.LINE,
                    title=f"Trend of {n_name} over {d_name}",
                    description=f"Temporal trend for {n_name}",
                    dataset_id=dataset_id,
                    version_id=version_id,
                    x="timestamp",
                    y="value",
                    data=line_data,
                    options=ChartOptions(
                        show_legend=False,
                        x_axis_label=d_name,
                        y_axis_label=n_name,
                    ),
                    sampling=sampling_meta,
                )
            )

        # Pattern 3: 2 Numeric -> Scatter Plot
        if len(num_cols) >= 2:
            x_num = num_cols[0]
            y_num = num_cols[1]
            scatter_data = [
                {"x": r.get(x_num), "y": r.get(y_num)}
                for r in data_sample
                if r.get(x_num) is not None and r.get(y_num) is not None
            ]
            specs.append(
                ChartSpec(
                    chart_id=f"sql_scatter_{x_num}_{y_num}",
                    chart_type=ChartType.SCATTER,
                    title=f"{y_num} vs {x_num}",
                    description=f"Correlation scatter plot of {x_num} and {y_num}",
                    dataset_id=dataset_id,
                    version_id=version_id,
                    x="x",
                    y="y",
                    data=scatter_data,
                    options=ChartOptions(
                        show_legend=False,
                        x_axis_label=x_num,
                        y_axis_label=y_num,
                    ),
                    sampling=sampling_meta,
                )
            )

        # Pattern 4: 1 Numeric only -> Histogram Bins
        elif len(num_cols) == 1 and not cat_cols and not date_cols:
            n_name = num_cols[0]
            values = [float(r[n_name]) for r in rows if r.get(n_name) is not None and isinstance(r[n_name], (int, float))]
            if values:
                min_v, max_v = min(values), max(values)
                bin_count = min(10, len(values))
                step = (max_v - min_v) / bin_count if max_v > min_v else 1.0
                bins = [{"bin_start": min_v + i * step, "bin_end": min_v + (i + 1) * step, "count": 0} for i in range(bin_count)]
                for v in values:
                    idx = min(int((v - min_v) / step), bin_count - 1) if step > 0 else 0
                    bins[idx]["count"] += 1

                specs.append(
                    ChartSpec(
                        chart_id=f"sql_hist_{n_name}",
                        chart_type=ChartType.HISTOGRAM,
                        title=f"Distribution of {n_name}",
                        description=f"Frequency histogram for {n_name}",
                        dataset_id=dataset_id,
                        version_id=version_id,
                        x="bin_start",
                        y="count",
                        data=bins,
                        options=ChartOptions(
                            bin_count=bin_count,
                            x_axis_label=n_name,
                            y_axis_label="Frequency",
                        ),
                        sampling=sampling_meta,
                    )
                )

        return specs
