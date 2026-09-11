"""
Deterministic Visualization Planner & Recommender.
Evaluates dataset metadata, semantic classifications, cardinality, and quality to recommend charts.
"""

from typing import Any, Dict, List, Optional
import uuid

from backend.app.engines.visualization.models import (
    ChartType,
    VisualizationIntent,
    VisualizationRecommendation,
)
from backend.app.engines.visualization.rules import (
    CategoricalBivariateRule,
    CategoricalComparisonRule,
    ColumnContext,
    CompositionRule,
    EvaluationContext,
    NumericDistributionRule,
    NumericRelationshipRule,
    QualityGuardrailFilter,
    TemporalTrendRule,
)


class VisualizationRecommender:
    """
    Coordinates modular recommendation rules and produces ranked,
    explainable chart suggestions with deterministic confidence scoring.
    """

    def __init__(self):
        self.rules = [
            TemporalTrendRule(),
            CategoricalComparisonRule(),
            NumericRelationshipRule(),
            NumericDistributionRule(),
            CompositionRule(),
            CategoricalBivariateRule(),
        ]
        self.quality_filter = QualityGuardrailFilter()

    def recommend(
        self,
        columns: Dict[str, ColumnContext],
        row_count: int,
        selected_fields: Optional[List[str]] = None,
        intent: Optional[VisualizationIntent] = None,
        quality_issues: Optional[List[Dict[str, Any]]] = None,
        max_recommendations: int = 12,
    ) -> List[VisualizationRecommendation]:
        """
        Generates deterministic recommendations ordered by priority and confidence.
        """
        ctx = EvaluationContext(
            columns=columns,
            row_count=row_count,
            selected_fields=selected_fields,
            intent=intent,
            quality_issues=quality_issues or [],
        )

        raw_recommendations: List[VisualizationRecommendation] = []
        for rule in self.rules:
            try:
                results = rule.evaluate(ctx)
                raw_recommendations.extend(results)
            except Exception:
                continue

        # Apply data-quality penalties and guardrails
        filtered = self.quality_filter.apply(raw_recommendations, ctx)

        # Populate tier and registry recommendation priority from central registry (VIZ-T06, VIZ-T07, VIZ-T08)
        from backend.app.engines.visualization.registry import get_chart_definition

        for r in filtered:
            c_def = get_chart_definition(r.chart_type)
            if c_def:
                r.tier = c_def.tier.value

        # Deterministic sorting hierarchy:
        # 1. Analytical suitability (r.priority ASC - 1 is highest priority/suitability) -> VIZ-T07
        # 2. Confidence (r.confidence DESC)
        # 3. Chart Tier (r.tier ASC: Tier 1 > Tier 2 > Tier 3) -> VIZ-T06
        # 4. Registry priority (c_def.recommendation_priority DESC)
        # 5. Title (r.title ASC for deterministic tie-breaking)
        def _tier_aware_sort_key(r: VisualizationRecommendation):
            c_def = get_chart_definition(r.chart_type)
            reg_prio = c_def.recommendation_priority if c_def else 50
            return (r.priority, -r.confidence, r.tier, -reg_prio, r.title)

        filtered.sort(key=_tier_aware_sort_key)

        return filtered[:max_recommendations]

    def recommend_from_sql_result(
        self,
        columns: List[Dict[str, Any]],
        rows: List[Dict[str, Any]],
        query_text: Optional[str] = None,
    ) -> List[VisualizationRecommendation]:
        """
        Deterministic recommendation engine for Phase 8 SQL QueryResults.
        """
        if not columns or not rows:
            return []

        row_count = len(rows)
        col_contexts: Dict[str, ColumnContext] = {}

        for col in columns:
            name = col.get("name", "")
            phys_type = col.get("physical_type", "string").lower()
            sem_type = col.get("semantic_type", "unknown").lower()

            # Inspect cardinality in rows
            distinct_vals = set(r.get(name) for r in rows if r.get(name) is not None)
            card = len(distinct_vals)

            col_contexts[name] = ColumnContext(
                name=name,
                physical_type=phys_type,
                semantic_type=sem_type,
                cardinality=card,
                unique_percentage=(card / max(1, row_count)) * 100.0,
                is_constant=(card == 1),
                is_identifier=(card == row_count and card > 20 and sem_type != "numeric"),
            )

        return self.recommend(
            columns=col_contexts,
            row_count=row_count,
            max_recommendations=6,
        )
