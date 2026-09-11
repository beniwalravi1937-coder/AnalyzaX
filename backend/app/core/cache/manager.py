"""
AnalyzaX — Phase 23: Centralized Caching Architecture.
Provides thread-safe in-memory LRU caching with TTL, single-flight stampede protection,
namespace invalidation, and resilient fail-safe fallback.
"""

import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.metrics import metrics_collector

T = TypeVar("T")


class _SingleFlightCall:
    def __init__(self) -> None:
        self.event = threading.Event()
        self.val: Any = None
        self.err: Optional[Exception] = None


class SingleFlight:
    """
    Suppresses duplicate concurrent in-flight computations for identical cache keys.
    If 50 requests miss cache key 'X' simultaneously, only 1 computes; 49 wait and share the result.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._m: Dict[str, _SingleFlightCall] = {}

    def execute(self, key: str, fn: Callable[[], T]) -> T:
        with self._lock:
            if key in self._m:
                c = self._m[key]
                is_leader = False
            else:
                c = _SingleFlightCall()
                self._m[key] = c
                is_leader = True

        if not is_leader:
            # Follower waits for leader to finish
            timeout = getattr(settings, "CACHE_STAMPEDE_TIMEOUT_SEC", 30.0)
            signaled = c.event.wait(timeout=timeout)
            if not signaled:
                # Timed out waiting for leader, compute fallback
                return fn()
            if c.err is not None:
                raise c.err
            return c.val

        try:
            c.val = fn()
            return c.val
        except Exception as e:
            c.err = e
            raise e
        finally:
            with self._lock:
                c.event.set()
                self._m.pop(key, None)


class CacheService:
    """
    Centralized caching abstraction for AnalyzaX.
    Guarantees:
    - Never bypasses authorization or billing quotas.
    - Resilient: Cache failure bypasses cache safely to authoritative source.
    - Thread-safe in-memory LRU with TTL eviction.
    """

    SAFE_LONG_TTL: int = 86400    # 24 hours (version-bound deterministic analytical results)
    SAFE_SHORT_TTL: int = 60      # 1 minute (catalogs, non-critical metrics)
    DEFAULT_MAX_ENTRIES: int = 5000

    def __init__(self, max_entries: Optional[int] = None) -> None:
        self.max_entries = max_entries or getattr(settings, "CACHE_MAX_ENTRIES", self.DEFAULT_MAX_ENTRIES)
        self._lock = threading.Lock()
        # Key -> (value, expiry_timestamp_float, created_timestamp_float)
        self._store: Dict[str, Tuple[Any, float, float]] = {}
        self._single_flight = SingleFlight()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "evictions": 0,
        }

    def get(self, key: str) -> Optional[Any]:
        """Retrieves an item from cache if present and unexpired."""
        with self._lock:
            if key not in self._store:
                self._stats["misses"] += 1
                self._record_metric_miss(key)
                return None

            val, expiry, _ = self._store[key]
            now = time.time()
            if expiry > 0 and now > expiry:
                # Expired
                self._store.pop(key, None)
                self._stats["misses"] += 1
                self._record_metric_miss(key)
                return None

            # Refresh access timestamp for true LRU eviction
            self._store[key] = (val, expiry, now)
            self._stats["hits"] += 1
            self._record_metric_hit(key)
            return val

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """Stores an item in cache with optional TTL."""
        now = time.time()
        expiry = now + ttl_seconds if ttl_seconds and ttl_seconds > 0 else 0.0

        with self._lock:
            # Enforce LRU eviction if capacity reached
            if len(self._store) >= self.max_entries and key not in self._store:
                self._evict_oldest()

            self._store[key] = (value, expiry, now)

    def delete(self, key: str) -> bool:
        """Removes an item from cache."""
        with self._lock:
            if key in self._store:
                self._store.pop(key, None)
                return True
            return False

    def get_or_set(
        self,
        key: str,
        factory_func: Callable[[], T],
        ttl_seconds: Optional[int] = None,
        use_stampede_protection: bool = True,
    ) -> T:
        """
        Thread-safe get-or-compute pattern with single-flight stampede protection.
        If cache fails, falls back gracefully to factory_func() without throwing.
        """
        try:
            val = self.get(key)
            if val is not None:
                return val
        except Exception as e:
            logger.warning(f"Cache get failed for key [{key}]: {e}")
            self._stats["errors"] += 1
            return factory_func()

        # Cache miss - compute via single flight
        try:
            if use_stampede_protection:
                computed = self._single_flight.execute(key, factory_func)
            else:
                computed = factory_func()

            self.set(key, computed, ttl_seconds=ttl_seconds)
            return computed
        except Exception as e:
            logger.error(f"Computation failed during get_or_set for [{key}]: {e}")
            raise e

    def invalidate_namespace(self, namespace: str) -> int:
        """Invalidates all keys starting with the given namespace prefix (e.g. 'profile:', 'eda:')."""
        prefix = f"{namespace}:" if not namespace.endswith(":") else namespace
        count = 0
        with self._lock:
            keys_to_delete = [k for k in self._store if k.startswith(prefix) or k.startswith(namespace)]
            for k in keys_to_delete:
                self._store.pop(k, None)
                count += 1
        logger.info(f"Invalidated {count} cache entries for namespace [{namespace}]")
        return count

    def invalidate_pattern(self, match_substring: str) -> int:
        """Invalidates all keys containing match_substring (e.g. dataset_id or version_id)."""
        count = 0
        with self._lock:
            keys_to_delete = [k for k in self._store if match_substring in k]
            for k in keys_to_delete:
                self._store.pop(k, None)
                count += 1
        logger.info(f"Invalidated {count} cache entries matching pattern [{match_substring}]")
        return count

    def clear(self) -> int:
        """Clears entire cache store and returns number of cleared entries."""
        with self._lock:
            count = len(self._store)
            self._store.clear()
            logger.info(f"Cleared entire cache store ({count} entries).")
            return count

    def get_stats(self) -> Dict[str, Any]:
        """Returns diagnostic telemetry for cache performance."""
        with self._lock:
            total_lookups = self._stats["hits"] + self._stats["misses"]
            hit_ratio_pct = round((self._stats["hits"] / total_lookups) * 100, 2) if total_lookups > 0 else 0.0
            hit_ratio = round(self._stats["hits"] / total_lookups, 4) if total_lookups > 0 else 0.0
            return {
                "size": len(self._store),
                "total_entries": len(self._store),
                "max_entries": self.max_entries,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "errors": self._stats["errors"],
                "evictions": self._stats["evictions"],
                "hit_ratio": hit_ratio,
                "hit_ratio_percent": hit_ratio_pct,
            }

    def _evict_oldest(self) -> None:
        """Evicts expired or oldest entries based on creation timestamp."""
        now = time.time()
        # 1. First sweep expired items
        expired = [k for k, (_, exp, _) in self._store.items() if exp > 0 and now > exp]
        if expired:
            for k in expired:
                self._store.pop(k, None)
                self._stats["evictions"] += 1
            return

        # 2. Otherwise evict oldest 10%
        batch_size = max(1, len(self._store) // 10)
        sorted_keys = sorted(self._store.keys(), key=lambda k: self._store[k][2])
        for k in sorted_keys[:batch_size]:
            self._store.pop(k, None)
            self._stats["evictions"] += 1

    def _record_metric_hit(self, key: str) -> None:
        ns = key.split(":")[0] if ":" in key else "default"
        try:
            if hasattr(metrics_collector, "record_cache_hit"):
                metrics_collector.record_cache_hit(ns)
        except Exception:
            pass

    def _record_metric_miss(self, key: str) -> None:
        ns = key.split(":")[0] if ":" in key else "default"
        try:
            if hasattr(metrics_collector, "record_cache_miss"):
                metrics_collector.record_cache_miss(ns)
        except Exception:
            pass


# Global singleton instance
cache_service = CacheService()
