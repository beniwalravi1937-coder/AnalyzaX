"""
Post-processing quality filter and safety guardrails for recommendations.
"""

from typing import List
from backend.app.engines.visualization.models import VisualizationRecommendation
from backend.app.engines.visualization.rules.base import EvaluationContext


class QualityGuardrailFilter:
    """
    Applies deterministic quality adjustments, penalties, and warnings
    based on missingness, identifier status, constancy, and small dataset limits.
    """

    def apply(
        self,
        recommendations: List[VisualizationRecommendation],
        ctx: EvaluationContext,
    ) -> List[VisualizationRecommendation]:
        filtered: List[VisualizationRecommendation] = []

        for rec in recommendations:
            adjusted_conf = rec.confidence
            warnings = list(rec.warnings)

            # 1. Small dataset warning (VIZ-64)
            if ctx.row_count < 15:
                warnings.append(f"Small dataset ({ctx.row_count} rows): statistical trends and distributions should be interpreted with caution.")
                adjusted_conf = min(adjusted_conf, 0.75)

            # 2. Identifier column penalty (VIZ-10)
            for f in rec.required_fields:
                if f in ctx.columns:
                    col = ctx.columns[f]
                    if col.is_identifier:
                        if not ctx.selected_fields or f not in ctx.selected_fields:
                            # Severely penalize automatic recommendation of identifiers
                            adjusted_conf *= 0.3
                            warnings.append(f"Field '{f}' appears to be a unique identifier / key.")
                    if col.is_constant:
                        adjusted_conf *= 0.2
                        warnings.append(f"Field '{f}' is constant or has only 1 distinct value.")

            # 3. High missingness warning (VIZ-09)
            for f in rec.required_fields:
                if f in ctx.columns:
                    col = ctx.columns[f]
                    if col.null_percentage >= 20.0:
                        warnings.append(f"High missingness in '{f}' ({col.null_percentage:.1f}% nulls): may skew visual aggregates.")
                        adjusted_conf *= 0.85

            rec.confidence = round(max(0.05, min(1.0, adjusted_conf)), 2)
            rec.warnings = list(dict.fromkeys(warnings))  # Deduplicate

            # Only retain recommendations with viable confidence
            if rec.confidence >= 0.30:
                filtered.append(rec)

        return filtered
