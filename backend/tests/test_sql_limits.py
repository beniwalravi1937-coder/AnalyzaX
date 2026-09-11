"""
Tests for Phase 8 SQL Execution Resource Limits & Containment.
"""

import os
import threading
import time
import polars as pl
import pytest
from backend.app.engines.sql.executor import SQLExecutor, query_registry
from backend.app.engines.sql.models import QueryStatus


@pytest.fixture
def large_parquet(tmp_path):
    filepath = os.path.join(tmp_path, "large_table.parquet")
    n = 1000
    df = pl.DataFrame({
        "id": list(range(n)),
        "value": [f"item_{i}" for i in range(n)],
    })
    df.write_parquet(filepath)
    return str(filepath)


def test_row_limit_truncation(large_parquet):
    resp = SQLExecutor.execute(
        sql="SELECT * FROM dataset;",
        storage_path=large_parquet,
        dataset_id="test_ds",
        version_id="v1",
        max_rows=50,
    )
    assert resp.status == QueryStatus.COMPLETED
    assert resp.row_count == 50
    assert resp.is_truncated is True


def test_query_timeout_interruption(large_parquet):
    resp = SQLExecutor.execute(
        sql="SELECT sum(hash(a.range, b.range)) FROM range(5000000) a, range(10) b;",
        storage_path=large_parquet,
        dataset_id="test_ds",
        version_id="v1",
        timeout_seconds=0.05,
    )
    assert resp.status == QueryStatus.TIMEOUT
    assert resp.error_message is not None
    assert "timed out" in resp.error_message.lower()


def test_query_cancellation(large_parquet):
    query_id = "cancellation_test_query"

    def cancel_after_delay():
        time.sleep(0.05)
        query_registry.cancel(query_id)

    thread = threading.Thread(target=cancel_after_delay)
    thread.start()

    resp = SQLExecutor.execute(
        sql="SELECT sum(hash(a.range, b.range)) FROM range(5000000) a, range(10) b;",
        storage_path=large_parquet,
        dataset_id="test_ds",
        version_id="v1",
        timeout_seconds=5.0,
        query_id=query_id,
    )
    thread.join()
    assert resp.status in (QueryStatus.CANCELLED, QueryStatus.TIMEOUT, QueryStatus.FAILED)
