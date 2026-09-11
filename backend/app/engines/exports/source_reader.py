"""
Source Readers for Phase 15 Export Engine.
Reads finalized analytical results from existing engine storage.
Never recomputes — only reads persisted, deterministic results.
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple

import duckdb

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.exports.models import (
    ExportProvenance,
    ExportSourceData,
    ExportSourceType,
)


class BaseSourceReader:
    """Base class for source readers with common utility methods."""

    def _read_json_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Safely read a JSON file and return its contents."""
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to read JSON file {file_path}: {e}")
            return None

    def _build_provenance(
        self,
        dataset_id: str,
        version_id: str,
        source_engine: Optional[str] = None,
        source_result_id: Optional[str] = None,
    ) -> ExportProvenance:
        return ExportProvenance(
            dataset_id=dataset_id,
            dataset_version_id=version_id,
            source_engine=source_engine,
            source_result_id=source_result_id,
        )


class DatasetSourceReader(BaseSourceReader):
    """Reads raw or versioned dataset parquet files via DuckDB."""

    def read(
        self,
        dataset_id: str,
        version_id: str,
        parquet_path: str,
        max_rows: Optional[int] = None,
    ) -> ExportSourceData:
        limit = max_rows or settings.EXPORT_MAX_ROWS
        try:
            conn = duckdb.connect(":memory:")
            query = f"SELECT * FROM read_parquet(?) LIMIT {int(limit)}"
            result = conn.execute(query, [parquet_path])
            columns = [desc[0] for desc in result.description]
            rows = result.fetchall()
            data = [dict(zip(columns, row)) for row in rows]

            # Get total count
            count_result = conn.execute(
                "SELECT COUNT(*) FROM read_parquet(?)", [parquet_path]
            )
            total_rows = count_result.fetchone()[0]
            conn.close()

            return ExportSourceData(
                data=data,
                metadata={
                    "total_rows": total_rows,
                    "exported_rows": len(data),
                    "columns": columns,
                    "truncated": len(data) < total_rows,
                },
                provenance=self._build_provenance(
                    dataset_id, version_id, "dataset"
                ),
                row_count=len(data),
                columns=columns,
            )
        except Exception as e:
            logger.error(f"DatasetSourceReader failed: {e}")
            raise ValueError(f"Failed to read dataset: {e}")


class SqlResultSourceReader(BaseSourceReader):
    """Reads saved SQL query results from data/sql/."""

    def read(
        self,
        dataset_id: str,
        version_id: str,
        source_id: Optional[str] = None,
    ) -> ExportSourceData:
        sql_dir = os.path.join(settings.DATA_SQL_DIR, dataset_id)
        if not os.path.isdir(sql_dir):
            raise ValueError(f"No SQL results found for dataset {dataset_id}")

        # If source_id given, read specific result; otherwise read latest
        if source_id:
            result_path = os.path.join(sql_dir, f"{source_id}.json")
        else:
            # Get latest result
            files = sorted(
                [f for f in os.listdir(sql_dir) if f.endswith(".json")],
                key=lambda x: os.path.getmtime(os.path.join(sql_dir, x)),
                reverse=True,
            )
            if not files:
                raise ValueError(f"No SQL results found in {sql_dir}")
            result_path = os.path.join(sql_dir, files[0])

        result_data = self._read_json_file(result_path)
        if not result_data:
            raise ValueError(f"SQL result not found at {result_path}")

        # Extract rows and columns from the SQL result format
        rows = result_data.get("rows", result_data.get("data", []))
        columns = result_data.get("columns", [])
        if not columns and rows:
            columns = list(rows[0].keys()) if isinstance(rows[0], dict) else []

        return ExportSourceData(
            data=rows,
            metadata={
                "query": result_data.get("query", ""),
                "execution_time_ms": result_data.get("execution_time_ms"),
                "columns": columns,
            },
            provenance=self._build_provenance(
                dataset_id, version_id, "sql", source_id
            ),
            row_count=len(rows),
            columns=columns,
        )


class ProfileSourceReader(BaseSourceReader):
    """Reads profiling results from data/profiles/."""

    def read(
        self,
        dataset_id: str,
        version_id: str,
    ) -> ExportSourceData:
        profile_path = os.path.join(
            settings.DATA_PROFILES_DIR, dataset_id, f"{version_id}.json"
        )
        # Fallback: try without version
        if not os.path.exists(profile_path):
            profile_path = os.path.join(
                settings.DATA_PROFILES_DIR, f"{dataset_id}.json"
            )

        data = self._read_json_file(profile_path)
        if not data:
            raise ValueError(f"Profile not found for dataset {dataset_id}")

        # Convert column profiles to tabular format
        columns_data = data.get("columns", data.get("column_profiles", []))
        if isinstance(columns_data, dict):
            table_rows = []
            for col_name, col_info in columns_data.items():
                row = {"column_name": col_name}
                if isinstance(col_info, dict):
                    row.update(col_info)
                table_rows.append(row)
            columns_data = table_rows

        return ExportSourceData(
            data=columns_data,
            metadata={
                "dataset_id": dataset_id,
                "version_id": version_id,
                "row_count": data.get("row_count"),
                "column_count": data.get("column_count"),
            },
            provenance=self._build_provenance(
                dataset_id, version_id, "profiling"
            ),
            row_count=len(columns_data) if isinstance(columns_data, list) else 0,
        )


class QualitySourceReader(BaseSourceReader):
    """Reads quality report from data/quality/."""

    def read(
        self,
        dataset_id: str,
        version_id: str,
    ) -> ExportSourceData:
        quality_path = os.path.join(
            settings.DATA_QUALITY_DIR, dataset_id, f"{version_id}.json"
        )
        if not os.path.exists(quality_path):
            quality_path = os.path.join(
                settings.DATA_QUALITY_DIR, f"{dataset_id}.json"
            )

        data = self._read_json_file(quality_path)
        if not data:
            raise ValueError(f"Quality report not found for dataset {dataset_id}")

        # Extract issues as tabular data
        issues = data.get("issues", data.get("findings", []))
        if isinstance(issues, list):
            table_data = issues
        else:
            table_data = [data]

        return ExportSourceData(
            data=table_data,
            metadata={
                "overall_score": data.get("overall_score", data.get("quality_score")),
                "total_issues": len(table_data),
                "severity_breakdown": data.get("severity_breakdown", {}),
            },
            provenance=self._build_provenance(
                dataset_id, version_id, "quality"
            ),
            row_count=len(table_data),
        )


class EdaSourceReader(BaseSourceReader):
    """Reads EDA results from data/eda/."""

    def read(
        self,
        dataset_id: str,
        version_id: str,
    ) -> ExportSourceData:
        eda_path = os.path.join(
            settings.DATA_EDA_DIR, dataset_id, f"{version_id}.json"
        )
        if not os.path.exists(eda_path):
            eda_path = os.path.join(
                settings.DATA_EDA_DIR, f"{dataset_id}.json"
            )

        data = self._read_json_file(eda_path)
        if not data:
            raise ValueError(f"EDA results not found for dataset {dataset_id}")

        findings = data.get("findings", data.get("insights", []))

        return ExportSourceData(
            data=findings if isinstance(findings, list) else [data],
            metadata={
                "dataset_id": dataset_id,
                "version_id": version_id,
                "analysis_count": len(findings) if isinstance(findings, list) else 1,
            },
            provenance=self._build_provenance(
                dataset_id, version_id, "eda"
            ),
            row_count=len(findings) if isinstance(findings, list) else 1,
        )


class StatisticsSourceReader(BaseSourceReader):
    """Reads statistical test results from data/statistics/."""

    def read(
        self,
        dataset_id: str,
        version_id: str,
        source_id: Optional[str] = None,
    ) -> ExportSourceData:
        stats_dir = os.path.join(settings.DATA_STATISTICS_DIR, dataset_id)
        if not os.path.isdir(stats_dir):
            raise ValueError(f"No statistics results for dataset {dataset_id}")

        if source_id:
            result_path = os.path.join(stats_dir, f"{source_id}.json")
        else:
            files = sorted(
                [f for f in os.listdir(stats_dir) if f.endswith(".json")],
                key=lambda x: os.path.getmtime(os.path.join(stats_dir, x)),
                reverse=True,
            )
            if not files:
                raise ValueError(f"No statistics results found in {stats_dir}")
            result_path = os.path.join(stats_dir, files[0])
            source_id = files[0].replace(".json", "")

        data = self._read_json_file(result_path)
        if not data:
            raise ValueError(f"Statistics result not found at {result_path}")

        return ExportSourceData(
            data=data if isinstance(data, list) else [data],
            metadata={
                "test_type": data.get("test_type", data.get("test_name", "")),
                "result_id": source_id,
            },
            provenance=self._build_provenance(
                dataset_id, version_id, "statistics", source_id
            ),
        )


class MlSourceReader(BaseSourceReader):
    """Reads ML experiment results from data/ml/."""

    def read(
        self,
        dataset_id: str,
        version_id: str,
        source_id: Optional[str] = None,
    ) -> ExportSourceData:
        ml_dir = os.path.join(settings.DATA_ML_DIR, dataset_id)
        if not os.path.isdir(ml_dir):
            raise ValueError(f"No ML results for dataset {dataset_id}")

        if source_id:
            result_path = os.path.join(ml_dir, f"{source_id}.json")
        else:
            files = sorted(
                [f for f in os.listdir(ml_dir) if f.endswith(".json")],
                key=lambda x: os.path.getmtime(os.path.join(ml_dir, x)),
                reverse=True,
            )
            if not files:
                raise ValueError(f"No ML results found in {ml_dir}")
            result_path = os.path.join(ml_dir, files[0])
            source_id = files[0].replace(".json", "")

        data = self._read_json_file(result_path)
        if not data:
            raise ValueError(f"ML result not found at {result_path}")

        return ExportSourceData(
            data=data if isinstance(data, list) else [data],
            metadata={
                "experiment_id": source_id,
                "task_type": data.get("task_type", ""),
            },
            provenance=self._build_provenance(
                dataset_id, version_id, "ml", source_id
            ),
        )


class ForecastSourceReader(BaseSourceReader):
    """Reads forecast results from data/forecasting/."""

    def read(
        self,
        dataset_id: str,
        version_id: str,
        source_id: Optional[str] = None,
    ) -> ExportSourceData:
        forecast_dir = os.path.join(settings.DATA_FORECASTING_DIR, dataset_id)
        if not os.path.isdir(forecast_dir):
            raise ValueError(f"No forecast results for dataset {dataset_id}")

        if source_id:
            result_path = os.path.join(forecast_dir, f"{source_id}.json")
        else:
            files = sorted(
                [f for f in os.listdir(forecast_dir) if f.endswith(".json")],
                key=lambda x: os.path.getmtime(os.path.join(forecast_dir, x)),
                reverse=True,
            )
            if not files:
                raise ValueError(f"No forecast results found in {forecast_dir}")
            result_path = os.path.join(forecast_dir, files[0])
            source_id = files[0].replace(".json", "")

        data = self._read_json_file(result_path)
        if not data:
            raise ValueError(f"Forecast result not found at {result_path}")

        return ExportSourceData(
            data=data if isinstance(data, list) else [data],
            metadata={
                "forecast_id": source_id,
                "model_type": data.get("model_type", ""),
            },
            provenance=self._build_provenance(
                dataset_id, version_id, "forecasting", source_id
            ),
        )


class DashboardSourceReader(BaseSourceReader):
    """Reads dashboard configuration from data/dashboards/."""

    def read(
        self,
        dataset_id: str,
        version_id: str,
        source_id: Optional[str] = None,
    ) -> ExportSourceData:
        dashboards_path = os.path.join(
            settings.DATA_DASHBOARDS_DIR, "dashboards.json"
        )
        data = self._read_json_file(dashboards_path)
        if not data:
            raise ValueError("No dashboards found")

        dashboards = data if isinstance(data, list) else []

        if source_id:
            dashboard = next(
                (d for d in dashboards if d.get("dashboard_id") == source_id),
                None,
            )
            if not dashboard:
                raise ValueError(f"Dashboard {source_id} not found")
            dashboards = [dashboard]

        # Filter by dataset_id
        matching = [
            d for d in dashboards if d.get("dataset_id") == dataset_id
        ]

        return ExportSourceData(
            data=matching,
            metadata={
                "dashboard_count": len(matching),
                "dataset_id": dataset_id,
            },
            provenance=self._build_provenance(
                dataset_id, version_id, "dashboard", source_id
            ),
        )


class AiAnalystSourceReader(BaseSourceReader):
    """Reads AI analyst session results from data/ai_analyst/."""

    def read(
        self,
        dataset_id: str,
        version_id: str,
        source_id: Optional[str] = None,
    ) -> ExportSourceData:
        ai_dir = os.path.join(settings.DATA_AI_ANALYST_DIR, dataset_id)
        if not os.path.isdir(ai_dir):
            raise ValueError(f"No AI analyst sessions for dataset {dataset_id}")

        if source_id:
            result_path = os.path.join(ai_dir, f"{source_id}.json")
        else:
            files = sorted(
                [f for f in os.listdir(ai_dir) if f.endswith(".json")],
                key=lambda x: os.path.getmtime(os.path.join(ai_dir, x)),
                reverse=True,
            )
            if not files:
                raise ValueError(f"No AI analyst sessions found in {ai_dir}")
            result_path = os.path.join(ai_dir, files[0])
            source_id = files[0].replace(".json", "")

        data = self._read_json_file(result_path)
        if not data:
            raise ValueError(f"AI analyst session not found at {result_path}")

        return ExportSourceData(
            data=data if isinstance(data, list) else [data],
            metadata={
                "session_id": source_id,
            },
            provenance=self._build_provenance(
                dataset_id, version_id, "ai_analyst", source_id
            ),
        )


# ─────────────────────────────────────────────────────────────
# Source Reader Registry
# ─────────────────────────────────────────────────────────────

SOURCE_READERS = {
    ExportSourceType.DATASET: DatasetSourceReader,
    ExportSourceType.SQL_RESULT: SqlResultSourceReader,
    ExportSourceType.PROFILE: ProfileSourceReader,
    ExportSourceType.QUALITY_REPORT: QualitySourceReader,
    ExportSourceType.EDA_RESULT: EdaSourceReader,
    ExportSourceType.STATISTICS_RESULT: StatisticsSourceReader,
    ExportSourceType.ML_RESULT: MlSourceReader,
    ExportSourceType.FORECAST_RESULT: ForecastSourceReader,
    ExportSourceType.DASHBOARD: DashboardSourceReader,
    ExportSourceType.AI_ANALYST_SESSION: AiAnalystSourceReader,
}


def get_source_reader(source_type: ExportSourceType) -> BaseSourceReader:
    """Factory function to get the appropriate source reader."""
    reader_class = SOURCE_READERS.get(source_type)
    if not reader_class:
        raise ValueError(f"Unsupported export source type: {source_type}")
    return reader_class()
