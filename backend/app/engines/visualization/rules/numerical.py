"""
Recommendation rules for numeric distributions and relationships.
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


class NumericDistributionRule(BaseRecommendationRule):
    """
    Evaluates single numeric measures and suggests Histogram or Boxplot.
    """

    def evaluate(self, ctx: EvaluationContext) -> List[VisualizationRecommendation]:
        recommendations: List[VisualizationRecommendation] = []
        numeric_cols = ctx.get_numeric_columns()

        if ctx.selected_fields:
            numeric_cols = [c for c in ctx.selected_fields if c in numeric_cols]

        for col_name in numeric_cols:
            col = ctx.columns[col_name]
            warnings = []
            if col.null_percentage > 10.0:
                warnings.append(f"Column '{col_name}' contains {col.null_percentage:.1f}% missing values.")

            # Histogram Recommendation
            conf_hist = 0.90
            if ctx.intent == VisualizationIntent.DISTRIBUTION:
                conf_hist = 0.98

            recommendations.append(
                VisualizationRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    chart_type=ChartType.HISTOGRAM,
                    title=f"Distribution of {col_name}",
                    reason=f"Numerical measure '{col_name}' is well suited to frequency binning to inspect skewness and spread.",
                    confidence=conf_hist,
                    x_field=col_name,
                    aggregation="count",
                    warnings=warnings,
                    required_fields=[col_name],
                    priority=2,
                    intent="distribution",
                )
            )

            # Box Plot Recommendation (Tier 1)
            conf_box = 0.85
            if ctx.intent == VisualizationIntent.DISTRIBUTION:
                conf_box = 0.92

            recommendations.append(
                VisualizationRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    chart_type=ChartType.BOX,
                    title=f"Box Plot of {col_name}",
                    reason=f"Five-number summary (median, quartiles, outliers) for continuous measure '{col_name}'.",
                    confidence=conf_box,
                    y_field=col_name,
                    warnings=warnings,
                    required_fields=[col_name],
                    priority=3,
                    tier=1,
                    intent="distribution",
                )
            )

            # Violin Plot Recommendation (Tier 2 - Advanced Analytical)
            # Analytical suitability rule (VIZ-T06, VIZ-T07): Does not outrank Histogram/Boxplot merely for complexity.
            conf_violin = 0.72
            if ctx.intent == VisualizationIntent.DISTRIBUTION:
                conf_violin = 0.82

            recommendations.append(
                VisualizationRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    chart_type=ChartType.VIOLIN,
                    title=f"Violin Plot of {col_name}",
                    reason=f"Kernel density and probability distribution shape for continuous measure '{col_name}'.",
                    confidence=conf_violin,
                    y_field=col_name,
                    warnings=warnings,
                    required_fields=[col_name],
                    priority=4,
                    tier=2,
                    intent="distribution",
                )
            )

        return recommendations


class NumericRelationshipRule(BaseRecommendationRule):
    """
    Evaluates pairs of numeric features and suggests Scatter or Bubble plots.
    """

    def evaluate(self, ctx: EvaluationContext) -> List[VisualizationRecommendation]:
        recommendations: List[VisualizationRecommendation] = []
        numeric_cols = ctx.get_numeric_columns()

        if ctx.selected_fields:
            numeric_cols = [c for c in ctx.selected_fields if c in numeric_cols]

        if len(numeric_cols) < 2:
            return recommendations

        # Inspect pairs (limit to top pairs if too many)
        pairs_evaluated = 0
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                if pairs_evaluated >= 4 and not ctx.selected_fields:
                    break

                x_col = numeric_cols[i]
                y_col = numeric_cols[j]
                pairs_evaluated += 1

                warnings = []
                if ctx.row_count > 5000:
                    warnings.append(f"Large dataset ({ctx.row_count} rows): scatter will use deterministic bounded sampling.")

                conf = 0.92
                if ctx.intent in (VisualizationIntent.RELATIONSHIP, VisualizationIntent.CORRELATION):
                    conf = 0.98

                recommendations.append(
                    VisualizationRecommendation(
                        recommendation_id=str(uuid.uuid4()),
                        chart_type=ChartType.SCATTER,
                        title=f"{y_col} vs. {x_col}",
                        reason=f"Two continuous numeric variables '{x_col}' and '{y_col}' reveal correlation, clustering, and bivariate outliers.",
                        confidence=conf,
                        x_field=x_col,
                        y_field=y_col,
                        warnings=warnings,
                        required_fields=[x_col, y_col],
                        priority=1 if ctx.intent == VisualizationIntent.RELATIONSHIP else 2,
                        intent="relationship",
                    )
                )

        return recommendations
