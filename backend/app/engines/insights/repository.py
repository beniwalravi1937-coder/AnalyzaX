"""
AnalyzaX — Phase 25: Insights Repository.
Thread-safe persistence for proactive insights, evidence graphs, and status transitions.
"""

import json
import os
import threading
from typing import Dict, List, Optional
from uuid import uuid4

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.insights.models import Insight, InsightSeverity, InsightStatus


class InsightRepository:
    """Thread-safe JSON repository managing analytical insights."""

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        self._dir = storage_dir or os.path.join(settings.DATA_STORAGE_ROOT, "insights")
        self._file_path = os.path.join(self._dir, "insights.json")
        self._lock = threading.Lock()
        self._insights: Dict[str, Insight] = {}
        self._init_storage()

    def _init_storage(self) -> None:
        os.makedirs(self._dir, exist_ok=True)
        with self._lock:
            if os.path.exists(self._file_path):
                try:
                    with open(self._file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self._insights = {k: Insight(**v) for k, v in data.items()}
                except Exception as e:
                    logger.error(f"Failed to load insights repository: {e}")
                    self._insights = {}
            else:
                self._insights = {}

    def _flush(self) -> None:
        temp_path = f"{self._file_path}.tmp.{uuid4().hex[:6]}"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump({k: v.model_dump() for k, v in self._insights.items()}, f, indent=2)
        os.replace(temp_path, self._file_path)

    def save_insight(self, insight: Insight) -> Insight:
        with self._lock:
            self._insights[insight.insight_id] = insight
            self._flush()
            return insight

    def save_insights(self, insights: List[Insight]) -> List[Insight]:
        with self._lock:
            for ins in insights:
                self._insights[ins.insight_id] = ins
            self._flush()
            return insights

    def get_insight(self, insight_id: str) -> Optional[Insight]:
        with self._lock:
            return self._insights.get(insight_id)

    def list_insights(
        self,
        workspace_id: Optional[str] = None,
        project_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        version_id: Optional[str] = None,
        severity: Optional[InsightSeverity] = None,
        status: Optional[InsightStatus] = InsightStatus.CURRENT,
    ) -> List[Insight]:
        with self._lock:
            results = list(self._insights.values())
            if workspace_id:
                results = [i for i in results if i.workspace_id == workspace_id]
            if project_id:
                results = [i for i in results if i.project_id == project_id or i.project_id is None]
            if dataset_id:
                results = [i for i in results if i.dataset_id == dataset_id]
            if version_id:
                results = [i for i in results if i.dataset_version_id == version_id]
            if severity:
                results = [i for i in results if i.severity == severity]
            if status:
                results = [i for i in results if i.status == status]
            return sorted(results, key=lambda x: x.importance_score, reverse=True)

    def dismiss_insight(self, insight_id: str) -> bool:
        with self._lock:
            ins = self._insights.get(insight_id)
            if not ins:
                return False
            ins.status = InsightStatus.DISMISSED
            self._flush()
            return True

    def mark_stale_for_dataset(self, dataset_id: str, current_version_id: str) -> int:
        """Marks insights derived from older versions of a dataset as STALE."""
        updated = 0
        with self._lock:
            for ins in self._insights.values():
                if ins.dataset_id == dataset_id and ins.dataset_version_id != current_version_id:
                    if ins.status == InsightStatus.CURRENT:
                        ins.status = InsightStatus.STALE
                        updated += 1
            if updated > 0:
                self._flush()
        return updated


insight_repo = InsightRepository()
insight_repository = insight_repo
