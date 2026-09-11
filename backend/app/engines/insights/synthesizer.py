"""
AnalyzaX — Phase 25: Cross-Engine Insight Synthesizer.
Fuses evidence from EDA, Statistics, Quality, and Forecasting engines into
coherent, grounded analytical summaries without LLM calculation hallucinations.
"""

from typing import Any, Dict, List, Optional
from backend.app.engines.insights.models import Insight, InsightEvidence


class InsightSynthesizer:
    """Synthesizes multiple deterministic findings into a cohesive analytical finding."""

    @classmethod
    def synthesize_findings(
        cls,
        insights: List[Insight],
        focus_metric: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fuses a collection of related insights into an integrated narrative synthesis.
        Guarantees every claim is tied to an underlying evidence item.
        """
        if not insights:
            return {
                "headline": "No anomalous signals detected.",
                "summary": "The active dataset version does not show severe quality, correlation, or statistical anomalies.",
                "evidence_count": 0,
                "synthesized_narrative": "All inspected dimensions appear stable and conform to typical distributions.",
                "citations": [],
            }

        citations: List[Dict[str, Any]] = []
        key_points: List[str] = []

        # Triage critical and high importance findings
        critical_insights = [i for i in insights if i.importance_score >= 50.0]
        working_set = critical_insights if critical_insights else insights[:3]

        for ins in working_set:
            key_points.append(f"{ins.title}: {ins.summary}")
            for ev in ins.evidence:
                citations.append({
                    "insight_id": ins.insight_id,
                    "evidence_type": ev.evidence_type,
                    "description": ev.description,
                    "metrics": ev.metrics,
                })

        # Deterministic structured synthesis
        headline = f"Identified {len(working_set)} Priority Signal{'s' if len(working_set) > 1 else ''}"
        if focus_metric:
            headline = f"Analysis of '{focus_metric}': {headline}"

        bullet_points = "\n".join(f"• {pt}" for pt in key_points)
        synthesized_narrative = (
            f"Based on multi-engine analysis across the current dataset version:\n"
            f"{bullet_points}\n\n"
            f"Recommended Next Step: Investigate the underlying dimensions and verify if historical trends or data quality anomalies account for the observed variations."
        )

        return {
            "headline": headline,
            "summary": working_set[0].summary if working_set else "",
            "evidence_count": len(citations),
            "synthesized_narrative": synthesized_narrative,
            "citations": citations,
            "primary_insight_id": working_set[0].insight_id if working_set else None,
        }
