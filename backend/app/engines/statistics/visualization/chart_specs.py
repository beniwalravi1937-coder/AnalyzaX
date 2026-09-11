"""
AnalyzaX — Phase 10: Statistical Visualization Integration
Translates deterministic statistical outputs into standard Phase 9 ChartSpec objects (STAT-46 to STAT-50).
Reuses the existing ChartRenderer without creating duplicate rendering logic.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from backend.app.engines.visualization.models import (
    ChartAxesConfig,
    ChartEncoding,
    ChartLegendConfig,
    ChartSamplingMetadata,
    ChartSpec,
    ChartType,
    VisualizationProvenance,
)


def build_distribution_chart_specs(
    dist_result: Dict[str, Any],
    dataset_id: str,
    dataset_version_id: str,
    column_name: str,
) -> List[Dict[str, Any]]:
    """Generates ChartSpecs for distribution analysis (Histogram, ECDF)."""
    bins = dist_result.get("histogram_bins", [])
    specs = []

    if bins:
        # Format data points for histogram
        hist_data = [
            {
                "bin_label": f"[{b['bin_start']}, {b['bin_end']})",
                "count": b["count"],
                "percentage": b["percentage"],
                "expected_normal": b.get("expected_normal_count", 0),
            }
            for b in bins
        ]

        hist_spec = ChartSpec(
            chart_id=f"stat_hist_{uuid.uuid4().hex[:8]}",
            chart_type=ChartType.BAR,
            title=f"Distribution Histogram: {column_name}",
            subtitle=f"Freedman-Diaconis binned counts with normal distribution overlay (n={dist_result.get('count')})",
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            source_type="statistics",
            x="bin_label",
            y="count",
            data=hist_data,
            axes=ChartAxesConfig(x_label="Bin Range", y_label="Frequency Count", x_rotate=45),
            legend=ChartLegendConfig(show=False),
            sampling=ChartSamplingMetadata(original_row_count=dist_result.get("count", 0), displayed_points=len(hist_data)),
            provenance=VisualizationProvenance(
                dataset_id=dataset_id,
                dataset_version_id=dataset_version_id,
                source_type="statistics",
                source_reference="distribution_analysis",
                created_at=datetime.now(timezone.utc).isoformat(),
            ),
        )
        specs.append(hist_spec.model_dump())

    # ECDF chart
    ecdf = dist_result.get("ecdf", [])
    if ecdf:
        ecdf_spec = ChartSpec(
            chart_id=f"stat_ecdf_{uuid.uuid4().hex[:8]}",
            chart_type=ChartType.LINE,
            title=f"Empirical Cumulative Distribution (ECDF): {column_name}",
            subtitle="Cumulative probability distribution function",
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            source_type="statistics",
            x="value",
            y="cumulative_probability",
            data=ecdf,
            axes=ChartAxesConfig(x_label=column_name, y_label="Cumulative Probability", y_min=0.0, y_max=1.0),
            legend=ChartLegendConfig(show=False),
            sampling=ChartSamplingMetadata(original_row_count=dist_result.get("count", 0), displayed_points=len(ecdf)),
            provenance=VisualizationProvenance(
                dataset_id=dataset_id,
                dataset_version_id=dataset_version_id,
                source_type="statistics",
                source_reference="distribution_analysis",
                created_at=datetime.now(timezone.utc).isoformat(),
            ),
        )
        specs.append(ecdf_spec.model_dump())

    return specs


def build_group_comparison_chart_specs(
    comparison_result: Dict[str, Any],
    dataset_id: str,
    dataset_version_id: str,
    outcome_name: str,
    group_col_name: str,
) -> List[Dict[str, Any]]:
    """Generates ChartSpecs for group comparisons (Means + CI bar/error chart)."""
    group_summaries = comparison_result.get("group_summaries")
    if not group_summaries:
        # Fallback to group1 and group2 summaries
        g1 = comparison_result.get("group1_summary")
        g2 = comparison_result.get("group2_summary")
        if g1 and g2:
            group_summaries = [g1, g2]

    if not group_summaries:
        return []

    chart_data = [
        {
            "group": g["group"],
            "mean": g.get("mean", g.get("median", 0)),
            "std": g.get("std", 0),
            "se": g.get("se", 0),
            "count": g["count"],
        }
        for g in group_summaries
    ]

    spec = ChartSpec(
        chart_id=f"stat_grp_{uuid.uuid4().hex[:8]}",
        chart_type=ChartType.BAR,
        title=f"Group Means Comparison: {outcome_name} by {group_col_name}",
        subtitle=f"Computed with {comparison_result.get('method_name', 'Group Comparison')}",
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        source_type="statistics",
        x="group",
        y="mean",
        data=chart_data,
        axes=ChartAxesConfig(x_label=group_col_name, y_label=f"Mean {outcome_name}"),
        legend=ChartLegendConfig(show=False),
        provenance=VisualizationProvenance(
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            source_type="statistics",
            source_reference=comparison_result.get("method", "group_comparison"),
            created_at=datetime.now(timezone.utc).isoformat(),
        ),
    )
    return [spec.model_dump()]


def build_correlation_chart_specs(
    corr_result: Dict[str, Any],
    dataset_id: str,
    dataset_version_id: str,
) -> List[Dict[str, Any]]:
    """Generates ChartSpecs for correlation matrices (Heatmap)."""
    matrix = corr_result.get("matrix", [])
    columns = corr_result.get("columns", [])
    if not matrix or not columns:
        return []

    heatmap_data = []
    for i, col_a in enumerate(columns):
        for j, col_b in enumerate(columns):
            cell = matrix[i][j]
            r_val = cell.get("r")
            heatmap_data.append({
                "var_x": col_b,
                "var_y": col_a,
                "correlation": r_val if r_val is not None else 0.0,
                "p_value": cell.get("p_value"),
                "is_valid": cell.get("is_valid", False),
            })

    spec = ChartSpec(
        chart_id=f"stat_corrmat_{uuid.uuid4().hex[:8]}",
        chart_type=ChartType.CORRELATION_MATRIX,
        title=f"Correlation Matrix ({corr_result.get('method', 'pearson').capitalize()})",
        subtitle=f"Pairwise correlations across {len(columns)} numerical variables",
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        source_type="statistics",
        x="var_x",
        y="var_y",
        color="correlation",
        data=heatmap_data,
        axes=ChartAxesConfig(x_label="", y_label="", x_rotate=45),
        provenance=VisualizationProvenance(
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            source_type="statistics",
            source_reference="correlation_matrix",
            created_at=datetime.now(timezone.utc).isoformat(),
        ),
    )
    return [spec.model_dump()]


def build_regression_chart_specs(
    reg_result: Dict[str, Any],
    dataset_id: str,
    dataset_version_id: str,
    y_name: str,
    x_name: str,
) -> List[Dict[str, Any]]:
    """Generates ChartSpecs for regression diagnostics (Residual vs Fitted)."""
    plot_data = reg_result.get("plot_data", {})
    residual_points = plot_data.get("residual_vs_fitted", [])
    if not residual_points:
        return []

    spec = ChartSpec(
        chart_id=f"stat_resid_{uuid.uuid4().hex[:8]}",
        chart_type=ChartType.SCATTER,
        title=f"Residuals vs Fitted: {y_name}",
        subtitle=f"Homoscedasticity diagnostic (R²={reg_result.get('r_squared')})",
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        source_type="statistics",
        x="fitted",
        y="residual",
        data=residual_points,
        axes=ChartAxesConfig(x_label="Fitted Values (Y-hat)", y_label="Residuals (e)"),
        legend=ChartLegendConfig(show=False),
        provenance=VisualizationProvenance(
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            source_type="statistics",
            source_reference="ols_regression",
            created_at=datetime.now(timezone.utc).isoformat(),
        ),
    )
    return [spec.model_dump()]


def build_contingency_chart_specs(
    cat_result: Dict[str, Any],
    dataset_id: str,
    dataset_version_id: str,
    var1_name: str,
    var2_name: str,
) -> List[Dict[str, Any]]:
    """Generates ChartSpecs for categorical contingency tables (Heatmap)."""
    table = cat_result.get("contingency_table", {})
    rows = table.get("rows", [])
    if not rows:
        return []

    heatmap_cells = []
    for r in rows:
        r_lbl = r["row_category"]
        for cell in r["cells"]:
            c_lbl = cell["column_category"]
            heatmap_cells.append({
                "var_x": c_lbl,
                "var_y": r_lbl,
                "observed": cell["observed"],
                "expected": cell["expected"],
                "residual": cell["residual"],
                "row_percentage": cell["row_percentage"],
            })

    spec = ChartSpec(
        chart_id=f"stat_cont_{uuid.uuid4().hex[:8]}",
        chart_type=ChartType.HEATMAP,
        title=f"Contingency Heatmap: {var1_name} × {var2_name}",
        subtitle=f"Chi-square={cat_result.get('statistic')}, p={cat_result.get('p_value')}",
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        source_type="statistics",
        x="var_x",
        y="var_y",
        color="observed",
        data=heatmap_cells,
        axes=ChartAxesConfig(x_label=var2_name, y_label=var1_name, x_rotate=45),
        provenance=VisualizationProvenance(
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            source_type="statistics",
            source_reference="chi_square",
            created_at=datetime.now(timezone.utc).isoformat(),
        ),
    )
    return [spec.model_dump()]
