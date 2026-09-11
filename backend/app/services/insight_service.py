"""
AnalyzaX — Phase 25: Proactive Insight Application Service.
Coordinates automated signal detection across analytical engines, deterministic ranking,
and persistent insight lifecycle management.
"""

from typing import Any, Dict, List, Optional
from backend.app.core.logging import logger
from backend.app.engines.insights.detector import ProactiveInsightDetector
from backend.app.engines.insights.models import (
    Insight,
    InsightSeverity,
    InsightStatus,
    InsightType,
)
from backend.app.engines.insights.ranker import InsightRanker
from backend.app.engines.insights.repository import insight_repository


class InsightService:
    """Application Service for Proactive Insights."""

    def list_insights(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        severity: Optional[InsightSeverity] = None,
        status: Optional[InsightStatus] = None,
        insight_type: Optional[InsightType] = None,
    ) -> List[Insight]:
        """Lists stored insights matching criteria, ordered by importance score."""
        return insight_repository.list_insights(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_id=dataset_id,
            severity=severity,
            status=status,
            insight_type=insight_type,
        )

    def get_insight(self, insight_id: str) -> Optional[Insight]:
        return insight_repository.get_insight(insight_id)

    def dismiss_insight(self, insight_id: str) -> bool:
        return insight_repository.dismiss_insight(insight_id)

    def generate_insights_for_dataset(
        self,
        workspace_id: str,
        dataset_id: str,
        version_id: str,
        project_id: Optional[str] = None,
        profile_data: Optional[Dict[str, Any]] = None,
        quality_data: Optional[Dict[str, Any]] = None,
        eda_data: Optional[Dict[str, Any]] = None,
        stats_data: Optional[Dict[str, Any]] = None,
    ) -> List[Insight]:
        """Runs proactive signal detection across analytical outputs and persists ranked findings."""
        detected = ProactiveInsightDetector.detect_insights(
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            version_id=version_id,
            project_id=project_id,
            profile_data=profile_data,
            quality_data=quality_data,
            eda_data=eda_data,
            stats_data=stats_data,
        )

        ranked: List[Insight] = []
        for ins in detected:
            scored = InsightRanker.rank_insight(ins)
            insight_repository.save_insight(scored)
            ranked.append(scored)

        ranked.sort(key=lambda x: x.importance_score, reverse=True)
        return ranked


insight_service = InsightService()
