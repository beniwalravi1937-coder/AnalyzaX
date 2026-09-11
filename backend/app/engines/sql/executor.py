"""
AnalyzaX — Phase 8: Safe DuckDB SQL Execution Engine
Handles sandboxed query execution, timeout watchdog containment, row truncation,
path sanitization in error traces & plans, and query cancellation.
"""

import math
import re
import threading
import time
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import duckdb
from backend.app.core.logging import logger
from backend.app.engines.sql.models import (
    QueryStatus,
    SQLColumnDescriptor,
    SQLExplainResult,
    SQLQueryResponse,
)


class ActiveQueryRegistry:
    """Tracks running DuckDB connections to allow user cancellation."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active_connections: Dict[str, duckdb.DuckDBPyConnection] = {}
        self._cancelled_queries: set[str] = set()

    def register(self, query_id: str, conn: duckdb.DuckDBPyConnection) -> None:
        with self._lock:
            self._active_connections[query_id] = conn

    def unregister(self, query_id: str) -> None:
        with self._lock:
            self._active_connections.pop(query_id, None)
            self._cancelled_queries.discard(query_id)

    def cancel(self, query_id: str) -> bool:
        with self._lock:
            self._cancelled_queries.add(query_id)
            conn = self._active_connections.get(query_id)
            if conn:
                try:
                    conn.interrupt()
                    logger.info(f"Query {query_id} interrupted via ActiveQueryRegistry")
                    return True
                except Exception as e:
                    logger.warning(f"Failed to interrupt query {query_id}: {e}")
        return False

    def is_cancelled(self, query_id: str) -> bool:
        with self._lock:
            return query_id in self._cancelled_queries


query_registry = ActiveQueryRegistry()


class SQLExecutor:
    """
    Executes validated SQL statements against versioned Parquet data in DuckDB.
    """

    @staticmethod
    def _sanitize_output(text: str) -> str:
        """Removes local filesystem paths and raw parquet filenames from output/errors."""
        if not text:
            return ""
        # Replace Windows and POSIX paths with sanitized placeholders
        sanitized = re.sub(r"[A-Za-z]:[\\/][^'\"\s]+(?:\.parquet|\.csv|\.json)?", "<dataset_storage>", text)
        sanitized = re.sub(r"/data/[^'\"\s]+(?:\.parquet|\.csv|\.json)?", "<dataset_storage>", sanitized)
        return sanitized

    @staticmethod
    def _serialize_cell(value: Any) -> Any:
        """Serializes cell values to JSON-safe Python types."""
        if value is None:
            return None
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return None
            return value
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, (bytes, bytearray)):
            return value.hex()
        return value

    @classmethod
    def execute(
        cls,
        sql: str,
        storage_path: str,
        dataset_id: str,
        version_id: str,
        friendly_name: Optional[str] = None,
        max_rows: int = 10000,
        timeout_seconds: float = 30.0,
        query_id: Optional[str] = None,
    ) -> SQLQueryResponse:
        """
        Executes a SQL query in an isolated DuckDB connection with strict timeout
        watchdog, row limit containment, and path sanitization.
        """
        qid = query_id or str(uuid.uuid4())
        posix_path = storage_path.replace("\\", "/")

        start_time = time.perf_counter()
        is_cancelled = False
        is_timeout = False

        # Create an isolated in-memory DuckDB connection for this query execution
        conn = duckdb.connect()
        query_registry.register(qid, conn)

        def run_query():
            nonlocal conn
            # Phase 24: Ingest Parquet file into an in-memory table before locking external access
            conn.execute(f"CREATE OR REPLACE TABLE dataset AS SELECT * FROM read_parquet('{posix_path}');")
            conn.execute("CREATE OR REPLACE VIEW current_dataset AS SELECT * FROM dataset;")
            conn.execute(f"CREATE OR REPLACE VIEW dataset_{version_id} AS SELECT * FROM dataset;")
            conn.execute(f"CREATE OR REPLACE VIEW dataset_{dataset_id}_{version_id} AS SELECT * FROM dataset;")

            if friendly_name:
                safe_alias = re.sub(r"[^a-zA-Z0-9_]", "_", friendly_name).strip("_").lower()
                if safe_alias and safe_alias not in ("select", "from", "where", "dataset"):
                    conn.execute(f"CREATE OR REPLACE VIEW {safe_alias} AS SELECT * FROM dataset;")
                    conn.execute(f"CREATE OR REPLACE VIEW {safe_alias}_{version_id} AS SELECT * FROM dataset;")

            # Phase 24: Hardened DuckDB Sandboxing and Resource Containment
            conn.execute("SET max_memory = '4GB';")
            conn.execute("SET threads = 4;")
            conn.execute("SET enable_external_access = false;")
            conn.execute("SET lock_configuration = true;")

            # Execute the user's analytical query
            cursor = conn.cursor()
            cursor.execute(sql)


            # Extract column descriptions
            raw_columns = cursor.description or []
            column_descriptors: List[SQLColumnDescriptor] = []
            for col in raw_columns:
                col_name = str(col[0])
                col_type = str(col[1]) if len(col) > 1 and col[1] else "VARCHAR"
                # Map physical type to coarse semantic type
                sem_type = (
                    "numeric"
                    if any(t in col_type.upper() for t in ["INT", "DOUBLE", "FLOAT", "DECIMAL", "NUMERIC"])
                    else "datetime"
                    if any(t in col_type.upper() for t in ["DATE", "TIME", "TIMESTAMP"])
                    else "boolean"
                    if "BOOL" in col_type.upper()
                    else "categorical"
                )

                column_descriptors.append(
                    SQLColumnDescriptor(
                        name=col_name,
                        physical_type=col_type,
                        semantic_type=sem_type,
                        nullable=True,
                    )
                )

            # Fetch up to max_rows + 1 to test for truncation
            raw_rows = cursor.fetchmany(max_rows + 1)
            is_truncated = len(raw_rows) > max_rows
            if is_truncated:
                raw_rows = raw_rows[:max_rows]

            col_names = [c.name for c in column_descriptors]
            rows: List[Dict[str, Any]] = []
            for r in raw_rows:
                row_dict = {}
                for idx, val in enumerate(r):
                    row_dict[col_names[idx]] = cls._serialize_cell(val)
                rows.append(row_dict)

            return column_descriptors, rows, is_truncated

        import concurrent.futures

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(run_query)

        try:
            column_descriptors, rows, is_truncated = future.result(timeout=timeout_seconds)
            execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

            if query_registry.is_cancelled(qid):
                return SQLQueryResponse(
                    query_id=qid,
                    dataset_id=dataset_id,
                    version_id=version_id,
                    status=QueryStatus.CANCELLED,
                    columns=[],
                    rows=[],
                    row_count=0,
                    execution_time_ms=execution_time_ms,
                    is_truncated=False,
                    cached=False,
                    error_message="Query execution was cancelled by user.",
                )

            return SQLQueryResponse(
                query_id=qid,
                dataset_id=dataset_id,
                version_id=version_id,
                status=QueryStatus.COMPLETED,
                columns=column_descriptors,
                rows=rows,
                row_count=len(rows),
                total_rows_estimate=None,
                scanned_rows=len(rows),
                execution_time_ms=execution_time_ms,
                is_truncated=is_truncated,
                cached=False,
                error_message=None,
            )

        except concurrent.futures.TimeoutError:
            try:
                conn.interrupt()
            except Exception:
                pass
            execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.warning(f"Query {qid} timed out after {timeout_seconds}s.")
            return SQLQueryResponse(
                query_id=qid,
                dataset_id=dataset_id,
                version_id=version_id,
                status=QueryStatus.TIMEOUT,
                columns=[],
                rows=[],
                row_count=0,
                execution_time_ms=execution_time_ms,
                is_truncated=False,
                cached=False,
                error_message=f"Query execution timed out after {timeout_seconds} seconds.",
            )

        except Exception as e:
            execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            raw_error = str(e)
            if "INTERRUPT" in raw_error.upper() or "CANCEL" in raw_error.upper():
                status = QueryStatus.CANCELLED
                err_msg = "Query execution was cancelled by user."
            else:
                status = QueryStatus.FAILED
                err_msg = cls._sanitize_output(raw_error)

            logger.error(f"SQL execution failed for query {qid}: {err_msg}")
            return SQLQueryResponse(
                query_id=qid,
                dataset_id=dataset_id,
                version_id=version_id,
                status=status,
                columns=[],
                rows=[],
                row_count=0,
                execution_time_ms=execution_time_ms,
                is_truncated=False,
                cached=False,
                error_message=err_msg,
            )

        finally:
            query_registry.unregister(qid)
            executor.shutdown(wait=False, cancel_futures=True)
            try:
                conn.close()
            except Exception:
                pass

    @classmethod
    def explain(
        cls,
        sql: str,
        storage_path: str,
        dataset_id: str,
        version_id: str,
        friendly_name: Optional[str] = None,
    ) -> SQLExplainResult:
        """
        Runs EXPLAIN query to inspect DuckDB execution plan without executing full scan.
        """
        qid = str(uuid.uuid4())
        posix_path = storage_path.replace("\\", "/")
        start_time = time.perf_counter()

        conn = duckdb.connect()
        try:
            # Register safe table aliases
            # Phase 24: Ingest Parquet file into an in-memory table before locking external access
            conn.execute(f"CREATE OR REPLACE TABLE dataset AS SELECT * FROM read_parquet('{posix_path}');")
            conn.execute("CREATE OR REPLACE VIEW current_dataset AS SELECT * FROM dataset;")
            conn.execute(f"CREATE OR REPLACE VIEW dataset_{version_id} AS SELECT * FROM dataset;")

            if friendly_name:
                safe_alias = re.sub(r"[^a-zA-Z0-9_]", "_", friendly_name).strip("_").lower()
                if safe_alias and safe_alias not in ("select", "from", "where", "dataset"):
                    conn.execute(f"CREATE OR REPLACE VIEW {safe_alias} AS SELECT * FROM dataset;")

            # Phase 24: Hardened DuckDB Sandboxing
            conn.execute("SET max_memory = '4GB';")
            conn.execute("SET threads = 4;")
            conn.execute("SET enable_external_access = false;")
            conn.execute("SET lock_configuration = true;")

            clean_sql = sql.strip().rstrip(";")
            if not clean_sql.upper().startswith("EXPLAIN"):
                clean_sql = f"EXPLAIN {clean_sql}"


            res = conn.execute(clean_sql).fetchall()
            plan_text = "\n".join(str(row[1]) if len(row) > 1 else str(row[0]) for row in res)
            sanitized_plan = cls._sanitize_output(plan_text)

            execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return SQLExplainResult(
                query_id=qid,
                dataset_id=dataset_id,
                version_id=version_id,
                plan_text=sanitized_plan,
                plan_tree=None,
                estimated_cardinality=None,
                execution_time_ms=execution_time_ms,
            )
        finally:
            try:
                conn.close()
            except Exception:
                pass
