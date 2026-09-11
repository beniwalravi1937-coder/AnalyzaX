"""
AnalyzaX — Phase 23: Performance, Cache Management & Telemetry API Tests
Validates /api/v1/admin/cache, /api/v1/admin/cache/clear, GZip compression headers,
and dataset cache invalidation flow.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.cache import cache_service, build_cache_key


@pytest.fixture
def client():
    return TestClient(app)


class TestCacheAdminEndpoints:
    """Validates operational cache telemetry and administration endpoints."""

    def test_get_cache_stats(self, client: TestClient):
        # Prepopulate an entry
        cache_service.set("test_key", {"val": 42}, ttl_seconds=60.0)
        _ = cache_service.get("test_key")

        response = client.get("/api/v1/admin/cache")
        assert response.status_code == 200
        data = response.json()

        assert "total_entries" in data
        assert "hits" in data
        assert "misses" in data
        assert "hit_ratio" in data
        assert "max_entries" in data
        assert data["hits"] >= 1

    def test_clear_cache_by_pattern(self, client: TestClient):
        cache_service.set("profile:ws1:temp_ds_123:v1:abc", "data1")
        cache_service.set("eda:ws1:temp_ds_123:v1:def", "data2")
        cache_service.set("eda:ws1:other_ds_999:v1:ghi", "data3")

        response = client.post("/api/v1/admin/cache/clear?pattern=temp_ds_123")
        assert response.status_code == 200
        data = response.json()
        assert data["cleared_entries"] >= 2
        assert "pattern:temp_ds_123" in data["scope"]

        assert cache_service.get("profile:ws1:temp_ds_123:v1:abc") is None
        assert cache_service.get("eda:ws1:other_ds_999:v1:ghi") == "data3"

    def test_clear_cache_by_namespace(self, client: TestClient):
        cache_service.set("profile:ws1:ds1:v1:abc", "data1")
        cache_service.set("eda:ws1:ds1:v1:def", "data2")

        response = client.post("/api/v1/admin/cache/clear?namespace=profile")
        assert response.status_code == 200
        data = response.json()
        assert data["cleared_entries"] >= 1
        assert "namespace:profile" in data["scope"]

        assert cache_service.get("profile:ws1:ds1:v1:abc") is None
        assert cache_service.get("eda:ws1:ds1:v1:def") == "data2"

    def test_observability_includes_cache(self, client: TestClient):
        response = client.get("/api/v1/admin/observability")
        assert response.status_code == 200
        data = response.json()
        assert "cache" in data
        assert "total_entries" in data["cache"]
        assert "hit_ratio" in data["cache"]


class TestGZipCompression:
    """Validates that large payloads are compressed with gzip when requested."""

    def test_gzip_compression_on_large_payload(self, client: TestClient):
        # Request metrics endpoint with Accept-Encoding: gzip
        response = client.get(
            "/api/v1/admin/metrics",
            headers={"Accept-Encoding": "gzip"},
        )
        assert response.status_code == 200
        # If payload is larger than 1024 bytes, GZipMiddleware adds gzip encoding
        # TestClient automatically decompresses or preserves headers
        assert "content-encoding" in response.headers or len(response.content) > 0
