"""
AnalyzaX — Phase 25: AI Recommendation Engine.
Produces contextual NextAnalysisRecommendation objects based on detected insights,
current analytical results, and schema dimensions.
"""

import uuid
from typing import Any, Dict, List, Optional

from backend.app.engines.ai_copilot.models import NextAnalysisRecommendation, RiskLevel
from backend.app.engines.insights.models import Insight, InsightType


class RecommendationEngine:
    """Generates deterministic, context-rich next-step analytical recommendations."""

    @staticmethod
    def generate_recommendations(
        insights: List[Insight],
        active_columns: Optional[List[str]] = None,
        has_time_column: bool = False,
        dataset_meta: Optional[Dict[str, Any]] = None,
    ) -> List[NextAnalysisRecommendation]:
        """Maps discovered insights to targeted next-best analyses."""
        recommendations: List[NextAnalysisRecommendation] = []
        active_columns = active_columns or []

        for ins in insights:
            if ins.insight_type == InsightType.ANOMALY:
                recommendations.append(
                    NextAnalysisRecommendation(
                        recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                        type="outlier_investigation",
                        title=f"Isolate and investigate outliers in {', '.join(ins.affected_columns)}",
                        reason=f"Detected anomaly '{ins.title}'. Segmenting extreme values will prevent skewed model performance.",
                        expected_value="Identify whether anomalies stem from data entry errors or genuine behavioral spikes.",
                        required_inputs=ins.affected_columns,
                        tool_plan=["get_eda_insights", "execute_sql"],
                        risk=RiskLevel.ANALYTICAL,
                        estimated_cost=0.01,
                    )
                )

            elif ins.insight_type == InsightType.CORRELATION:
                recommendations.append(
                    NextAnalysisRecommendation(
                        recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                        type="feature_interaction",
                        title=f"Analyze feature interaction for {', '.join(ins.affected_columns[:2])}",
                        reason=f"High correlation identified in '{ins.title}'. Exploring joint distribution clarifies colinearity.",
                        expected_value="Determine if one feature is redundant or if both should be combined for predictive modeling.",
                        required_inputs=ins.affected_columns[:2],
                        tool_plan=["run_statistical_test", "create_visualization"],
                        risk=RiskLevel.ANALYTICAL,
                        estimated_cost=0.01,
                    )
                )

            elif ins.insight_type == InsightType.TREND_CHANGE:
                recommendations.append(
                    NextAnalysisRecommendation(
                        recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                        type="forecast_projection",
                        title=f"Run 6-month time-series forecast on {', '.join(ins.affected_columns)}",
                        reason=f"Trend shift detected in '{ins.title}'. Projecting forward reveals future trajectory.",
                        expected_value="Quantify projected baseline vs scenario deviations for planning.",
                        required_inputs=ins.affected_columns,
                        tool_plan=["generate_forecast", "create_visualization"],
                        risk=RiskLevel.ANALYTICAL,
                        estimated_cost=0.05,
                    )
                )

            elif ins.insight_type == InsightType.SEGMENT_DIFFERENCE:
                recommendations.append(
                    NextAnalysisRecommendation(
                        recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                        type="statistical_significance",
                        title=f"Test statistical significance across {', '.join(ins.affected_dimensions)}",
                        reason=f"Segment disparity observed in '{ins.title}'. Formal hypothesis testing verifies reliability.",
                        expected_value="Determine p-value to confirm difference is statistically robust rather than random noise.",
                        required_inputs=ins.affected_columns + ins.affected_dimensions,
                        tool_plan=["run_statistical_test"],
                        risk=RiskLevel.ANALYTICAL,
                        estimated_cost=0.01,
                    )
                )

            elif ins.insight_type == InsightType.DATA_QUALITY:
                recommendations.append(
                    NextAnalysisRecommendation(
                        recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                        type="cleaning_plan",
                        title=f"Review imputation and cleaning options for {', '.join(ins.affected_columns)}",
                        reason=f"Data quality issue reported: {ins.summary}. Remediation stabilizes downstream analysis.",
                        expected_value="Produce a previewable, immutable transformation plan.",
                        required_inputs=ins.affected_columns,
                        tool_plan=["propose_cleaning", "apply_cleaning"],
                        risk=RiskLevel.REVERSIBLE_MUTATION,
                        estimated_cost=0.02,
                    )
                )

        # If no specific insight triggered recommendations, provide a smart default based on schema
        if not recommendations:
            if has_time_column:
                recommendations.append(
                    NextAnalysisRecommendation(
                        recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                        type="trend_analysis",
                        title="Analyze temporal trend across key metrics",
                        reason="Dataset has temporal dimensions. Trend decomposition highlights seasonal patterns.",
                        expected_value="Reveal underlying cycle and growth trajectory.",
                        required_inputs=[],
                        tool_plan=["generate_forecast", "create_visualization"],
                        risk=RiskLevel.ANALYTICAL,
                        estimated_cost=0.01,
                    )
                )
            else:
                recommendations.append(
                    NextAnalysisRecommendation(
                        recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                        type="segment_comparison",
                        title="Compare distributions across categorical groups",
                        reason="Exploring cohort variance uncovers hidden segment clusters.",
                        expected_value="Identify which segments deviate most from population averages.",
                        required_inputs=[],
                        tool_plan=["get_eda_insights", "create_visualization"],
                        risk=RiskLevel.ANALYTICAL,
                        estimated_cost=0.01,
                    )
                )

        return recommendations[:5]
