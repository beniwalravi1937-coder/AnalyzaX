"""
AnalyzaX — Phase 8: Query Result Cache
Thread-safe in-memory cache for deterministic read-only query results against
immutable dataset versions.
"""

import threading
import time
from typing import Dict, Optional, Tuple
from backend.app.engines.sql.models import SQLQueryResponse


class QueryResultCache:
    """
    In-memory LRU-style cache for SQL query responses.
    """

    def __init__(self, max_size: int = 100, default_ttl_seconds: float = 300.0) -> None:
        self._max_size = max_size
        self._default_ttl = default_ttl_seconds
        self._lock = threading.Lock()
        # Key: (dataset_id, version_id, query_hash) -> (response, expiry_timestamp)
        self._cache: Dict[Tuple[str, str, str], Tuple[SQLQueryResponse, float]] = {}

    def get(self, dataset_id: str, version_id: str, query_hash: str) -> Optional[SQLQueryResponse]:
        key = (dataset_id, version_id, query_hash)
        with self._lock:
            if key in self._cache:
                resp, expiry = self._cache[key]
                if time.time() < expiry:
                    # Return cached copy with cached=True
                    cached_copy = resp.model_copy(deep=True)
                    cached_copy.cached = True
                    from backend.app.core.metrics import metrics_collector
                    metrics_collector.record_cache_hit("sql")
                    return cached_copy
                else:
                    self._cache.pop(key, None)
        from backend.app.core.metrics import metrics_collector
        metrics_collector.record_cache_miss("sql")
        return None

    def set(
        self,
        dataset_id: str,
        version_id: str,
        query_hash: str,
        response: SQLQueryResponse,
        ttl_seconds: Optional[float] = None,
    ) -> None:
        key = (dataset_id, version_id, query_hash)
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        expiry = time.time() + ttl

        with self._lock:
            if len(self._cache) >= self._max_size:
                # Evict oldest entry
                oldest_key = next(iter(self._cache))
                self._cache.pop(oldest_key, None)
            self._cache[key] = (response, expiry)

    def invalidate(self, dataset_id: Optional[str] = None) -> None:
        """Invalidates entries for a dataset or clears entire cache."""
        with self._lock:
            if dataset_id:
                keys_to_remove = [k for k in self._cache if k[0] == dataset_id]
                for k in keys_to_remove:
                    self._cache.pop(k, None)
            else:
                self._cache.clear()
        from backend.app.core.cache import cache_service
        if dataset_id:
            cache_service.invalidate_pattern(dataset_id)
        else:
            cache_service.invalidate_namespace("sql")


query_cache = QueryResultCache()
