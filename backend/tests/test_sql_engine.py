"""
Tests for Phase 8 Safe DuckDB SQL Execution Engine.
"""

import os
import tempfile
import polars as pl
import pytest
from backend.app.engines.sql.executor import SQLExecutor
from backend.app.engines.sql.models import QueryStatus


@pytest.fixture
def sample_parquet(tmp_path):
    filepath = os.path.join(tmp_path, "sample_orders.parquet")
    df = pl.DataFrame({
        "order_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "customer": ["Alice", "Bob", "Alice", "Charlie", "Bob", "Alice", "Charlie", "David", "Eve", "Frank"],
        "category": ["Electronics", "Clothing", "Electronics", "Home", "Clothing", "Home", "Electronics", "Home", "Clothing", "Electronics"],
        "amount": [120.50, 45.00, 310.00, 89.99, 15.50, 220.00, 450.00, 60.00, 110.00, 95.00],
        "quantity": [1, 2, 3, 1, 1, 2, 4, 1, 2, 1],
    })
    df.write_parquet(filepath)
    return str(filepath)


def test_execute_simple_select(sample_parquet):
    resp = SQLExecutor.execute(
        sql="SELECT order_id, customer, amount FROM dataset WHERE amount > 100 ORDER BY amount DESC;",
        storage_path=sample_parquet,
        dataset_id="test_ds",
        version_id="v1",
        friendly_name="orders",
        max_rows=100,
    )
    assert resp.status == QueryStatus.COMPLETED
    assert resp.row_count == 5
    assert len(resp.columns) == 3
    assert resp.rows[0]["amount"] == 450.00
    assert resp.rows[0]["customer"] == "Charlie"
    assert resp.error_message is None
    assert resp.execution_time_ms > 0


def test_execute_group_by_aggregation(sample_parquet):
    resp = SQLExecutor.execute(
        sql="""
        SELECT
            category,
            count(*) as order_count,
            round(sum(amount), 2) as total_revenue,
            round(avg(amount), 2) as avg_order
        FROM orders
        GROUP BY category
        ORDER BY total_revenue DESC;
        """,
        storage_path=sample_parquet,
        dataset_id="test_ds",
        version_id="v1",
        friendly_name="orders",
    )
    assert resp.status == QueryStatus.COMPLETED
    assert resp.row_count == 3
    assert resp.rows[0]["category"] == "Electronics"
    assert resp.rows[0]["total_revenue"] == 975.50


def test_execute_window_function(sample_parquet):
    resp = SQLExecutor.execute(
        sql="""
        SELECT
            customer,
            amount,
            rank() OVER (ORDER BY amount DESC) as spend_rank
        FROM dataset
        LIMIT 3;
        """,
        storage_path=sample_parquet,
        dataset_id="test_ds",
        version_id="v1",
    )
    assert resp.status == QueryStatus.COMPLETED
    assert resp.row_count == 3
    assert resp.rows[0]["spend_rank"] == 1


def test_execute_cte_and_filter(sample_parquet):
    resp = SQLExecutor.execute(
        sql="""
        WITH customer_totals AS (
            SELECT customer, sum(amount) as total_spent
            FROM dataset
            GROUP BY customer
        )
        SELECT * FROM customer_totals WHERE total_spent >= 200 ORDER BY total_spent DESC;
        """,
        storage_path=sample_parquet,
        dataset_id="test_ds",
        version_id="v1",
    )
    assert resp.status == QueryStatus.COMPLETED
    assert resp.row_count == 2
    assert resp.rows[0]["customer"] == "Alice"


def test_explain_query(sample_parquet):
    explain_res = SQLExecutor.explain(
        sql="SELECT category, avg(amount) FROM dataset GROUP BY category;",
        storage_path=sample_parquet,
        dataset_id="test_ds",
        version_id="v1",
    )
    assert explain_res.plan_text != ""
    assert "PROJECTION" in explain_res.plan_text or "SCAN" in explain_res.plan_text or "AGGREGATE" in explain_res.plan_text
    # Verify local file paths are not leaked in explain text
    assert sample_parquet not in explain_res.plan_text
