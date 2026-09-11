"""
Data Quality Application Service
Coordinates data quality analysis workflows, report caching, and query filtering.
"""

import json
import os
from typing import Optional
from backend.app.core.cache import cache_service, build_cache_key
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.quality.engine import DataQualityEngine
from backend.app.schemas.quality import (
    DataQualityReportResponse,
)
from backend.app.services.dataset_service import dataset_service
from backend.app.services.duckdb_service import duckdb_service
from backend.app.services.profiling_service import profiling_service


class QualityService:
    """
    Application Service orchestrating the Data Quality assessment lifecycle.
    Persists evaluation reports on disk and in-memory cache to provide instant retrieval.
    """

    def __init__(self) -> None:
        self._quality_dir = os.path.abspath(settings.DATA_QUALITY_DIR)
        os.makedirs(self._quality_dir, exist_ok=True)
        self._engine = DataQualityEngine()

    def _get_report_path(self, dataset_id: str) -> str:
        dataset_quality_dir = os.path.join(self._quality_dir, dataset_id)
        os.makedirs(dataset_quality_dir, exist_ok=True)
        return os.path.join(dataset_quality_dir, "report.json")

    def _build_cache_key(self, dataset_id: str) -> str:
        return build_cache_key(
            namespace="quality",
            workspace_id="global",
            operation="report",
            dataset_id=dataset_id,
            engine_version=settings.QUALITY_REPORT_VERSION,
        )

    def get_cached_report(self, dataset_id: str) -> Optional[DataQualityReportResponse]:
        """Loads cached report from memory or disk if version matches current engine version."""
        cache_key = self._build_cache_key(dataset_id)
        mem_cached = cache_service.get(cache_key)
        if mem_cached and isinstance(mem_cached, DataQualityReportResponse):
            return mem_cached

        report_path = self._get_report_path(dataset_id)
        if os.path.exists(report_path):
            try:
                with open(report_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("quality_report_version") == settings.QUALITY_REPORT_VERSION:
                        res = DataQualityReportResponse(**data)
                        cache_service.set(cache_key, res, ttl_seconds=cache_service.SAFE_LONG_TTL)
                        return res
            except Exception as e:
                logger.warning(f"Failed to read cached quality report for {dataset_id}: {e}")
        return None

    def invalidate_quality(self, dataset_id: str) -> None:
        """Invalidates in-memory and disk cached quality reports for a dataset."""
        cache_key = self._build_cache_key(dataset_id)
        cache_service.delete(cache_key)
        report_path = self._get_report_path(dataset_id)
        if os.path.exists(report_path):
            try:
                os.remove(report_path)
            except Exception as e:
                logger.warning(f"Failed to delete disk quality cache for {dataset_id}: {e}")

    def assess_dataset_quality(
        self,
        dataset_id: str,
        force_refresh: bool = False,
        severity_filter: Optional[str] = None,
        dimension_filter: Optional[str] = None,
        column_filter: Optional[str] = None,
    ) -> DataQualityReportResponse:
        """
        Runs or retrieves Data Quality report for a dataset, applying optional filters.
        """
        cache_key = self._build_cache_key(dataset_id)
        if force_refresh:
            self.invalidate_quality(dataset_id)

        report: Optional[DataQualityReportResponse] = None
        if not force_refresh:
            report = self.get_cached_report(dataset_id)

        if not report:
            # 1. Verify dataset exists and is in READY state
            dataset_meta = dataset_service.get_dataset(dataset_id)
            if not dataset_meta:
                raise ValueError(f"Dataset with ID '{dataset_id}' not found.")

            if dataset_meta.status != "READY":
                raise ValueError(
                    f"Dataset '{dataset_id}' is not ready for quality assessment (status: {dataset_meta.status})."
                )

            # 2. Ensure Phase 4 profile exists
            profile = profiling_service.profile_dataset(dataset_id)

            # 3. Execute quality rules against DuckDB table
            table_name = dataset_meta.duckdb_table_name
            with duckdb_service.get_connection() as conn:
                raw_report = self._engine.evaluate(
                    conn=conn,
                    table_name=table_name,
                    profile=profile,
                )

            # 4. Persist report to disk
            report_path = self._get_report_path(dataset_id)
            try:
                with open(report_path, "w", encoding="utf-8") as f:
                    json.dump(raw_report.model_dump(), f, indent=2)
                logger.info(f"Persisted data quality report for dataset {dataset_id} to {report_path}")
            except Exception as e:
                logger.error(f"Failed to persist quality report for {dataset_id}: {e}")

            report = DataQualityReportResponse(**raw_report.model_dump())

        # Apply optional filtering on issues list if requested
        if severity_filter or dimension_filter or column_filter:
            filtered_issues = report.issues
            if severity_filter:
                sev_upper = severity_filter.upper()
                filtered_issues = [i for i in filtered_issues if i.severity.value == sev_upper]
            if dimension_filter:
                dim_upper = dimension_filter.upper()
                filtered_issues = [i for i in filtered_issues if i.dimension.value == dim_upper]
            if column_filter:
                col_lower = column_filter.lower()
                filtered_issues = [i for i in filtered_issues if i.column_name and i.column_name.lower() == col_lower]

            # Return filtered view
            report_dict = report.model_dump()
            report_dict["issues"] = [i.model_dump() for i in filtered_issues]
            return DataQualityReportResponse(**report_dict)

        return report


quality_service = QualityService()
