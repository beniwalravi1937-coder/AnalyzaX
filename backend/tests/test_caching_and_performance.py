"""
AnalyzaX — Phase 23: Caching, Query Optimization & Performance Tests
Tests LRU cache eviction, TTL expiry, single-flight stampede protection,
deterministic cache key generation, cross-version isolation, and engine integration.
"""

import time
import threading
from typing import Any, Dict
import pytest

from backend.app.core.cache import (
    CacheService,
    SingleFlight,
    build_cache_key,
)
from backend.app.core.metrics import metrics_collector


class TestCacheKeyBuilder:
    """Validates deterministic, collision-resistant, order-invariant cache key generation."""

    def test_deterministic_key_generation(self):
        k1 = build_cache_key(
            namespace="profile",
            workspace_id="ws_1",
            operation="full",
            dataset_id="ds_123",
            version_id="v1",
            params={"a": 1, "b": "test"},
            engine_version="2.0.0",
        )
        k2 = build_cache_key(
            namespace="profile",
            workspace_id="ws_1",
            operation="full",
            dataset_id="ds_123",
            version_id="v1",
            params={"b": "test", "a": 1},  # reversed param order
            engine_version="2.0.0",
        )
        assert k1 == k2
        assert k1.startswith("profile:ws_1:ds_123:v1:full:")

    def test_version_isolation_in_keys(self):
        k_v1 = build_cache_key(
            namespace="eda",
            workspace_id="ws_1",
            operation="report",
            dataset_id="ds_1",
            version_id="v1",
        )
        k_v2 = build_cache_key(
            namespace="eda",
            workspace_id="ws_1",
            operation="report",
            dataset_id="ds_1",
            version_id="v2",
        )
        assert k_v1 != k_v2

    def test_workspace_isolation_in_keys(self):
        k_ws1 = build_cache_key(
            namespace="query",
            workspace_id="ws_alpha",
            operation="sql",
            dataset_id="ds_1",
            version_id="v1",
        )
        k_ws2 = build_cache_key(
            namespace="query",
            workspace_id="ws_beta",
            operation="sql",
            dataset_id="ds_1",
            version_id="v1",
        )
        assert k_ws1 != k_ws2


class TestSingleFlightStampedeProtection:
    """Validates that concurrent requests for the exact same key execute the heavy computation only once."""

    def test_single_flight_deduplication(self):
        sf = SingleFlight()
        execution_count = 0
        lock = threading.Lock()

        def slow_heavy_task():
            nonlocal execution_count
            time.sleep(0.08)
            with lock:
                execution_count += 1
            return "computed_result_42"

        results = []
        threads = []

        def worker():
            res = sf.execute("same_key", slow_heavy_task)
            results.append(res)

        # Launch 5 threads simultaneously
        for _ in range(5):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert execution_count == 1, f"Expected exactly 1 execution, got {execution_count}"
        assert len(results) == 5
        assert all(r == "computed_result_42" for r in results)


class TestCacheServiceLRUAndTTL:
    """Validates CacheService memory management, LRU eviction, and TTL expiration."""

    def test_basic_get_set_delete(self):
        cache = CacheService(max_entries=10)
        cache.set("k1", {"data": 123}, ttl_seconds=10.0)
        assert cache.get("k1") == {"data": 123}

        cache.delete("k1")
        assert cache.get("k1") is None

    def test_ttl_expiration(self):
        cache = CacheService(max_entries=10)
        cache.set("k_expire", "val", ttl_seconds=0.05)
        assert cache.get("k_expire") == "val"

        time.sleep(0.08)
        assert cache.get("k_expire") is None

    def test_lru_eviction(self):
        cache = CacheService(max_entries=3)
        cache.set("k1", 1)
        time.sleep(0.01)
        cache.set("k2", 2)
        time.sleep(0.01)
        cache.set("k3", 3)
        time.sleep(0.01)

        # Access k1 so k2 becomes least recently used
        _ = cache.get("k1")
        time.sleep(0.01)

        # Insert k4, should evict k2
        cache.set("k4", 4)
        assert cache.get("k1") == 1
        assert cache.get("k3") == 3
        assert cache.get("k4") == 4
        assert cache.get("k2") is None

    def test_namespace_invalidation(self):
        cache = CacheService(max_entries=20)
        cache.set("profile:ws1:ds1:v1:hash1", "prof1")
        cache.set("profile:ws1:ds2:v1:hash2", "prof2")
        cache.set("eda:ws1:ds1:v1:hash3", "eda1")

        cleared = cache.invalidate_namespace("profile")
        assert cleared == 2
        assert cache.get("profile:ws1:ds1:v1:hash1") is None
        assert cache.get("profile:ws1:ds2:v1:hash2") is None
        assert cache.get("eda:ws1:ds1:v1:hash3") == "eda1"

    def test_pattern_invalidation(self):
        cache = CacheService(max_entries=20)
        cache.set("profile:ws1:target_ds:v1:h1", "prof1")
        cache.set("eda:ws1:target_ds:v1:h2", "eda1")
        cache.set("eda:ws1:other_ds:v1:h3", "eda2")

        cleared = cache.invalidate_pattern("target_ds")
        assert cleared == 2
        assert cache.get("profile:ws1:target_ds:v1:h1") is None
        assert cache.get("eda:ws1:target_ds:v1:h2") is None
        assert cache.get("eda:ws1:other_ds:v1:h3") == "eda2"

    def test_get_or_set_stampede_protection(self):
        cache = CacheService(max_entries=10)
        counter = 0

        def slow_calc():
            nonlocal counter
            time.sleep(0.05)
            counter += 1
            return 999

        threads = []
        outputs = []

        def worker():
            val = cache.get_or_set("shared_calc_key", slow_calc, ttl_seconds=10.0)
            outputs.append(val)

        for _ in range(4):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert counter == 1
        assert len(outputs) == 4
        assert all(v == 999 for v in outputs)

    def test_stats_reporting(self):
        cache = CacheService(max_entries=50)
        cache.set("a", 1)
        _ = cache.get("a")  # hit
        _ = cache.get("nonexistent")  # miss

        stats = cache.get_stats()
        assert stats["total_entries"] == 1
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1
        assert 0.0 <= stats["hit_ratio"] <= 1.0
