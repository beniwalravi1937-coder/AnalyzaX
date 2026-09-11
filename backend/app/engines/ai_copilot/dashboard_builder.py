"""
AnalyzaX — Phase 25: AI Dashboard Builder Engine.
Produces structured, deterministic DashboardPlan specifications based on dataset
schema, profile, and governed metrics without generating arbitrary frontend code.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.engines.ai_copilot.models import DashboardPlan, DashboardPlanComponent
from backend.app.engines.semantic.models import MetricDefinition


class DashboardBuilderEngine:
    """Plans intelligent dashboards from dataset metadata, governed metrics, and user goals."""

    @staticmethod
    def plan_dashboard(
        title: str,
        description: str,
        dataset_id: str,
        version_id: str,
        profile_data: Optional[Dict[str, Any]] = None,
        governed_metrics: Optional[List[MetricDefinition]] = None,
        selected_dimensions: Optional[List[str]] = None,
    ) -> DashboardPlan:
        """Constructs a deterministic DashboardPlan with layout grid, KPIs, and charts."""
        plan_id = f"plan_{uuid.uuid4().hex[:12]}"
        components: List[DashboardPlanComponent] = []
        governed_metrics = governed_metrics or []
        profile_data = profile_data or {}
        columns_profile = profile_data.get("columns", {})

        # Identify numeric and categorical columns
        numeric_cols = [
            c for c, meta in columns_profile.items()
            if meta.get("inferred_type") in ("numeric", "float", "integer", "DOUBLE", "BIGINT")
        ]
        categorical_cols = [
            c for c, meta in columns_profile.items()
            if meta.get("inferred_type") in ("categorical", "string", "VARCHAR", "TEXT")
        ]
        datetime_cols = [
            c for c, meta in columns_profile.items()
            if meta.get("inferred_type") in ("datetime", "date", "TIMESTAMP", "DATE")
        ]

        # Augment from selected_dimensions if provided
        selected_dimensions = selected_dimensions or []
        for col in selected_dimensions:
            col_lower = col.lower()
            if any(t in col_lower for t in ["date", "time", "month", "year", "day"]):
                if col not in datetime_cols:
                    datetime_cols.append(col)
            elif any(n in col_lower for n in ["amount", "revenue", "sales", "price", "cost", "total", "qty", "count"]):
                if col not in numeric_cols:
                    numeric_cols.append(col)
            else:
                if col not in categorical_cols:
                    categorical_cols.append(col)

        layout_y = 0

        # 1. Top KPI Row (width 4 each, up to 3 KPIs)
        kpi_metrics = governed_metrics[:3]
        if not kpi_metrics and numeric_cols:
            # Fallback to top numeric columns as simple KPIs
            for i, num_col in enumerate(numeric_cols[:3]):
                components.append(
                    DashboardPlanComponent(
                        component_type="kpi",
                        title=f"Total {num_col.replace('_', ' ').title()}",
                        metric_name=num_col,
                        layout={"x": i * 4, "y": layout_y, "w": 4, "h": 2},
                        chart_spec={
                            "chart_type": "kpi",
                            "value_column": num_col,
                            "aggregation": "SUM",
                        },
                    )
                )

        else:
            for i, metric in enumerate(kpi_metrics):
                components.append(
                    DashboardPlanComponent(
                        component_type="kpi",
                        title=metric.name,
                        metric_name=metric.name,
                        layout={"x": i * 4, "y": layout_y, "w": 4, "h": 2},
                        chart_spec={
                            "chart_type": "kpi",
                            "metric_id": metric.metric_id,
                            "expression": metric.expression,
                            "unit": metric.unit,
                        },
                    )
                )

        if components:
            layout_y += 2

        # 2. Main Trend or Distribution Chart
        time_col = datetime_cols[0] if datetime_cols else None
        primary_metric = (
            governed_metrics[0].name
            if governed_metrics
            else (numeric_cols[0] if numeric_cols else "count")
        )

        if time_col and primary_metric:
            components.append(
                DashboardPlanComponent(
                    component_type="chart",
                    title=f"{primary_metric.replace('_', ' ').title()} Over Time",
                    metric_name=primary_metric,
                    dimensions=[time_col],
                    layout={"x": 0, "y": layout_y, "w": 8, "h": 4},
                    chart_spec={
                        "chart_type": "line",
                        "x_axis": time_col,
                        "y_axis": primary_metric,
                        "title": f"{primary_metric.replace('_', ' ').title()} Over Time",
                    },
                )
            )
        elif categorical_cols and primary_metric:
            cat_col = categorical_cols[0]
            components.append(
                DashboardPlanComponent(
                    component_type="chart",
                    title=f"{primary_metric.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                    metric_name=primary_metric,
                    dimensions=[cat_col],
                    layout={"x": 0, "y": layout_y, "w": 8, "h": 4},
                    chart_spec={
                        "chart_type": "bar",
                        "x_axis": cat_col,
                        "y_axis": primary_metric,
                        "title": f"{primary_metric.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                    },
                )
            )

        # 3. Categorical Breakdown / Secondary Visual
        second_cat = (
            categorical_cols[1]
            if len(categorical_cols) > 1
            else (categorical_cols[0] if categorical_cols else None)
        )
        if second_cat and primary_metric:
            components.append(
                DashboardPlanComponent(
                    component_type="chart",
                    title=f"Breakdown by {second_cat.replace('_', ' ').title()}",
                    metric_name=primary_metric,
                    dimensions=[second_cat],
                    layout={"x": 8, "y": layout_y, "w": 4, "h": 4},
                    chart_spec={
                        "chart_type": "donut",
                        "dimension": second_cat,
                        "metric": primary_metric,
                    },
                )
            )

        filters: List[Dict[str, Any]] = []
        if time_col:
            filters.append({
                "column": time_col,
                "filter_type": "date_range",
                "label": f"Filter by {time_col.replace('_', ' ').title()}",
            })
        if categorical_cols:
            filters.append({
                "column": categorical_cols[0],
                "filter_type": "select",
                "label": f"Filter by {categorical_cols[0].replace('_', ' ').title()}",
            })

        return DashboardPlan(
            plan_id=plan_id,
            title=title,
            description=description,
            dataset_id=dataset_id,
            version_id=version_id,
            components=components,
            filters=filters,
            requires_approval=True,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
