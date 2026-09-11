"""
AnalyzaX — Phase 8: Saved Queries Repository
Provides persistent storage and CRUD operations for saved SQL queries in data/sql/saved_queries.json.
"""

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.sql.models import (
    SavedQuery,
    SavedQueryCreateRequest,
    SavedQueryUpdateRequest,
)


class SavedQueryRepository:
    """
    Thread-safe repository for saved queries.
    """

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        self._dir = storage_dir or os.path.abspath(settings.DATA_SQL_DIR)
        os.makedirs(self._dir, exist_ok=True)
        self._filepath = os.path.join(self._dir, "saved_queries.json")
        self._lock = threading.Lock()
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not os.path.exists(self._filepath):
            try:
                with open(self._filepath, "w", encoding="utf-8") as f:
                    json.dump([], f)
            except Exception as e:
                logger.error(f"Failed to initialize saved queries file: {e}")

    def _read_all(self) -> List[dict]:
        try:
            if os.path.exists(self._filepath):
                with open(self._filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading saved queries: {e}")
        return []

    def _write_all(self, entries: List[dict]) -> None:
        try:
            with open(self._filepath, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error writing saved queries: {e}")

    def create(self, req: SavedQueryCreateRequest) -> SavedQuery:
        now = datetime.now(timezone.utc).isoformat()
        saved = SavedQuery(
            id=str(uuid.uuid4()),
            name=req.name,
            description=req.description,
            dataset_id=req.dataset_id,
            version_scope=req.version_scope,
            sql=req.sql,
            tags=req.tags,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            all_queries = self._read_all()
            all_queries.insert(0, saved.model_dump())
            self._write_all(all_queries)
        return saved

    def get(self, query_id: str) -> Optional[SavedQuery]:
        with self._lock:
            all_queries = self._read_all()
        for q in all_queries:
            if q.get("id") == query_id:
                return SavedQuery(**q)
        return None

    def list(self, dataset_id: Optional[str] = None, tag: Optional[str] = None) -> List[SavedQuery]:
        with self._lock:
            all_queries = self._read_all()

        results = []
        for q in all_queries:
            if dataset_id and q.get("dataset_id") != dataset_id:
                continue
            if tag and tag not in q.get("tags", []):
                continue
            results.append(SavedQuery(**q))
        return results

    def update(self, query_id: str, req: SavedQueryUpdateRequest) -> Optional[SavedQuery]:
        with self._lock:
            all_queries = self._read_all()
            found_idx = None
            for idx, q in enumerate(all_queries):
                if q.get("id") == query_id:
                    found_idx = idx
                    break

            if found_idx is None:
                return None

            item = all_queries[found_idx]
            if req.name is not None:
                item["name"] = req.name
            if req.description is not None:
                item["description"] = req.description
            if req.sql is not None:
                item["sql"] = req.sql
            if req.version_scope is not None:
                item["version_scope"] = req.version_scope
            if req.tags is not None:
                item["tags"] = req.tags
            item["updated_at"] = datetime.now(timezone.utc).isoformat()

            all_queries[found_idx] = item
            self._write_all(all_queries)
            return SavedQuery(**item)

    def delete(self, query_id: str) -> bool:
        with self._lock:
            all_queries = self._read_all()
            new_queries = [q for q in all_queries if q.get("id") != query_id]
            if len(new_queries) != len(all_queries):
                self._write_all(new_queries)
                return True
        return False


saved_queries_repo = SavedQueryRepository()
