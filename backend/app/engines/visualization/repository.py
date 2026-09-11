"""
Persistence repositories for saved visualizations and audit history.
"""

import json
import os
import threading
from typing import List, Optional
from backend.app.core.config import settings
from backend.app.engines.visualization.models import (
    SavedVisualization,
    VisualizationHistoryEntry,
)


class SavedVisualizationRepository:
    """
    Thread-safe repository for persisting saved visualizations.
    """

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or os.path.join(
            settings.DATA_VISUALIZATIONS_DIR, "saved.json"
        )
        self._lock = threading.Lock()
        self._ensure_file()

    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def get_all(
        self,
        dataset_id: Optional[str] = None,
        version_id: Optional[str] = None,
    ) -> List[SavedVisualization]:
        with self._lock:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                items = [SavedVisualization.model_validate(d) for d in data]
                if dataset_id:
                    items = [i for i in items if i.dataset_id == dataset_id]
                if version_id:
                    items = [i for i in items if i.dataset_version_id == version_id]
                return items
            except Exception:
                return []

    def get_by_id(self, visualization_id: str) -> Optional[SavedVisualization]:
        items = self.get_all()
        for item in items:
            if item.visualization_id == visualization_id:
                return item
        return None

    def save(self, viz: SavedVisualization) -> SavedVisualization:
        with self._lock:
            items = []
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                items = [SavedVisualization.model_validate(d) for d in raw]
            except Exception:
                items = []

            # Upsert
            existing_idx = next(
                (i for i, v in enumerate(items) if v.visualization_id == viz.visualization_id),
                None,
            )
            if existing_idx is not None:
                items[existing_idx] = viz
            else:
                items.insert(0, viz)

            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([item.model_dump() for item in items], f, indent=2)

            return viz

    def delete(self, visualization_id: str) -> bool:
        with self._lock:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                items = [SavedVisualization.model_validate(d) for d in raw]
            except Exception:
                return False

            initial_len = len(items)
            items = [v for v in items if v.visualization_id != visualization_id]
            if len(items) == initial_len:
                return False

            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([item.model_dump() for item in items], f, indent=2)

            return True


class VisualizationHistoryRepository:
    """
    Thread-safe audit repository for visualization activity.
    """

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or os.path.join(
            settings.DATA_VISUALIZATIONS_DIR, "history.json"
        )
        self._lock = threading.Lock()
        self._ensure_file()

    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def log_action(self, entry: VisualizationHistoryEntry) -> None:
        with self._lock:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                entries = [VisualizationHistoryEntry.model_validate(d) for d in raw]
            except Exception:
                entries = []

            entries.insert(0, entry)
            entries = entries[:200]  # Cap at 200 entries

            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([e.model_dump() for e in entries], f, indent=2)

    def get_history(self, limit: int = 50) -> List[VisualizationHistoryEntry]:
        with self._lock:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                entries = [VisualizationHistoryEntry.model_validate(d) for d in raw]
                return entries[:limit]
            except Exception:
                return []
