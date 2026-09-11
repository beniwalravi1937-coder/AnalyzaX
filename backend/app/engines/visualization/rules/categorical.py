"""
Recommendation rules for categorical comparisons and high-cardinality ranking.
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


class CategoricalComparisonRule(BaseRecommendationRule):
    """
    Evaluates categorical dimension paired with numeric measures.
    Emits standard Bar Chart for reasonable cardinality, or Top-N Bar for high cardinality.
    """

    def evaluate(self, ctx: EvaluationContext) -> List[VisualizationRecommendation]:
        recommendations: List[VisualizationRecommendation] = []
        cat_cols = ctx.get_categorical_columns()
        num_cols = ctx.get_numeric_columns()

        if ctx.selected_fields:
            cat_cols = [c for c in ctx.selected_fields if c in cat_cols]
            num_cols = [c for c in ctx.selected_fields if c in num_cols]

        for cat_name in cat_cols:
            cat_col = ctx.columns[cat_name]
            cardinality = cat_col.cardinality or 1

            for num_name in num_cols[:3]:  # Limit measure combinations
                warnings = []
                if cat_col.null_percentage > 5.0:
                    warnings.append(f"Dimension '{cat_name}' has {cat_col.null_percentage:.1f}% missing values.")

                # Case 1: Low-to-moderate cardinality (<= 25 categories)
                if cardinality <= 25:
                    conf = 0.94
                    if ctx.intent in (VisualizationIntent.COMPARISON, VisualizationIntent.RANKING):
                        conf = 0.98

                    recommendations.append(
                        VisualizationRecommendation(
                            recommendation_id=str(uuid.uuid4()),
                            chart_type=ChartType.BAR,
                            title=f"{num_name} by {cat_name}",
                            reason=f"Categorical dimension '{cat_name}' ({cardinality} categories) with metric '{num_name}' is ideal for discrete comparison.",
                            confidence=conf,
                            x_field=cat_name,
                            y_field=num_name,
                            aggregation="sum",
                            sorting="desc",
                            warnings=warnings,
                            required_fields=[cat_name, num_name],
                            priority=1,
                            intent="comparison",
                        )
                    )

                    # Also offer horizontal bar if labels are likely long or cardinality > 8
                    if cardinality > 8:
                        recommendations.append(
                            VisualizationRecommendation(
                                recommendation_id=str(uuid.uuid4()),
                                chart_type=ChartType.HORIZONTAL_BAR,
                                title=f"{num_name} by {cat_name} (Horizontal)",
                                reason=f"Horizontal orientation offers improved label legibility across {cardinality} categories.",
                                confidence=0.91,
                                x_field=num_name,
                                y_field=cat_name,
                                aggregation="sum",
                                sorting="desc",
                                warnings=warnings,
                                required_fields=[cat_name, num_name],
                                priority=2,
                                intent="ranking",
                            )
                        )

                # Case 2: High cardinality (> 25 categories) -> Top-N Bar Chart
                else:
                    warnings.append(f"High cardinality ({cardinality} categories): Bounded to Top 10 with remainder aggregated as 'Other'.")
                    recommendations.append(
                        VisualizationRecommendation(
                            recommendation_id=str(uuid.uuid4()),
                            chart_type=ChartType.BAR,
                            title=f"Top 10 {cat_name} by {num_name}",
                            reason=f"High-cardinality dimension '{cat_name}' ({cardinality} categories) is safely visualized via Top-N ranking to avoid visual clutter.",
                            confidence=0.88,
                            x_field=cat_name,
                            y_field=num_name,
                            aggregation="sum",
                            sorting="desc",
                            warnings=warnings,
                            required_fields=[cat_name, num_name],
                            priority=2,
                            intent="ranking",
                        )
                    )

        return recommendations


class CategoricalBivariateRule(BaseRecommendationRule):
    """
    Evaluates pairs of categorical dimensions and suggests Grouped Bar or Heatmap.
    """

    def evaluate(self, ctx: EvaluationContext) -> List[VisualizationRecommendation]:
        recommendations: List[VisualizationRecommendation] = []
        cat_cols = ctx.get_categorical_columns()
        num_cols = ctx.get_numeric_columns()

        if ctx.selected_fields:
            cat_cols = [c for c in ctx.selected_fields if c in cat_cols]
            num_cols = [c for c in ctx.selected_fields if c in num_cols]

        if len(cat_cols) < 2:
            return recommendations

        col_a_name = cat_cols[0]
        col_b_name = cat_cols[1]
        card_a = ctx.columns[col_a_name].cardinality or 1
        card_b = ctx.columns[col_b_name].cardinality or 1

        if card_a <= 15 and card_b <= 15:
            measure = num_cols[0] if num_cols else None
            conf = 0.82
            if ctx.intent == VisualizationIntent.RELATIONSHIP:
                conf = 0.90

            recommendations.append(
                VisualizationRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    chart_type=ChartType.HEATMAP,
                    title=f"Cross-tabulation: {col_a_name} vs. {col_b_name}",
                    reason=f"Bivariate categorical matrix ({card_a} x {card_b}) exposes intersectional density and distribution.",
                    confidence=conf,
                    x_field=col_a_name,
                    y_field=col_b_name,
                    color_field=measure,
                    aggregation="count" if not measure else "sum",
                    required_fields=[col_a_name, col_b_name],
                    priority=3,
                    intent="relationship",
                )
            )

        return recommendations
