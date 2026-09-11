"""
AnalyzaX — Phase 7: EDA Application Service
Coordinates EDA computation, caching, interactive column/relationship drilldown,
and findings extraction for dataset versions.
"""

import json
import os
from typing import Any, Dict, List, Optional
import polars as pl

from backend.app.core.cache import cache_service, build_cache_key
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.eda.analyzers import (
    CategoricalAnalyzer,
    DatetimeAnalyzer,
    NumericAnalyzer,
)
from backend.app.engines.eda.chart_builder import ChartBuilder
from backend.app.engines.eda.engine import EDAEngine
from backend.app.engines.eda.models import (
    ChartOptions,
    ChartSpec,
    ChartType,
    EDAFinding,
    EDAReport,
    FindingCategory,
    FindingSeverity,
    RelationshipQueryResponse,
)
from backend.app.services.cleaning.version_service import VersionService
from backend.app.services.dataset_service import dataset_service
from backend.app.services.quality_service import QualityService


class EDAService:
    """
    Application Service orchestrating the Exploratory Data Analysis lifecycle.
    Persists evaluation reports on disk and in-memory cache to provide instant retrieval.
    """

    def __init__(self) -> None:
        self._eda_dir = os.path.abspath(settings.DATA_EDA_DIR)
        os.makedirs(self._eda_dir, exist_ok=True)
        self._version_service = VersionService()
        self._quality_service = QualityService()

    def _get_report_path(self, dataset_id: str, version_id: str) -> str:
        version_eda_dir = os.path.join(self._eda_dir, dataset_id, version_id)
        os.makedirs(version_eda_dir, exist_ok=True)
        return os.path.join(version_eda_dir, "report.json")

    def _build_cache_key(self, dataset_id: str, version_id: str) -> str:
        return build_cache_key(
            namespace="eda",
            workspace_id="global",
            operation="report",
            dataset_id=dataset_id,
            version_id=version_id,
            engine_version=settings.EDA_VERSION,
        )

    def get_cached_report(self, dataset_id: str, version_id: str) -> Optional[EDAReport]:
        """Loads cached report from memory or disk if version matches current engine version."""
        cache_key = self._build_cache_key(dataset_id, version_id)
        mem_cached = cache_service.get(cache_key)
        if mem_cached and isinstance(mem_cached, EDAReport):
            return mem_cached

        report_path = self._get_report_path(dataset_id, version_id)
        if os.path.exists(report_path):
            try:
                with open(report_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("eda_version") == settings.EDA_VERSION:
                        rep = EDAReport(**data)
                        cache_service.set(cache_key, rep, ttl_seconds=cache_service.SAFE_LONG_TTL)
                        return rep
            except Exception as e:
                logger.warning(f"Failed to read cached EDA report for {dataset_id}/{version_id}: {e}")
        return None

    def invalidate_eda(self, dataset_id: str, version_id: Optional[str] = None) -> None:
        """Invalidates in-memory and disk cached EDA reports."""
        if version_id:
            cache_key = self._build_cache_key(dataset_id, version_id)
            cache_service.delete(cache_key)
            report_path = self._get_report_path(dataset_id, version_id)
            if os.path.exists(report_path):
                try:
                    os.remove(report_path)
                except Exception as e:
                    logger.warning(f"Failed to delete disk EDA cache: {e}")
        else:
            cache_service.invalidate_pattern(dataset_id)

    def _save_report(self, dataset_id: str, version_id: str, report: EDAReport) -> None:
        report_path = self._get_report_path(dataset_id, version_id)
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report.model_dump(), f, indent=2, default=str)
            cache_key = self._build_cache_key(dataset_id, version_id)
            cache_service.set(cache_key, report, ttl_seconds=cache_service.SAFE_LONG_TTL)
        except Exception as e:
            logger.error(f"Failed to persist EDA report for {dataset_id}/{version_id}: {e}")
        except Exception as e:
            logger.error(f"Failed to persist EDA report for {dataset_id}/{version_id}: {e}")

    def get_or_create_eda_report(
        self,
        dataset_id: str,
        version_id: Optional[str] = None,
        force_refresh: bool = False,
    ) -> EDAReport:
        """
        Retrieves existing EDA report or computes a fresh deterministic analysis.
        """
        # 1. Resolve dataset metadata
        ds = dataset_service.get_dataset(dataset_id)
        if not ds:
            raise ValueError(f"Dataset '{dataset_id}' not found.")

        # 2. Resolve version
        if not version_id:
            active_v = self._version_service.get_active_version(dataset_id)
            version_id = active_v.version_id

        # 3. Check disk cache
        if not force_refresh:
            cached = self.get_cached_report(dataset_id, version_id)
            if cached:
                return cached

        # 4. Load version DataFrame
        df = self._version_service.get_version_dataframe(dataset_id, version_id)

        # 5. Retrieve quality score and anomalies if available
        quality_score = None
        anomalies_count = 0
        quality_timestamp = None
        try:
            cached_quality = self._quality_service.get_cached_report(dataset_id)
            if cached_quality:
                quality_score = cached_quality.overall_score
                anomalies_count = len(cached_quality.issues)
                quality_timestamp = cached_quality.generated_at
        except Exception:
            pass

        # 6. Run deterministic EDA engine
        v_meta = self._version_service.get_version(dataset_id, version_id)
        storage_bytes = v_meta.file_size_bytes if v_meta else None

        report = EDAEngine.run_eda(
            df=df,
            dataset_id=dataset_id,
            version_id=version_id,
            quality_score=quality_score,
            anomalies_count=anomalies_count,
            storage_size_bytes=storage_bytes,
            quality_timestamp=quality_timestamp,
        )

        # 7. Persist report to disk
        self._save_report(dataset_id, version_id, report)

        return report

    def get_column_analysis(
        self,
        dataset_id: str,
        column: str,
        version_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Interactive single-column deep drilldown with statistics and charts.
        """
        if not version_id:
            version_id = self._version_service.get_active_version(dataset_id).version_id

        df = self._version_service.get_version_dataframe(dataset_id, version_id)
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in dataset '{dataset_id}' ({version_id}).")

        series = df[column]
        dtype = series.dtype
        is_numeric = dtype.is_numeric()
        is_temporal = dtype.is_temporal()

        charts: List[ChartSpec] = []
        stats_payload: Dict[str, Any] = {}

        if is_numeric:
            num_res = NumericAnalyzer.analyze(df, column)
            if num_res:
                stats_payload = num_res.model_dump()
                all_charts = ChartBuilder.build_all_charts(
                    dataset_id=dataset_id,
                    version_id=version_id,
                    numeric_analyses=[num_res],
                    categorical_analyses=[],
                    datetime_analyses=[],
                    correlation=None,
                    numeric_relationships=[],
                    missingness=None,
                )
                charts.extend(all_charts)
        elif is_temporal:
            dt_res = DatetimeAnalyzer.analyze(df, column)
            if dt_res:
                stats_payload = dt_res.model_dump()
                all_charts = ChartBuilder.build_all_charts(
                    dataset_id=dataset_id,
                    version_id=version_id,
                    numeric_analyses=[],
                    categorical_analyses=[],
                    datetime_analyses=[dt_res],
                    correlation=None,
                    numeric_relationships=[],
                    missingness=None,
                )
                charts.extend(all_charts)
        else:
            cat_res = CategoricalAnalyzer.analyze(df, column)
            if cat_res:
                stats_payload = cat_res.model_dump()
                all_charts = ChartBuilder.build_all_charts(
                    dataset_id=dataset_id,
                    version_id=version_id,
                    numeric_analyses=[],
                    categorical_analyses=[cat_res],
                    datetime_analyses=[],
                    correlation=None,
                    numeric_relationships=[],
                    missingness=None,
                )
                charts.extend(all_charts)

        sample_values = [
            str(val) if val is not None else None
            for val in series.head(10).to_list()
        ]

        return {
            "column": column,
            "data_type": str(dtype),
            "is_numeric": is_numeric,
            "is_temporal": is_temporal,
            "statistics": stats_payload,
            "sample_values": sample_values,
            "charts": [c.model_dump() for c in charts],
        }

    def analyze_relationship(
        self,
        dataset_id: str,
        col_x: str,
        col_y: str,
        version_id: Optional[str] = None,
    ) -> RelationshipQueryResponse:
        """
        Interactive pairwise relationship analysis between any two dataset features.
        """
        if not version_id:
            version_id = self._version_service.get_active_version(dataset_id).version_id

        df = self._version_service.get_version_dataframe(dataset_id, version_id)
        return EDAEngine.analyze_interactive_relationship(
            df=df,
            col_x=col_x,
            col_y=col_y,
            dataset_id=dataset_id,
            version_id=version_id,
        )

    def get_findings(
        self,
        dataset_id: str,
        version_id: Optional[str] = None,
        category: Optional[FindingCategory] = None,
        severity: Optional[FindingSeverity] = None,
    ) -> List[EDAFinding]:
        """
        Retrieves structured automated findings with optional filtering.
        """
        report = self.get_or_create_eda_report(dataset_id, version_id)
        findings = report.findings

        if category:
            findings = [f for f in findings if f.category == category]
        if severity:
            findings = [f for f in findings if f.severity == severity]

        return findings


eda_service = EDAService()
