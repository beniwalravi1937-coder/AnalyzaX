"""
Recommendation rules for part-to-whole compositions and proportion analysis.
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


class CompositionRule(BaseRecommendationRule):
    """
    Evaluates part-to-whole proportion analysis.
    Strictly restricts Donut/Pie to low cardinality (2 to 7 categories).
    Recommends Treemap for moderate cardinality (8 to 30 categories).
    """

    def evaluate(self, ctx: EvaluationContext) -> List[VisualizationRecommendation]:
        recommendations: List[VisualizationRecommendation] = []
        cat_cols = ctx.get_categorical_columns()
        num_cols = ctx.get_numeric_columns()

        if ctx.selected_fields:
            cat_cols = [c for c in ctx.selected_fields if c in cat_cols]
            num_cols = [c for c in ctx.selected_fields if c in num_cols]

        if not cat_cols or not num_cols:
            return recommendations

        for cat_name in cat_cols:
            cat_col = ctx.columns[cat_name]
            cardinality = cat_col.cardinality or 1
            num_name = num_cols[0]

            # Rule: Donut / Pie ONLY when 2 <= cardinality <= 7
            if 2 <= cardinality <= 7:
                conf = 0.78
                if ctx.intent == VisualizationIntent.COMPOSITION:
                    conf = 0.94

                recommendations.append(
                    VisualizationRecommendation(
                        recommendation_id=str(uuid.uuid4()),
                        chart_type=ChartType.DONUT,
                        title=f"{num_name} Share by {cat_name}",
                        reason=f"Low-cardinality dimension '{cat_name}' ({cardinality} categories) allows legible proportional share representation without visual clutter.",
                        confidence=conf,
                        x_field=cat_name,
                        y_field=num_name,
                        aggregation="sum",
                        required_fields=[cat_name, num_name],
                        priority=3,
                        intent="composition",
                    )
                )

            # Rule: Treemap when cardinality is between 8 and 30
            elif 8 <= cardinality <= 30:
                conf = 0.82
                if ctx.intent == VisualizationIntent.COMPOSITION:
                    conf = 0.92

                recommendations.append(
                    VisualizationRecommendation(
                        recommendation_id=str(uuid.uuid4()),
                        chart_type=ChartType.TREEMAP,
                        title=f"{num_name} Distribution across {cat_name}",
                        reason=f"Nested rectangular treemap displays hierarchical proportion across {cardinality} categories more effectively than angular slices.",
                        confidence=conf,
                        x_field=cat_name,
                        y_field=num_name,
                        aggregation="sum",
                        required_fields=[cat_name, num_name],
                        priority=3,
                        intent="composition",
                    )
                )

        return recommendations
