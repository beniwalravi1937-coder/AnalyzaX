import os
import re
from typing import Dict, Any

from backend.app.core.logging import logger
from backend.app.services.duckdb_service import DuckDBService


def register_dataset_view(
    duckdb_svc: DuckDBService,
    table_name: str,
    file_path: str,
    format_str: str,
) -> Dict[str, Any]:
    """
    Registers an analytical SQL view in the DuckDB engine.
    Ensures safe identifier naming and validates that the view can be queried.

    Args:
        duckdb_svc: DuckDBService singleton instance
        table_name: Safe validated table name (e.g. dataset_ds_01j...)
        file_path: Absolute path to the Parquet or CSV file
        format_str: 'csv' or 'parquet'

    Returns:
        dict: Ingestion probe results (row count, status)
    """
    # Strict SQL identifier verification
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", table_name):
        raise ValueError(f"Invalid SQL table name: {table_name}")

    # Standardize path for DuckDB SQL parser (forward slashes)
    clean_path = os.path.abspath(file_path).replace("\\", "/")

    if format_str == "parquet":
        sql = f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_parquet('{clean_path}');"
    elif format_str == "csv":
        sql = f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_csv_auto('{clean_path}', header=True);"
    else:
        raise ValueError(f"Unsupported format for direct DuckDB registration: {format_str}")

    with duckdb_svc.get_exclusive_connection() as conn:
        logger.info(f"Registering DuckDB view: {table_name} for file {clean_path}")
        conn.execute(sql)

        # Verification probe: check that the table can be queried
        probe_result = conn.execute(f"SELECT COUNT(*) AS count FROM {table_name};").fetchone()
        row_count = probe_result[0] if probe_result else 0
        logger.info(f"DuckDB view {table_name} registered successfully. Row count probe: {row_count}")

    return {
        "table_name": table_name,
        "row_count": row_count,
        "status": "ready",
    }


def unregister_dataset_view(duckdb_svc: DuckDBService, table_name: str) -> bool:
    """
    Safely drops a dataset view from DuckDB when deleted.
    """
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", table_name):
        return False

    with duckdb_svc.get_exclusive_connection() as conn:
        conn.execute(f"DROP VIEW IF EXISTS {table_name};")
        logger.info(f"DuckDB view {table_name} dropped.")
    return True
