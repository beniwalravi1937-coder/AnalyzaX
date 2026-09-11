"""
AnalyzaX — Phase 24 Tests: DuckDB External Access Lockdown, System Catalog Sandbox & Query Defenses.
Verifies hardware containment, config locking, external filesystem/network isolation, and system catalog blocking.
"""

import pytest

from backend.app.engines.sql.executor import SQLExecutor
from backend.app.engines.sql.models import QueryStatus
from backend.app.engines.sql.validator import SQLValidator


def test_sql_validator_blocks_system_catalogs_and_external_functions():
    validator = SQLValidator()

    # System catalogs blocked
    sys_queries = [
        "SELECT * FROM duckdb_settings;",
        "SELECT * FROM duckdb_tables();",
        "SELECT * FROM duckdb_views();",
        "SELECT * FROM duckdb_secrets();",
        "SELECT * FROM information_schema.tables;",
        "SELECT * FROM information_schema.columns;",
    ]
    for q in sys_queries:
        res = validator.validate(q)
        assert res.is_valid is False, f"Expected query '{q}' to be blocked by validator"
        assert any("catalog" in e.message.lower() or "system table" in e.message.lower() or "forbidden" in e.message.lower() for e in res.errors)

    # External filesystem & network access blocked by validator
    ext_queries = [
        "SELECT * FROM read_parquet('/etc/passwd');",
        "SELECT * FROM read_csv_auto('http://evil.com/malware.csv');",
        "COPY (SELECT 1) TO '/tmp/pwned.csv';",
        "ATTACH 'evil.db';",
        "INSTALL httpfs;",
        "LOAD httpfs;",
    ]
    for q in ext_queries:
        res = validator.validate(q)
        assert res.is_valid is False, f"Expected query '{q}' to be blocked"


def test_sql_executor_duckdb_sandbox_enforces_external_access_lock(tmp_path):
    """
    Directly verifies at the DuckDB engine level that enable_external_access=false
    and lock_configuration=true prevent external reads or setting overrides.
    """
    import os
    import polars as pl
    parquet_file = os.path.join(tmp_path, "sample.parquet")
    df = pl.DataFrame({"id": [1, 2, 3], "val": [10, 20, 30]})
    df.write_parquet(parquet_file)

    # Execute a safe query
    res = SQLExecutor.execute(
        sql="SELECT id, val FROM dataset WHERE id = 1;",
        storage_path=parquet_file,
        dataset_id="ds_sec",
        version_id="v1",
    )
    assert res.row_count == 1

    # 1. Attempt to override configuration lock
    res_lock = SQLExecutor.execute(
        sql="SET enable_external_access = true;",
        storage_path=parquet_file,
        dataset_id="ds_sec",
        version_id="v1",
    )
    assert res_lock.status == QueryStatus.FAILED
    assert any(w in (res_lock.error_message or "").lower() for w in ["lock", "cannot change", "invalid input"])

    # 2. Attempt to bypass and read filesystem directly
    res_read = SQLExecutor.execute(
        sql="SELECT * FROM read_parquet('C:/Windows/notepad.exe');",
        storage_path=parquet_file,
        dataset_id="ds_sec",
        version_id="v1",
    )
    assert res_read.status == QueryStatus.FAILED
    assert any(w in (res_read.error_message or "").lower() for w in ["disabled", "permission", "file system", "access"])
