"""
AnalyzaX — Phase 8: SQL Query Service
Coordinates validation, execution watchdogs, cache management, chart recommendation,
and execution history logging across datasets and immutable versions.
"""

from typing import Optional

from backend.app.core.logging import logger
from backend.app.engines.sql.cache import query_cache
from backend.app.engines.sql.chart_advisor import SQLChartAdvisor
from backend.app.engines.sql.executor import SQLExecutor, query_registry
from backend.app.engines.sql.hasher import SQLHasher
from backend.app.engines.sql.history import query_history_repo
from backend.app.engines.sql.models import (
    QueryHistoryEntry,
    QueryStatus,
    SQLExplainResult,
    SQLQueryRequest,
    SQLQueryResponse,
    SQLValidationResult,
)
from backend.app.engines.sql.validator import SQLValidator
from backend.app.services.cleaning.version_service import VersionService
from backend.app.services.dataset_service import dataset_service


class SQLQueryService:
    """
    Application service coordinating analytical SQL executions.
    """

    def __init__(self) -> None:
        self._version_service = VersionService()
        self._dataset_service = dataset_service

    def _resolve_context(self, dataset_id: str, version_id: Optional[str] = None):
        """Resolves target dataset and version file."""
        dataset = self._dataset_service.get_dataset(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset '{dataset_id}' not found.")

        if version_id:
            version = self._version_service.get_version(dataset_id, version_id)
            if not version:
                raise ValueError(f"Version '{version_id}' not found for dataset '{dataset_id}'.")
        else:
            version = self._version_service.get_active_version(dataset_id)

        return dataset, version

    def validate_query(self, dataset_id: str, sql: str, version_id: Optional[str] = None) -> SQLValidationResult:
        """Validates query against the schema of the specified dataset version."""
        dataset, version = self._resolve_context(dataset_id, version_id)

        # Extract column names for typo suggestions
        from backend.app.engines.sql.introspection import SchemaIntrospector
        schema_info = SchemaIntrospector.introspect(
            storage_path=version.storage_path,
            dataset_id=dataset_id,
            version_id=version.version_id,
            friendly_name=dataset.name,
        )

        valid_tables = [
            "dataset",
            "current_dataset",
            schema_info.table_alias,
            f"{schema_info.table_alias}_{version.version_id}",
            f"dataset_{version.version_id}",
            f"dataset_{dataset_id}_{version.version_id}",
        ]
        valid_cols = [c.name for c in schema_info.columns]

        return SQLValidator.validate(
            sql=sql,
            valid_tables=valid_tables,
            valid_columns=valid_cols,
        )

    def execute_query(self, req: SQLQueryRequest) -> SQLQueryResponse:
        """
        Coordinates full SQL query execution:
        1. Context resolution (version Parquet storage path)
        2. AST and security validation
        3. Cache check
        4. Safe execution
        5. Chart suggestions
        6. History recording
        """
        dataset, version = self._resolve_context(req.dataset_id, req.version_id)
        query_hash = SQLHasher.compute_hash(req.sql, req.dataset_id, version.version_id)

        # 1. Validation check
        val_result = self.validate_query(req.dataset_id, req.sql, version.version_id)
        if not val_result.is_valid:
            err_msg = "; ".join(e.message for e in val_result.errors)
            failed_resp = SQLQueryResponse(
                query_id="",
                dataset_id=req.dataset_id,
                version_id=version.version_id,
                status=QueryStatus.FAILED,
                columns=[],
                rows=[],
                row_count=0,
                execution_time_ms=0.0,
                is_truncated=False,
                query_hash=query_hash,
                cached=False,
                error_message=err_msg,
            )
            # Log failure to history
            query_history_repo.add_entry(
                QueryHistoryEntry(
                    query_id="failed_val",
                    dataset_id=req.dataset_id,
                    version_id=version.version_id,
                    query_text=req.sql,
                    query_hash=query_hash,
                    status=QueryStatus.FAILED,
                    execution_time_ms=0.0,
                    row_count=0,
                    error_message=err_msg,
                )
            )
            return failed_resp

        # 2. Check query cache
        if req.use_cache:
            cached_resp = query_cache.get(req.dataset_id, version.version_id, query_hash)
            if cached_resp:
                logger.info(f"Serving query from cache for dataset {req.dataset_id}:{version.version_id}")
                return cached_resp

        workspace_id = getattr(req, "workspace_id", None)
        effective_max_rows = req.max_rows
        if workspace_id:
            from backend.app.services.usage import plan_service, quota_service
            from backend.app.engines.usage.metrics import UsageMetrics

            quota_service.enforce_feature(workspace_id, "SQL_ANALYTICS")
            quota_service.enforce_quota(
                workspace_id=workspace_id,
                metric_key=UsageMetrics.SQL_QUERY_EXECUTIONS.key,
                quantity=1.0,
            )
            ent = plan_service.get_entitlement(workspace_id, "SQL_RESULT_ROWS")
            if ent and ent.limit is not None:
                effective_max_rows = min(req.max_rows, int(ent.limit))

        # 3. Execute via SQLExecutor
        resp = SQLExecutor.execute(
            sql=req.sql,
            storage_path=version.storage_path,
            dataset_id=req.dataset_id,
            version_id=version.version_id,
            friendly_name=dataset.name,
            max_rows=effective_max_rows,
            timeout_seconds=req.timeout_seconds,
        )
        resp.query_hash = query_hash

        # 4. Generate Chart Suggestions if successful
        if resp.status == QueryStatus.COMPLETED and resp.rows:
            try:
                resp.suggested_charts = SQLChartAdvisor.advise(
                    dataset_id=req.dataset_id,
                    version_id=version.version_id,
                    columns=resp.columns,
                    rows=resp.rows,
                )
            except Exception as e:
                logger.warning(f"Failed to generate chart recommendations: {e}")

            # Populate cache
            query_cache.set(req.dataset_id, version.version_id, query_hash, resp)

        # 5. Record to history
        query_history_repo.add_entry(
            QueryHistoryEntry(
                query_id=resp.query_id,
                dataset_id=req.dataset_id,
                version_id=version.version_id,
                query_text=req.sql,
                query_hash=query_hash,
                status=resp.status,
                execution_time_ms=resp.execution_time_ms,
                row_count=resp.row_count,
                error_message=resp.error_message,
            )
        )
        # 6. Record usage if workspace is known
        if workspace_id and resp.status == QueryStatus.COMPLETED:
            from backend.app.services.usage import usage_service
            from backend.app.engines.usage.metrics import UsageMetrics
            usage_service.record_usage(
                workspace_id=workspace_id,
                metric_key=UsageMetrics.SQL_QUERY_EXECUTIONS.key,
                quantity=1.0,
                operation_type="sql_query",
                resource_type="dataset",
                resource_id=req.dataset_id,
                idempotency_key=f"sql_{resp.query_id}",
            )

        return resp

    def explain_query(self, dataset_id: str, sql: str, version_id: Optional[str] = None) -> SQLExplainResult:
        """Generates execution plan for query."""
        dataset, version = self._resolve_context(dataset_id, version_id)

        # Ensure query is valid before explaining
        val_result = self.validate_query(dataset_id, sql, version.version_id)
        if not val_result.is_valid:
            raise ValueError("; ".join(e.message for e in val_result.errors))

        return SQLExecutor.explain(
            sql=sql,
            storage_path=version.storage_path,
            dataset_id=dataset_id,
            version_id=version.version_id,
            friendly_name=dataset.name,
        )

    def cancel_query(self, query_id: str) -> bool:
        """Interrupts a running query."""
        return query_registry.cancel(query_id)


sql_query_service = SQLQueryService()
