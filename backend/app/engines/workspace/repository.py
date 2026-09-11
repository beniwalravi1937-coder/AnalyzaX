"""
Thread-safe repository for Phase 16 Workspace, Project, Asset, and Activity persistence.
Maintains atomic JSON file storage under data/workspace/ with fast in-memory indexing.
"""

from datetime import datetime, timezone, timedelta
import json
import os
import shutil
import threading
import time
from typing import Any, Dict, List, Optional

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.workspace.models import (
    Workspace,
    Project,
    Asset,
    AssetRelationship,
    ActivityRecord,
    AssetStatus,
    ProjectStatus,
    WorkspaceStatus,
)


class WorkspaceRepository:
    """
    Thread-safe repository coordinating atomic JSON persistence
    and multi-index lookups for workspaces, projects, assets, and activity logs.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self._lock = threading.RLock()
        self._storage_dir = os.path.abspath(storage_dir or settings.DATA_WORKSPACE_DIR)
        self._workspaces_file = os.path.join(self._storage_dir, "workspaces.json")
        self._projects_file = os.path.join(self._storage_dir, "projects.json")
        self._assets_file = os.path.join(self._storage_dir, "assets.json")
        self._relationships_file = os.path.join(self._storage_dir, "relationships.json")
        self._activity_file = os.path.join(self._storage_dir, "activity.json")

        self._ensure_dirs()
        self._load_all()

    def _ensure_dirs(self) -> None:
        os.makedirs(self._storage_dir, exist_ok=True)

    def _load_json(self, file_path: str, default: Any) -> Any:
        if not os.path.exists(file_path):
            return default
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read {file_path}, falling back to default: {e}")
            return default

    def _atomic_save(self, file_path: str, data: Any) -> None:
        temp_path = f"{file_path}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            
            # Windows atomic replace with retry & fallback
            for attempt in range(5):
                try:
                    os.replace(temp_path, file_path)
                    return
                except (PermissionError, OSError):
                    if attempt < 4:
                        time.sleep(0.02)
                    else:
                        try:
                            shutil.copyfile(temp_path, file_path)
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                            return
                        except Exception:
                            raise
        except Exception as e:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            logger.error(f"Failed to atomically write {file_path}: {e}")
            raise

    def _load_all(self) -> None:
        with self._lock:
            self._workspaces: Dict[str, dict] = self._load_json(self._workspaces_file, {})
            self._projects: Dict[str, dict] = self._load_json(self._projects_file, {})
            self._assets: Dict[str, dict] = self._load_json(self._assets_file, {})
            self._relationships: Dict[str, dict] = self._load_json(self._relationships_file, {})
            self._activities: List[dict] = self._load_json(self._activity_file, [])

    # ─────────────────────────────────────────────────────────────
    # Workspaces
    # ─────────────────────────────────────────────────────────────

    def save_workspace(self, ws: Workspace) -> Workspace:
        with self._lock:
            ws.updated_at = datetime.now(timezone.utc).isoformat()
            self._workspaces[ws.workspace_id] = ws.model_dump()
            self._atomic_save(self._workspaces_file, self._workspaces)
            return ws

    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        with self._lock:
            data = self._workspaces.get(workspace_id)
            return Workspace(**data) if data else None

    def get_workspace_by_slug(self, slug: str) -> Optional[Workspace]:
        with self._lock:
            for data in self._workspaces.values():
                if data.get("slug") == slug:
                    return Workspace(**data)
            return None

    def list_workspaces(self, status: Optional[WorkspaceStatus] = None) -> List[Workspace]:
        with self._lock:
            res = []
            for data in self._workspaces.values():
                if status and data.get("status") != status.value:
                    continue
                res.append(Workspace(**data))
            return sorted(res, key=lambda w: w.created_at)

    def delete_workspace(self, workspace_id: str) -> bool:
        with self._lock:
            if workspace_id in self._workspaces:
                del self._workspaces[workspace_id]
                self._atomic_save(self._workspaces_file, self._workspaces)
                return True
            return False

    # ─────────────────────────────────────────────────────────────
    # Projects
    # ─────────────────────────────────────────────────────────────

    def save_project(self, proj: Project) -> Project:
        with self._lock:
            proj.updated_at = datetime.now(timezone.utc).isoformat()
            self._projects[proj.project_id] = proj.model_dump()
            self._atomic_save(self._projects_file, self._projects)
            return proj

    def get_project(self, project_id: str) -> Optional[Project]:
        with self._lock:
            data = self._projects.get(project_id)
            return Project(**data) if data else None

    def get_project_by_slug(self, workspace_id: str, slug: str) -> Optional[Project]:
        with self._lock:
            for data in self._projects.values():
                if data.get("workspace_id") == workspace_id and data.get("slug") == slug:
                    return Project(**data)
            return None

    def list_projects(
        self,
        workspace_id: Optional[str] = None,
        status: Optional[ProjectStatus] = None,
    ) -> List[Project]:
        with self._lock:
            res = []
            for data in self._projects.values():
                if workspace_id and data.get("workspace_id") != workspace_id:
                    continue
                if status and data.get("status") != status.value:
                    continue
                res.append(Project(**data))
            return sorted(res, key=lambda p: p.last_activity_at, reverse=True)

    def delete_project(self, project_id: str) -> bool:
        with self._lock:
            if project_id in self._projects:
                del self._projects[project_id]
                self._atomic_save(self._projects_file, self._projects)
                return True
            return False

    # ─────────────────────────────────────────────────────────────
    # Assets
    # ─────────────────────────────────────────────────────────────

    def save_asset(self, asset: Asset) -> Asset:
        with self._lock:
            asset.updated_at = datetime.now(timezone.utc).isoformat()
            self._assets[asset.asset_id] = asset.model_dump()
            self._atomic_save(self._assets_file, self._assets)

            # Update project activity timestamp
            if asset.project_id in self._projects:
                self._projects[asset.project_id]["last_activity_at"] = asset.updated_at
                self._atomic_save(self._projects_file, self._projects)

            return asset

    def get_asset(self, asset_id: str) -> Optional[Asset]:
        with self._lock:
            data = self._assets.get(asset_id)
            return Asset(**data) if data else None

    def get_asset_by_source(
        self, project_id: str, source_entity_id: str
    ) -> Optional[Asset]:
        with self._lock:
            for data in self._assets.values():
                if (
                    data.get("project_id") == project_id
                    and data.get("source_entity_id") == source_entity_id
                ):
                    return Asset(**data)
            return None

    def find_asset_by_source_id(self, source_entity_id: str) -> Optional[Asset]:
        """Finds an asset by its source_entity_id across all projects."""
        with self._lock:
            for data in self._assets.values():
                if data.get("source_entity_id") == source_entity_id:
                    return Asset(**data)
                # Also check source_metadata
                meta = data.get("source_metadata", {})
                if isinstance(meta, dict) and (meta.get("dataset_id") == source_entity_id or meta.get("id") == source_entity_id):
                    return Asset(**data)
            return None

    def list_assets(
        self,
        project_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        asset_type: Optional[str] = None,
        status: Optional[AssetStatus] = None,
        is_favorite: Optional[bool] = None,
    ) -> List[Asset]:
        with self._lock:
            res = []
            for data in self._assets.values():
                if project_id and data.get("project_id") != project_id:
                    continue
                if workspace_id and data.get("workspace_id") != workspace_id:
                    continue
                if asset_type and data.get("asset_type") != asset_type:
                    continue
                if status and data.get("status") != status.value:
                    continue
                if is_favorite is not None and data.get("is_favorite") != is_favorite:
                    continue
                res.append(Asset(**data))
            return sorted(res, key=lambda a: a.updated_at, reverse=True)

    def delete_asset(self, asset_id: str) -> bool:
        with self._lock:
            if asset_id in self._assets:
                del self._assets[asset_id]
                self._atomic_save(self._assets_file, self._assets)
                return True
            return False

    # ─────────────────────────────────────────────────────────────
    # Asset Relationships
    # ─────────────────────────────────────────────────────────────

    def save_relationship(self, rel: AssetRelationship) -> AssetRelationship:
        with self._lock:
            self._relationships[rel.relationship_id] = rel.model_dump()
            self._atomic_save(self._relationships_file, self._relationships)
            return rel

    def get_relationship(self, relationship_id: str) -> Optional[AssetRelationship]:
        with self._lock:
            data = self._relationships.get(relationship_id)
            return AssetRelationship(**data) if data else None

    def list_relationships(
        self,
        source_asset_id: Optional[str] = None,
        target_asset_id: Optional[str] = None,
    ) -> List[AssetRelationship]:
        with self._lock:
            res = []
            for data in self._relationships.values():
                if source_asset_id and data.get("source_asset_id") != source_asset_id:
                    continue
                if target_asset_id and data.get("target_asset_id") != target_asset_id:
                    continue
                res.append(AssetRelationship(**data))
            return res

    def delete_relationship(self, relationship_id: str) -> bool:
        with self._lock:
            if relationship_id in self._relationships:
                del self._relationships[relationship_id]
                self._atomic_save(self._relationships_file, self._relationships)
                return True
            return False

    def delete_relationships_for_asset(self, asset_id: str) -> int:
        with self._lock:
            to_del = [
                rid
                for rid, r in self._relationships.items()
                if r.get("source_asset_id") == asset_id
                or r.get("target_asset_id") == asset_id
            ]
            for rid in to_del:
                del self._relationships[rid]
            if to_del:
                self._atomic_save(self._relationships_file, self._relationships)
            return len(to_del)

    # ─────────────────────────────────────────────────────────────
    # Activity Log
    # ─────────────────────────────────────────────────────────────

    def record_activity(self, activity: ActivityRecord) -> ActivityRecord:
        with self._lock:
            self._activities.append(activity.model_dump())
            self._atomic_save(self._activity_file, self._activities)
            return activity

    def list_activity(
        self,
        project_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[ActivityRecord]:
        with self._lock:
            res = []
            for act in reversed(self._activities):
                if project_id and act.get("project_id") != project_id:
                    continue
                if workspace_id and act.get("workspace_id") != workspace_id:
                    continue
                res.append(ActivityRecord(**act))
                if len(res) >= limit:
                    break
            return res

    def cleanup_activity(self, retention_days: Optional[int] = None) -> int:
        days = retention_days or settings.PROJECT_ACTIVITY_RETENTION_DAYS
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with self._lock:
            initial_count = len(self._activities)
            self._activities = [
                act for act in self._activities if act.get("timestamp", "") >= cutoff
            ]
            removed = initial_count - len(self._activities)
            if removed > 0:
                self._atomic_save(self._activity_file, self._activities)
            return removed


workspace_repo = WorkspaceRepository()

