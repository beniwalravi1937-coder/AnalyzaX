"""
AnalyzaX — Phase 25: Insight Importance Ranker.
Deterministic multi-criteria prioritization algorithm scoring insights based on
effect magnitude, statistical significance, and data reliability.
"""

from typing import List
from backend.app.engines.insights.models import Insight, InsightSeverity


class InsightRanker:
    """Prioritizes and scores analytical insights deterministically."""

    @classmethod
    def rank_insights(cls, insights: List[Insight]) -> List[Insight]:
        """
        Computes and calibrates the importance score for each insight,
        assigning severity categories and sorting in descending order of priority.
        """
        for ins in insights:
            base_score = ins.importance_score
            if base_score <= 0.0:
                if ins.severity == InsightSeverity.CRITICAL:
                    base_score = 85.0
                elif ins.severity == InsightSeverity.HIGH:
                    base_score = 70.0
                elif ins.severity in (InsightSeverity.WARNING, InsightSeverity.MEDIUM):
                    base_score = 55.0
                else:
                    base_score = 30.0

            # Weight adjustments based on evidence completeness
            if ins.evidence:
                ev_count = len(ins.evidence)
                # Multi-evidence bonus (up to +10%)
                base_score = min(100.0, base_score + min(10.0, (ev_count - 1) * 5.0))

            # Adjust severity based on final score
            if base_score >= 80.0:
                ins.severity = InsightSeverity.CRITICAL
            elif base_score >= 50.0:
                ins.severity = InsightSeverity.WARNING
            else:
                ins.severity = InsightSeverity.INFO

            ins.importance_score = round(base_score, 2)

        # Sort descending by importance score
        return sorted(insights, key=lambda x: x.importance_score, reverse=True)

    @classmethod
    def rank_insight(cls, insight: Insight) -> Insight:
        """Ranks a single insight and returns the calibrated insight."""
        return cls.rank_insights([insight])[0]

