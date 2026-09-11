"""
AnalyzaX — Phase 10: Statistical Intelligence Application Service
Coordinates dataset version resolution, resource bounding, deterministic execution,
caching, and persistent history storage in backend/data/statistics/history.json.
"""

import hashlib
import json
import os
from typing import Any, Dict, List, Optional
import polars as pl

from backend.app.core.cache import cache_service, build_cache_key
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.statistics.catalog import get_all_catalog_items, get_catalog_item
from backend.app.engines.statistics.engine import statistics_engine
from backend.app.engines.statistics.models import (
    MethodCatalogItem,
    MethodRecommendation,
    MethodRecommendationRequest,
    MissingDataReport,
    StatisticalAnalysisRequest,
    StatisticalResult,
    ValidationResponse,
)
from backend.app.engines.statistics.recommender import recommend_statistical_method
from backend.app.services.cleaning import version_service
from backend.app.services.dataset_service import dataset_service


class StatisticsService:
    """
    Coordinates statistical computations with dataset version isolation and persistent history.
    """
    STATISTICS_MAX_ROWS = 1_000_000
    STATISTICS_MAX_COLUMNS = 100
    STATISTICS_MAX_CORRELATION_COLUMNS = 50
    STATISTICS_MAX_REGRESSION_FEATURES = 30

    def __init__(self) -> None:
        self._storage_dir = os.path.abspath(getattr(settings, "DATA_STATISTICS_DIR", "./data/statistics"))
        os.makedirs(self._storage_dir, exist_ok=True)
        self._history_file = os.path.join(self._storage_dir, "history.json")
        self._cache: Dict[str, StatisticalResult] = {}
        self._history: Dict[str, dict] = self._load_history()

    def _load_history(self) -> Dict[str, dict]:
        if os.path.exists(self._history_file):
            try:
                with open(self._history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load statistics history: {e}")
        return {}

    def _save_history(self) -> None:
        try:
            with open(self._history_file, "w", encoding="utf-8") as f:
                json.dump(self._history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to persist statistics history: {e}")

    def _generate_cache_key(self, req: StatisticalAnalysisRequest) -> str:
        return build_cache_key(
            namespace="statistics",
            workspace_id=getattr(req, "workspace_id", "global") or "global",
            operation=f"{req.analysis_type}:{req.method}",
            dataset_id=req.dataset_id,
            version_id=req.dataset_version_id,
            params={
                "target": sorted(req.target_columns),
                "group": sorted(req.group_columns),
                "extra": req.parameters,
            },
            engine_version=statistics_engine.ENGINE_VERSION,
        )

    def get_methods_catalog(self) -> List[MethodCatalogItem]:
        """Returns metadata for all available statistical methods."""
        return get_all_catalog_items()

    def validate_request(self, request: StatisticalAnalysisRequest) -> ValidationResponse:
        """
        Validates analysis request against dataset schema and row boundaries.
        """
        issues: List[str] = []
        warnings: List[str] = []

        ds = dataset_service.get_dataset(request.dataset_id)
        if not ds:
            issues.append(f"Dataset '{request.dataset_id}' not found.")
            return ValidationResponse(is_valid=False, issues=issues)

        # Version resolution
        version = version_service.get_version(request.dataset_id, request.dataset_version_id)
        if not version:
            issues.append(f"Dataset version '{request.dataset_version_id}' not found for dataset '{request.dataset_id}'.")
            return ValidationResponse(is_valid=False, issues=issues)

        try:
            df = version_service.get_version_dataframe(request.dataset_id, request.dataset_version_id)
        except Exception as e:
            issues.append(f"Failed to load DataFrame for version '{request.dataset_version_id}': {e}")
            return ValidationResponse(is_valid=False, issues=issues)

        cols = df.columns
        for c in request.target_columns:
            if c not in cols:
                issues.append(f"Target column '{c}' does not exist in dataset version.")

        for c in request.group_columns:
            if c not in cols:
                issues.append(f"Group column '{c}' does not exist in dataset version.")

        # Check column limits
        if len(request.target_columns) > self.STATISTICS_MAX_COLUMNS:
            issues.append(f"Too many target columns ({len(request.target_columns)} > {self.STATISTICS_MAX_COLUMNS}).")

        # Parameter validations
        alpha = request.parameters.get("alpha")
        if alpha is not None and (not isinstance(alpha, (int, float)) or not (0 < alpha < 1)):
            issues.append(f"Invalid alpha parameter: {alpha}. Must be strictly between 0 and 1.")

        conf_level = request.parameters.get("confidence_level")
        if conf_level is not None and (not isinstance(conf_level, (int, float)) or not (0 < conf_level < 1)):
            issues.append(f"Invalid confidence_level parameter: {conf_level}. Must be strictly between 0 and 1.")

        alt = request.parameters.get("alternative")
        if alt is not None and alt not in ["two_sided", "two-sided", "greater", "less"]:
            issues.append(f"Invalid alternative parameter: {alt}. Must be two_sided, greater, or less.")

        # Row checks
        if len(df) > self.STATISTICS_MAX_ROWS:
            warnings.append(f"Dataset has {len(df)} rows, exceeding recommended {self.STATISTICS_MAX_ROWS}. Execution may take longer.")

        # Calculate missing data report
        selected_cols = list(set(request.target_columns + request.group_columns))
        if selected_cols and all(c in cols for c in selected_cols):
            sub_df = df.select(selected_cols)
            null_count = sub_df.null_count().to_numpy().sum()
            used_obs = len(sub_df.drop_nulls())
            missing_rep = MissingDataReport(
                original_observations=len(df),
                used_observations=used_obs,
                excluded_observations=len(df) - used_obs,
                missing_policy=request.parameters.get("missing_data_policy", "listwise_deletion"),
            )
        else:
            missing_rep = None

        return ValidationResponse(
            is_valid=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            missing_data_report=missing_rep,
        )

    def recommend_method(self, req: MethodRecommendationRequest) -> MethodRecommendation:
        """Recommends appropriate statistical method deterministically."""
        df = version_service.get_version_dataframe(req.dataset_id, req.dataset_version_id)
        return recommend_statistical_method(
            df=df,
            target_columns=req.target_columns,
            group_columns=req.group_columns,
            intent=req.intent,
        )

    def execute_analysis(self, request: StatisticalAnalysisRequest) -> StatisticalResult:
        """
        Executes statistical computation with strict dataset version binding, caching, persistence, and quota enforcement.
        """
        workspace_id = getattr(request, "workspace_id", None)
        if workspace_id:
            from backend.app.services.usage import quota_service
            from backend.app.engines.usage.metrics import UsageMetrics

            quota_service.enforce_feature(workspace_id, "ADVANCED_STATISTICS")
            quota_service.enforce_quota(
                workspace_id=workspace_id,
                metric_key=UsageMetrics.STATISTICAL_ANALYSES.key,
                quantity=1.0,
            )

        val_res = self.validate_request(request)
        if not val_res.is_valid:
            raise ValueError(f"Invalid statistical analysis request: {'; '.join(val_res.issues)}")

        # Check cache
        cache_key = self._generate_cache_key(request)
        cached = cache_service.get(cache_key) or self._cache.get(cache_key)
        if cached:
            logger.info(f"Statistics cache hit for analysis {request.analysis_id}")
            # Persist to history if not already present
            if cached.result_id not in self._history:
                self._history[cached.result_id] = cached.model_dump()
                self._save_history()
            return cached

        # Load exact DataFrame for requested version
        df = version_service.get_version_dataframe(request.dataset_id, request.dataset_version_id)

        # Execute in pure deterministic engine
        result = statistics_engine.execute_analysis(df, request)

        # Store in cache & history
        self._cache[cache_key] = result
        cache_service.set(cache_key, result, ttl_seconds=cache_service.SAFE_LONG_TTL)
        self._history[result.result_id] = result.model_dump()
        self._save_history()

        logger.info(
            f"Completed statistical analysis {result.result_id} ({result.method}) for {result.dataset_id}@{result.dataset_version_id}"
        )

        if workspace_id:
            from backend.app.services.usage import usage_service
            from backend.app.engines.usage.metrics import UsageMetrics
            usage_service.record_usage(
                workspace_id=workspace_id,
                metric_key=UsageMetrics.STATISTICAL_ANALYSES.key,
                quantity=1.0,
                operation_type="statistical_analysis",
                resource_type="analysis",
                resource_id=result.result_id,
                idempotency_key=f"stats_{result.result_id}",
            )

        return result

    def get_analysis(self, analysis_id: str) -> Optional[StatisticalResult]:
        """Retrieves a saved statistical result by ID."""
        # Check in-memory results first
        for res in self._cache.values():
            if res.result_id == analysis_id:
                return res

        record = self._history.get(analysis_id)
        if record:
            return StatisticalResult(**record)
        return None

    def list_history(
        self,
        dataset_id: Optional[str] = None,
        dataset_version_id: Optional[str] = None,
    ) -> List[StatisticalResult]:
        """Lists historical statistical analyses, optionally filtered by dataset and version."""
        results = []
        for record in self._history.values():
            if dataset_id and record.get("dataset_id") != dataset_id:
                continue
            if dataset_version_id and record.get("dataset_version_id") != dataset_version_id:
                continue
            try:
                results.append(StatisticalResult(**record))
            except Exception as e:
                logger.warning(f"Error parsing historical result: {e}")

        # Sort descending by creation date
        results.sort(key=lambda r: r.created_at, reverse=True)
        return results

    def delete_analysis(self, analysis_id: str) -> bool:
        """Deletes a saved analysis from history."""
        if analysis_id in self._history:
            del self._history[analysis_id]
            self._save_history()
            # Also clear from memory cache
            keys_to_del = [k for k, v in self._cache.items() if v.result_id == analysis_id]
            for k in keys_to_del:
                del self._cache[k]
            return True
        return False


statistics_service = StatisticsService()
