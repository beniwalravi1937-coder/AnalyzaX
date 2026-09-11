"""
Recommendation rules for time-series and temporal trends.
"""

from typing import List
import uuid

from backend.app.engines.visualization.models import (
    ChartType,
    VisualizationIntent,
    VisualizationRecommendation,
)
from backend.app.engines.visualization.rules.base import (
    BaseRecommendationRule,
    EvaluationContext,
)


class TemporalTrendRule(BaseRecommendationRule):
    """
    Evaluates datetime dimensions paired with numerical measures.
    Emits Line Chart for trend continuity and Area Chart for volume over time.
    """

    def evaluate(self, ctx: EvaluationContext) -> List[VisualizationRecommendation]:
        recommendations: List[VisualizationRecommendation] = []
        time_cols = ctx.get_temporal_columns()
        num_cols = ctx.get_numeric_columns()
        cat_cols = ctx.get_categorical_columns()

        if ctx.selected_fields:
            time_cols = [c for c in ctx.selected_fields if c in time_cols]
            num_cols = [c for c in ctx.selected_fields if c in num_cols]
            cat_cols = [c for c in ctx.selected_fields if c in cat_cols]

        if not time_cols or not num_cols:
            return recommendations

        for time_col in time_cols:
            for num_col in num_cols[:2]:
                warnings = []
                col = ctx.columns[time_col]
                if col.null_percentage > 5.0:
                    warnings.append(f"Temporal field '{time_col}' has {col.null_percentage:.1f}% missing timestamps.")

                conf_line = 0.96
                if ctx.intent == VisualizationIntent.TREND:
                    conf_line = 0.99

                # 1. Single series Line Chart
                recommendations.append(
                    VisualizationRecommendation(
                        recommendation_id=str(uuid.uuid4()),
                        chart_type=ChartType.LINE,
                        title=f"{num_col} Trend over {time_col}",
                        reason=f"Temporal dimension '{time_col}' paired with numeric measure '{num_col}' reveals chronological progression, seasonality, and cycles.",
                        confidence=conf_line,
                        x_field=time_col,
                        y_field=num_col,
                        aggregation="sum",
                        sorting="asc",
                        warnings=warnings,
                        required_fields=[time_col, num_col],
                        priority=1,
                        intent="trend",
                    )
                )

                # 2. Area Chart for cumulative magnitude
                recommendations.append(
                    VisualizationRecommendation(
                        recommendation_id=str(uuid.uuid4()),
                        chart_type=ChartType.AREA,
                        title=f"{num_col} Volume over {time_col}",
                        reason=f"Area fill accentuates the overall volume and magnitude of '{num_col}' along the chronological horizon.",
                        confidence=0.88,
                        x_field=time_col,
                        y_field=num_col,
                        aggregation="sum",
                        sorting="asc",
                        warnings=warnings,
                        required_fields=[time_col, num_col],
                        priority=2,
                        intent="trend",
                    )
                )

                # 3. Multi-series Line Chart if low-cardinality categorical exists
                if cat_cols:
                    series_col = cat_cols[0]
                    card = ctx.columns[series_col].cardinality or 1
                    if card <= 10:
                        recommendations.append(
                            VisualizationRecommendation(
                                recommendation_id=str(uuid.uuid4()),
                                chart_type=ChartType.MULTI_LINE,
                                title=f"{num_col} over {time_col} by {series_col}",
                                reason=f"Breakdown of temporal trend across distinct series of '{series_col}' ({card} series).",
                                confidence=0.92,
                                x_field=time_col,
                                y_field=num_col,
                                series_field=series_col,
                                aggregation="sum",
                                sorting="asc",
                                warnings=warnings,
                                required_fields=[time_col, num_col, series_col],
                                priority=1,
                                intent="trend",
                            )
                        )

        return recommendations
