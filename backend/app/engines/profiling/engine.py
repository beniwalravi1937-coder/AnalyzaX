"""
Automated Dataset Profiler Coordinator
Orchestrates high-speed, out-of-core DuckDB profiling across all columns of a dataset.
"""

from datetime import datetime, timezone
from typing import Any, List
import duckdb

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.profiling.categorical import profile_categorical_column
from backend.app.engines.profiling.datetime_prof import profile_datetime_column
from backend.app.engines.profiling.numeric import profile_numeric_column
from backend.app.engines.profiling.physical import map_duckdb_physical_type
from backend.app.engines.profiling.semantic import infer_semantic_type
from backend.app.engines.profiling.targets import detect_target_candidates
from backend.app.schemas.profile import ColumnProfile, DatasetProfileResponse


class DatasetProfiler:
    """
    Pure analytical engine for deep structural and statistical profiling.
    Executes entirely through DuckDB without copying full datasets into memory.
    """

    def __init__(
        self,
        sample_size: int = settings.PROFILE_SAMPLE_SIZE,
        top_categories_limit: int = settings.TOP_CATEGORIES_LIMIT,
        profiling_version: str = settings.PROFILING_VERSION,
    ) -> None:
        self.sample_size = sample_size
        self.top_categories_limit = top_categories_limit
        self.profiling_version = profiling_version

    def profile_table(
        self,
        conn: duckdb.DuckDBPyConnection,
        table_name: str,
        dataset_id: str,
    ) -> DatasetProfileResponse:
        """
        Profiles a registered DuckDB table or view and produces a DatasetProfileResponse.
        """
        escaped_table = table_name.replace('"', '""')

        # 1. Total row count
        count_sql = f'SELECT COUNT(*) FROM "{escaped_table}"'
        try:
            row_count = int(conn.execute(count_sql).fetchone()[0] or 0)
        except Exception as e:
            logger.error(f"Failed to query row count for table {table_name}: {e}")
            raise RuntimeError(f"Could not access table {table_name}: {e}")

        # 2. Extract column metadata from DuckDB DESCRIBE
        desc_sql = f'DESCRIBE "{escaped_table}"'
        try:
            schema_rows = conn.execute(desc_sql).fetchall()
        except Exception as e:
            logger.error(f"Failed to describe schema for {table_name}: {e}")
            raise RuntimeError(f"Could not retrieve schema for {table_name}: {e}")

        columns: List[ColumnProfile] = []

        for row in schema_rows:
            raw_col_name = str(row[0])
            raw_type = str(row[1])
            is_nullable_str = str(row[2]) if len(row) > 2 else "YES"
            is_nullable = is_nullable_str.upper() != "NO"

            physical_type = map_duckdb_physical_type(raw_type)
            escaped_col = raw_col_name.replace('"', '""')

            # Extract small representative sample
            sample_sql = f"""
            SELECT CAST("{escaped_col}" AS VARCHAR)
            FROM "{escaped_table}"
            WHERE "{escaped_col}" IS NOT NULL
            LIMIT {self.sample_size}
            """
            sample_values: List[Any] = []
            try:
                sample_rows = conn.execute(sample_sql).fetchall()
                sample_values = [r[0] for r in sample_rows]
            except Exception:
                sample_values = []

            # Specialized type-specific profiling
            numeric_metrics = None
            categorical_metrics = None
            datetime_metrics = None

            min_val = None
            max_val = None
            is_text_flag = False

            if physical_type in ("integer", "float", "decimal"):
                prof = profile_numeric_column(conn, table_name, raw_col_name, row_count)
                numeric_metrics = prof.get("numeric_metrics")
                null_cnt = prof["null_count"]
                null_pct = prof["null_percentage"]
                uniq_cnt = prof["unique_count"]
                uniq_pct = prof["unique_percentage"]
                card_ratio = prof["cardinality_ratio"]
                if numeric_metrics:
                    min_val = numeric_metrics.min
                    max_val = numeric_metrics.max

            elif physical_type in ("date", "datetime", "time"):
                prof = profile_datetime_column(conn, table_name, raw_col_name, row_count)
                datetime_metrics = prof.get("datetime_metrics")
                null_cnt = prof["null_count"]
                null_pct = prof["null_percentage"]
                uniq_cnt = prof["unique_count"]
                uniq_pct = prof["unique_percentage"]
                card_ratio = prof["cardinality_ratio"]

            else:  # string, boolean, binary
                prof = profile_categorical_column(
                    conn, table_name, raw_col_name, row_count, self.top_categories_limit
                )
                categorical_metrics = prof.get("categorical_metrics")
                null_cnt = prof["null_count"]
                null_pct = prof["null_percentage"]
                uniq_cnt = prof["unique_count"]
                uniq_pct = prof["unique_percentage"]
                card_ratio = prof["cardinality_ratio"]
                if categorical_metrics:
                    is_text_flag = categorical_metrics.is_text

            # Multi-signal semantic inference
            sem_type, sem_conf, is_id, id_conf = infer_semantic_type(
                col_name=raw_col_name,
                physical_type=physical_type,
                unique_count=uniq_cnt,
                total_non_null=(row_count - null_cnt),
                cardinality_ratio=card_ratio,
                sample_values=sample_values,
                min_val=min_val,
                max_val=max_val,
                is_text=is_text_flag,
            )

            col_profile = ColumnProfile(
                name=raw_col_name,
                physical_type=physical_type,
                semantic_type=sem_type,
                semantic_confidence=sem_conf,
                nullable=is_nullable,
                null_count=null_cnt,
                null_percentage=null_pct,
                unique_count=uniq_cnt,
                unique_percentage=uniq_pct,
                cardinality_ratio=card_ratio,
                sample_values=sample_values,
                numeric_metrics=numeric_metrics,
                categorical_metrics=categorical_metrics,
                datetime_metrics=datetime_metrics,
                is_identifier_candidate=is_id,
                identifier_confidence=id_conf,
            )
            columns.append(col_profile)

        # Target candidate detection
        target_candidates = detect_target_candidates(columns)
        for cand in target_candidates:
            for col in columns:
                if col.name == cand.column_name:
                    col.target_candidate = cand

        # Summary counts
        numeric_cols_cnt = sum(1 for c in columns if c.physical_type in ("integer", "float", "decimal"))
        categorical_cols_cnt = sum(1 for c in columns if c.physical_type in ("string", "boolean"))
        datetime_cols_cnt = sum(1 for c in columns if c.physical_type in ("date", "datetime", "time"))
        identifier_cols_cnt = sum(1 for c in columns if c.is_identifier_candidate)

        return DatasetProfileResponse(
            dataset_id=dataset_id,
            row_count=row_count,
            column_count=len(columns),
            columns=columns,
            numeric_columns_count=numeric_cols_cnt,
            categorical_columns_count=categorical_cols_cnt,
            datetime_columns_count=datetime_cols_cnt,
            identifier_columns_count=identifier_cols_cnt,
            target_candidates=target_candidates,
            profiling_version=self.profiling_version,
            status="READY",
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
