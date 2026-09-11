"""
AnalyzaX — Phase 25: AI Narrative Generator & Causality Guard.
Generates structured analytical narratives across Executive, Analyst, and Technical tiers,
enforcing strict non-causal language constraints for observational datasets.
"""

import re
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from backend.app.engines.ai_copilot.models import AnalyticalStory
from backend.app.engines.insights.models import Insight, InsightEvidence


class NarrativeTone(str, Enum):
    EXECUTIVE = "EXECUTIVE"
    ANALYST = "ANALYST"
    TECHNICAL = "TECHNICAL"


class CausalityGuard:
    """Enforces non-causal language on observational data narratives."""

    UNSUPPORTED_CAUSAL_PATTERNS = [
        (r"\bcauses\b", "is associated with"),
        (r"\bcaused by\b", "associated with"),
        (r"\bproves that\b", "strongly suggests that"),
        (r"\bleads to\b", "is linked to"),
        (r"\bdriving the fact that\b", "correlated with the fact that"),
        (r"\bresponsible for creating\b", "associated with"),
    ]

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Replaces unsupported causal assertions with observational relationship phrasing."""
        sanitized = text
        for pattern, replacement in cls.UNSUPPORTED_CAUSAL_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        return sanitized


class NarrativeGenerator:
    """Generates structured analytical stories with multi-tier tone adaptation."""

    @staticmethod
    def generate_story(
        question: str,
        insights: List[Insight],
        evidence_list: Optional[List[InsightEvidence]] = None,
        tone: NarrativeTone = NarrativeTone.ANALYST,
        dataset_meta: Optional[Dict[str, Any]] = None,
    ) -> AnalyticalStory:
        """Builds a grounded AnalyticalStory adhering to observational causality guardrails."""
        story_id = f"story_{uuid.uuid4().hex[:12]}"
        evidence = evidence_list or []
        for ins in insights:
            evidence.extend(ins.evidence)

        observations: List[str] = []
        findings: List[str] = []
        limitations: List[str] = [
            "Analysis is based on observational data; associations do not imply strict causality.",
            "Historical trends may not account for unobserved exogenous variables.",
        ]
        recommendations: List[str] = []

        for ins in insights:
            observations.append(f"{ins.title}: {ins.summary}")
            findings.append(ins.summary)
            recommendations.extend(ins.recommended_actions)

        # Tone-specific framing
        if tone == NarrativeTone.EXECUTIVE:
            title = f"Executive Briefing: {question}"
            raw_explanation = (
                f"Key business takeaways: {len(insights)} primary signals detected. "
                + " ".join(observations[:2])
                + " Recommend focusing operational attention on the most severe variances."
            )
        elif tone == NarrativeTone.TECHNICAL:
            title = f"Technical Analytical Synthesis: {question}"
            raw_explanation = (
                f"Quantitative breakdown: Examined {len(insights)} deterministic signals across "
                f"{len(evidence)} evidence points. Findings demonstrate statistical variation "
                f"subject to underlying dataset distributions. Validation p-values and confidence intervals "
                f"should be benchmarked against baseline version schemas."
            )
        else:  # ANALYST
            title = f"Analytical Investigation: {question}"
            raw_explanation = (
                f"Detailed finding: Exploration uncovered notable variance across key dimensions. "
                + " ".join(observations)
            )

        sanitized_explanation = CausalityGuard.sanitize(raw_explanation)

        return AnalyticalStory(
            story_id=story_id,
            title=title,
            question=question,
            context=dataset_meta or {},
            observations=observations,
            evidence=evidence,
            findings=findings,
            explanations=sanitized_explanation,
            limitations=limitations,
            recommendations=list(set(recommendations)),
            charts=[],
            created_at=datetime.now(timezone.utc).isoformat(),
        )
