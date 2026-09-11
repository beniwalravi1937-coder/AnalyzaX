"""
Persistence Repositories for Phase 14 Dashboard Engine.
Thread-safe persistence for Dashboards and Dashboard Version History.
"""

import json
import os
import threading
from typing import List, Optional

from backend.app.core.config import settings
from backend.app.engines.dashboard.models import Dashboard, DashboardVersion


class DashboardRepository:
    """
    Thread-safe repository for persisting and querying dashboards.
    """

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or os.path.join(settings.DATA_DASHBOARDS_DIR, "dashboards.json")
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
        search: Optional[str] = None,
    ) -> List[Dashboard]:
        with self._lock:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                items = [Dashboard.model_validate(d) for d in data]

                if dataset_id:
                    items = [d for d in items if d.dataset_id == dataset_id]

                if search:
                    term = search.lower()
                    items = [
                        d for d in items
                        if term in d.name.lower() or (d.description and term in d.description.lower())
                    ]

                # Sort by updated_at desc
                items.sort(key=lambda x: x.updated_at, reverse=True)
                return items
            except Exception:
                return []

    def get_by_id(self, dashboard_id: str) -> Optional[Dashboard]:
        items = self.get_all()
        for item in items:
            if item.dashboard_id == dashboard_id:
                return item
        return None

    def save(self, dashboard: Dashboard) -> Dashboard:
        with self._lock:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                items = [Dashboard.model_validate(d) for d in data]
            except Exception:
                items = []

            # Compute hash before saving
            dashboard.configuration_hash = dashboard.compute_hash()

            existing_idx = next((i for i, d in enumerate(items) if d.dashboard_id == dashboard.dashboard_id), None)
            if existing_idx is not None:
                items[existing_idx] = dashboard
            else:
                items.append(dashboard)

            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([d.model_dump(mode="json") for d in items], f, indent=2, default=str)

            return dashboard

    def delete(self, dashboard_id: str) -> bool:
        with self._lock:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                items = [Dashboard.model_validate(d) for d in data]
            except Exception:
                return False

            orig_len = len(items)
            items = [d for d in items if d.dashboard_id != dashboard_id]
            if len(items) == orig_len:
                return False

            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([d.model_dump(mode="json") for d in items], f, indent=2, default=str)

            return True


class DashboardHistoryRepository:
    """
    Thread-safe repository for persisting audit history and immutable snapshots
    of Dashboard versions.
    """

    def __init__(self, history_dir: Optional[str] = None):
        self.history_dir = history_dir or os.path.join(settings.DATA_DASHBOARDS_DIR, "history")
        self._lock = threading.Lock()
        os.makedirs(self.history_dir, exist_ok=True)

    def _get_dashboard_dir(self, dashboard_id: str) -> str:
        d_path = os.path.join(self.history_dir, dashboard_id)
        os.makedirs(d_path, exist_ok=True)
        return d_path

    def save_version(self, version: DashboardVersion) -> DashboardVersion:
        with self._lock:
            d_path = self._get_dashboard_dir(version.dashboard_id)
            file_path = os.path.join(d_path, f"v{version.version_number}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(version.model_dump(mode="json"), f, indent=2, default=str)
            return version

    def get_versions(self, dashboard_id: str) -> List[DashboardVersion]:
        with self._lock:
            d_path = self._get_dashboard_dir(dashboard_id)
            versions: List[DashboardVersion] = []
            for fname in os.listdir(d_path):
                if fname.endswith(".json"):
                    fpath = os.path.join(d_path, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        versions.append(DashboardVersion.model_validate(data))
                    except Exception:
                        continue

            versions.sort(key=lambda x: x.version_number, reverse=True)
            return versions

    def get_version(self, dashboard_id: str, version_number: int) -> Optional[DashboardVersion]:
        with self._lock:
            d_path = self._get_dashboard_dir(dashboard_id)
            file_path = os.path.join(d_path, f"v{version_number}.json")
            if not os.path.exists(file_path):
                return None
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return DashboardVersion.model_validate(data)
            except Exception:
                return None
