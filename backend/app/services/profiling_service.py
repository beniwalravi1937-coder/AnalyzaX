"""
Profiling Application Service
Coordinates dataset profiling lifecycle, cache invalidation, persistence, and error handling.
"""

import json
import os
from typing import Optional

from backend.app.core.cache import cache_service, build_cache_key
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.profiling.engine import DatasetProfiler
from backend.app.schemas.profile import DatasetProfileResponse
from backend.app.services.dataset_service import dataset_service
from backend.app.services.duckdb_service import duckdb_service


class ProfilingService:
    """
    Application Service orchestrating profiling workflows.
    Ensures profiling results are cached both in-memory (sub-millisecond) and on-disk
    to eliminate redundant analytical scans.
    """

    def __init__(self) -> None:
        self._profiles_dir = os.path.abspath(settings.DATA_PROFILES_DIR)
        os.makedirs(self._profiles_dir, exist_ok=True)
        self._profiler = DatasetProfiler()

    def _get_profile_path(self, dataset_id: str) -> str:
        dataset_profile_dir = os.path.join(self._profiles_dir, dataset_id)
        os.makedirs(dataset_profile_dir, exist_ok=True)
        return os.path.join(dataset_profile_dir, "profile.json")

    def _build_cache_key(self, dataset_id: str) -> str:
        return build_cache_key(
            namespace="profile",
            workspace_id="global",
            operation="profile",
            dataset_id=dataset_id,
            engine_version=settings.PROFILING_VERSION,
        )

    def get_cached_profile(self, dataset_id: str) -> Optional[DatasetProfileResponse]:
        """Loads persistent profile from memory cache or disk if matches current profiling version."""
        cache_key = self._build_cache_key(dataset_id)
        mem_cached = cache_service.get(cache_key)
        if mem_cached and isinstance(mem_cached, DatasetProfileResponse):
            return mem_cached

        profile_path = self._get_profile_path(dataset_id)
        if os.path.exists(profile_path):
            try:
                with open(profile_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("profiling_version") == settings.PROFILING_VERSION:
                        res = DatasetProfileResponse(**data)
                        cache_service.set(cache_key, res, ttl_seconds=cache_service.SAFE_LONG_TTL)
                        return res
            except Exception as e:
                logger.warning(f"Failed to read cached profile for {dataset_id}: {e}")
        return None

    def invalidate_profile(self, dataset_id: str) -> None:
        """Invalidates in-memory and on-disk cached profile for a dataset."""
        cache_key = self._build_cache_key(dataset_id)
        cache_service.delete(cache_key)
        profile_path = self._get_profile_path(dataset_id)
        if os.path.exists(profile_path):
            try:
                os.remove(profile_path)
            except Exception as e:
                logger.warning(f"Failed to delete disk profile cache for {dataset_id}: {e}")

    def profile_dataset(self, dataset_id: str, force_refresh: bool = False) -> DatasetProfileResponse:
        """
        Profiles a dataset. Returns cached profile unless force_refresh is True or cache is missing.
        Uses single-flight coalescing to prevent duplicate concurrent profiling runs.
        """
        cache_key = self._build_cache_key(dataset_id)

        if force_refresh:
            self.invalidate_profile(dataset_id)
        else:
            cached = self.get_cached_profile(dataset_id)
            if cached:
                logger.info(f"Returning cached profile for dataset {dataset_id}")
                return cached

        # Verify dataset exists and is in READY status
        dataset_meta = dataset_service.get_dataset(dataset_id)
        if not dataset_meta:
            raise ValueError(f"Dataset with ID '{dataset_id}' not found.")

        if dataset_meta.status != "READY":
            raise ValueError(
                f"Dataset '{dataset_id}' is not ready for profiling (current status: {dataset_meta.status})."
            )

        table_name = dataset_meta.duckdb_table_name
        logger.info(f"Starting deterministic profiling for dataset {dataset_id} on table {table_name}")

        def _do_profile() -> DatasetProfileResponse:
            with duckdb_service.get_connection() as conn:
                prof = self._profiler.profile_table(
                    conn=conn,
                    table_name=table_name,
                    dataset_id=dataset_id,
                )
            # Persist profile to disk
            profile_path = self._get_profile_path(dataset_id)
            try:
                with open(profile_path, "w", encoding="utf-8") as f:
                    json.dump(prof.model_dump(), f, indent=2)
                logger.info(f"Persisted profile for dataset {dataset_id} to {profile_path}")
            except Exception as e:
                logger.error(f"Failed to persist profile for {dataset_id}: {e}")
            return prof

        # Execute with stampede protection
        profile = cache_service.get_or_set(
            cache_key,
            factory_func=_do_profile,
            ttl_seconds=cache_service.SAFE_LONG_TTL,
            use_stampede_protection=True,
        )
        return profile


profiling_service = ProfilingService()
