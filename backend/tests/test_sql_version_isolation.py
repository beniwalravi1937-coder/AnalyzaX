"""
Tests for Phase 8 Version Awareness & Isolation.
Verifies that the SQL engine strictly isolates dataset versions and never conflates them.
"""

import os
import polars as pl
import pytest
from backend.app.engines.sql.executor import SQLExecutor
from backend.app.engines.sql.models import QueryStatus


@pytest.fixture
def version_files(tmp_path):
    v1_path = os.path.join(tmp_path, "v1.parquet")
    v2_path = os.path.join(tmp_path, "v2.parquet")

    # V1: 5 rows, raw prices
    df_v1 = pl.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["A", "B", "C", "D", "E"],
        "price": [10.0, 20.0, 30.0, 40.0, 50.0],
    })
    df_v1.write_parquet(v1_path)

    # V2: Transformed dataset — filtered outliers, inflated prices, new column
    df_v2 = pl.DataFrame({
        "id": [1, 2, 3],
        "name": ["A", "B", "C"],
        "price": [15.0, 30.0, 45.0],
        "status": ["active", "active", "pending"],
    })
    df_v2.write_parquet(v2_path)

    return str(v1_path), str(v2_path)


def test_version_isolation_same_query_different_data(version_files):
    v1_path, v2_path = version_files
    query = "SELECT count(*) AS total_rows, sum(price) AS total_price FROM dataset;"

    # Run on V1
    resp_v1 = SQLExecutor.execute(
        sql=query,
        storage_path=v1_path,
        dataset_id="test_ds",
        version_id="v1",
    )
    assert resp_v1.status == QueryStatus.COMPLETED
    assert resp_v1.rows[0]["total_rows"] == 5
    assert resp_v1.rows[0]["total_price"] == 150.0

    # Run on V2
    resp_v2 = SQLExecutor.execute(
        sql=query,
        storage_path=v2_path,
        dataset_id="test_ds",
        version_id="v2",
    )
    assert resp_v2.status == QueryStatus.COMPLETED
    assert resp_v2.rows[0]["total_rows"] == 3
    assert resp_v2.rows[0]["total_price"] == 90.0

    # V2 has 'status' column, V1 does not
    resp_v2_status = SQLExecutor.execute(
        sql="SELECT id, status FROM dataset WHERE status = 'pending';",
        storage_path=v2_path,
        dataset_id="test_ds",
        version_id="v2",
    )
    assert resp_v2_status.status == QueryStatus.COMPLETED
    assert resp_v2_status.row_count == 1
    assert resp_v2_status.rows[0]["id"] == 3

    # Running against V1 must fail because 'status' column doesn't exist
    resp_v1_status = SQLExecutor.execute(
        sql="SELECT id, status FROM dataset WHERE status = 'pending';",
        storage_path=v1_path,
        dataset_id="test_ds",
        version_id="v1",
    )
    assert resp_v1_status.status == QueryStatus.FAILED
    assert "status" in resp_v1_status.error_message
