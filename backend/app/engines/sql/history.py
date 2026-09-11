"""
AnalyzaX — Phase 8: Query Execution History Repository
Provides persistent storage and querying for executed SQL statements in data/sql/history.json.
"""

import json
import os
import threading
from typing import List, Optional

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.sql.models import QueryHistoryEntry


class QueryHistoryRepository:
    """
    Thread-safe repository for query history.
    """

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        self._dir = storage_dir or os.path.abspath(settings.DATA_SQL_DIR)
        os.makedirs(self._dir, exist_ok=True)
        self._filepath = os.path.join(self._dir, "history.json")
        self._lock = threading.Lock()
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not os.path.exists(self._filepath):
            try:
                with open(self._filepath, "w", encoding="utf-8") as f:
                    json.dump([], f)
            except Exception as e:
                logger.error(f"Failed to initialize query history file: {e}")

    def _read_all(self) -> List[dict]:
        try:
            if os.path.exists(self._filepath):
                with open(self._filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading query history: {e}")
        return []

    def _write_all(self, entries: List[dict]) -> None:
        try:
            with open(self._filepath, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error writing query history: {e}")

    def add_entry(self, entry: QueryHistoryEntry) -> None:
        """Appends a new query execution entry to history (capped at 500 entries)."""
        with self._lock:
            entries = self._read_all()
            entries.insert(0, entry.model_dump())
            # Cap at 500 items
            if len(entries) > 500:
                entries = entries[:500]
            self._write_all(entries)

    def list_entries(
        self,
        dataset_id: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
    ) -> List[QueryHistoryEntry]:
        """Lists and filters query history entries."""
        with self._lock:
            raw = self._read_all()

        results: List[QueryHistoryEntry] = []
        for item in raw:
            if dataset_id and item.get("dataset_id") != dataset_id:
                continue
            if status and str(item.get("status", "")).upper() != status.upper():
                continue
            if search and search.lower() not in str(item.get("query_text", "")).lower():
                continue

            results.append(QueryHistoryEntry(**item))
            if len(results) >= limit:
                break

        return results

    def clear(self, dataset_id: Optional[str] = None) -> int:
        """Clears query history for a dataset or completely."""
        with self._lock:
            entries = self._read_all()
            if dataset_id:
                kept = [e for e in entries if e.get("dataset_id") != dataset_id]
                removed = len(entries) - len(kept)
                self._write_all(kept)
                return removed
            else:
                count = len(entries)
                self._write_all([])
                return count


query_history_repo = QueryHistoryRepository()
