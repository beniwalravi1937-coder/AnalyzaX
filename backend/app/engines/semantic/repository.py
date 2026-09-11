"""
AnalyzaX — Phase 25: Semantic Layer Repository.
Thread-safe persistence for governed metrics, dimensions, entities, and version histories.
"""

import json
import os
import threading
from typing import Dict, List, Optional
from uuid import uuid4

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.semantic.models import (
    DimensionDefinition,
    EntityDefinition,
    MetricDefinition,
    MetricStatus,
    MetricVersionRecord,
)


class SemanticRepository:
    """Thread-safe JSON repository managing semantic models and versioned metrics."""

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        self._dir = storage_dir or os.path.join(settings.DATA_STORAGE_ROOT, "semantic")
        self._metrics_path = os.path.join(self._dir, "metrics.json")
        self._versions_path = os.path.join(self._dir, "metric_versions.json")
        self._dimensions_path = os.path.join(self._dir, "dimensions.json")
        self._entities_path = os.path.join(self._dir, "entities.json")
        self._lock = threading.Lock()

        self._metrics: Dict[str, MetricDefinition] = {}
        self._versions: Dict[str, List[MetricVersionRecord]] = {}  # metric_id -> list of versions
        self._dimensions: Dict[str, DimensionDefinition] = {}
        self._entities: Dict[str, EntityDefinition] = {}

        self._init_storage()

    def _init_storage(self) -> None:
        os.makedirs(self._dir, exist_ok=True)
        with self._lock:
            # Load Metrics
            if os.path.exists(self._metrics_path):
                try:
                    with open(self._metrics_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self._metrics = {k: MetricDefinition(**v) for k, v in data.items()}
                except Exception as e:
                    logger.error(f"Failed to load metrics repository: {e}")
                    self._metrics = {}
            else:
                self._metrics = {}

            # Load Metric Versions
            if os.path.exists(self._versions_path):
                try:
                    with open(self._versions_path, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                        self._versions = {
                            k: [MetricVersionRecord(**rec) for rec in v_list]
                            for k, v_list in raw.items()
                        }
                except Exception as e:
                    logger.error(f"Failed to load metric versions: {e}")
                    self._versions = {}
            else:
                self._versions = {}

    def _flush_metrics(self) -> None:
        temp_path = f"{self._metrics_path}.tmp.{uuid4().hex[:6]}"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump({k: v.model_dump() for k, v in self._metrics.items()}, f, indent=2)
        os.replace(temp_path, self._metrics_path)

    def _flush_versions(self) -> None:
        temp_path = f"{self._versions_path}.tmp.{uuid4().hex[:6]}"
        with open(temp_path, "w", encoding="utf-8") as f:
            out = {k: [rec.model_dump() for rec in v_list] for k, v_list in self._versions.items()}
            json.dump(out, f, indent=2)
        os.replace(temp_path, self._versions_path)

    def save_metric(
        self,
        metric: MetricDefinition,
        author_id: str = "system",
        change_reason: Optional[str] = None,
        changed_by: Optional[str] = None,
        change_summary: Optional[str] = None,
    ) -> MetricDefinition:
        author = changed_by or author_id
        reason = change_summary or change_reason
        with self._lock:
            existing = self._metrics.get(metric.metric_id)
            history_list = self._versions.setdefault(metric.metric_id, [])
            if existing:
                metric.version = existing.version + 1
                history_list.append(
                    MetricVersionRecord(
                        version_id=str(uuid4()),
                        metric_id=metric.metric_id,
                        version=metric.version,
                        definition=metric.model_copy(deep=True),
                        changed_by=author,
                        change_reason=reason,
                        created_at=metric.updated_at,
                    )
                )
            else:
                history_list.append(
                    MetricVersionRecord(
                        version_id=str(uuid4()),
                        metric_id=metric.metric_id,
                        version=metric.version,
                        definition=metric.model_copy(deep=True),
                        changed_by=author,
                        change_reason=reason or "Initial metric creation",
                        created_at=metric.created_at,
                    )
                )
            self._flush_versions()
            self._metrics[metric.metric_id] = metric.model_copy(deep=True)
            self._flush_metrics()
            return metric

    def get_metric(self, metric_id: str) -> Optional[MetricDefinition]:
        with self._lock:
            return self._metrics.get(metric_id)

    def get_metric_by_name(self, name: str, workspace_id: Optional[str] = None) -> Optional[MetricDefinition]:
        with self._lock:
            clean_name = name.lower().strip()
            for m in self._metrics.values():
                if workspace_id and m.workspace_id != workspace_id:
                    continue
                if m.name.lower().strip() == clean_name:
                    return m
                if any(syn.lower().strip() == clean_name for syn in m.synonyms):
                    return m
            return None

    def list_metrics(
        self,
        workspace_id: Optional[str] = None,
        project_id: Optional[str] = None,
        status: Optional[MetricStatus] = None,
    ) -> List[MetricDefinition]:
        with self._lock:
            results = list(self._metrics.values())
            if workspace_id:
                results = [m for m in results if m.workspace_id == workspace_id]
            if project_id:
                results = [m for m in results if m.project_id == project_id or m.project_id is None]
            if status:
                results = [m for m in results if m.status == status]
            return sorted(results, key=lambda x: x.name)

    def delete_metric(self, metric_id: str, soft_archive: bool = True) -> bool:
        with self._lock:
            metric = self._metrics.get(metric_id)
            if not metric:
                return False
            if soft_archive:
                metric.status = MetricStatus.ARCHIVED
                self._flush_metrics()
            else:
                del self._metrics[metric_id]
                self._flush_metrics()
            return True

    def get_version_history(self, metric_id: str) -> List[MetricVersionRecord]:
        with self._lock:
            return list(self._versions.get(metric_id, []))

    def list_metric_versions(self, metric_id: str) -> List[MetricVersionRecord]:
        with self._lock:
            return list(self._versions.get(metric_id, []))


semantic_repo = SemanticRepository()
