import duckdb
import pytest

from backend.app.engines.profiling.categorical import profile_categorical_column
from backend.app.engines.profiling.datetime_prof import profile_datetime_column
from backend.app.engines.profiling.engine import DatasetProfiler
from backend.app.engines.profiling.numeric import profile_numeric_column
from backend.app.engines.profiling.physical import map_duckdb_physical_type
from backend.app.engines.profiling.semantic import infer_semantic_type
from backend.app.engines.profiling.targets import evaluate_target_candidate
from backend.app.schemas.profile import ColumnProfile


def test_map_duckdb_physical_type():
    assert map_duckdb_physical_type("BIGINT") == "integer"
    assert map_duckdb_physical_type("INTEGER") == "integer"
    assert map_duckdb_physical_type("DOUBLE") == "float"
    assert map_duckdb_physical_type("DECIMAL(10,2)") == "decimal"
    assert map_duckdb_physical_type("BOOLEAN") == "boolean"
    assert map_duckdb_physical_type("VARCHAR") == "string"
    assert map_duckdb_physical_type("DATE") == "date"
    assert map_duckdb_physical_type("TIMESTAMP") == "datetime"
    assert map_duckdb_physical_type("TIME") == "time"


def test_profile_numeric_column():
    conn = duckdb.connect()
    conn.execute("""
        CREATE TABLE test_num (
            val DOUBLE,
            const_val INT,
            all_null DOUBLE
        );
        INSERT INTO test_num VALUES
            (10.0, 5, NULL),
            (20.0, 5, NULL),
            (30.0, 5, NULL),
            (40.0, 5, NULL),
            (50.0, 5, NULL);
    """)

    # Standard numeric column
    res = profile_numeric_column(conn, "test_num", "val", total_rows=5)
    assert res["null_count"] == 0
    assert res["null_percentage"] == 0.0
    assert res["unique_count"] == 5
    m = res["numeric_metrics"]
    assert m is not None
    assert m.min == 10.0
    assert m.max == 50.0
    assert m.mean == 30.0
    assert m.median == 30.0
    assert m.quantiles is not None
    assert m.quantiles.p0 == 10.0
    assert m.quantiles.p50 == 30.0
    assert m.quantiles.p100 == 50.0
    assert m.quantiles.iqr == 20.0  # P75 (40) - P25 (20)

    # Constant column
    const_res = profile_numeric_column(conn, "test_num", "const_val", total_rows=5)
    assert const_res["unique_count"] == 1
    assert const_res["numeric_metrics"].min == 5.0
    assert const_res["numeric_metrics"].max == 5.0

    # All-null column
    null_res = profile_numeric_column(conn, "test_num", "all_null", total_rows=5)
    assert null_res["null_count"] == 5
    assert null_res["null_percentage"] == 100.0
    assert null_res["numeric_metrics"] is None


def test_profile_categorical_column():
    conn = duckdb.connect()
    conn.execute("""
        CREATE TABLE test_cat (
            category VARCHAR,
            review_text VARCHAR
        );
        INSERT INTO test_cat VALUES
            ('Electronics', 'This is an extremely long user review describing the product in great detail with many sentences.'),
            ('Electronics', 'Another very detailed and comprehensive customer review with long paragraphs.'),
            ('Clothing', 'A third customer feedback message with lengthy impressions and descriptions.'),
            ('Home', 'Fourth comprehensive customer testimony containing multiple complete thoughts.');
    """)

    res = profile_categorical_column(conn, "test_cat", "category", total_rows=4)
    assert res["null_count"] == 0
    assert res["unique_count"] == 3
    m = res["categorical_metrics"]
    assert len(m.top_categories) == 3
    assert m.top_categories[0].value == "Electronics"
    assert m.top_categories[0].count == 2
    assert m.top_categories[0].percentage == 50.0
    assert m.is_text is False

    # Long-form text detection
    text_res = profile_categorical_column(conn, "test_cat", "review_text", total_rows=4)
    assert text_res["categorical_metrics"].is_text is True


def test_profile_datetime_column():
    conn = duckdb.connect()
    conn.execute("""
        CREATE TABLE test_dt (
            event_time TIMESTAMP
        );
        INSERT INTO test_dt VALUES
            ('2026-01-01 10:00:00'),
            ('2026-01-02 10:00:00'),
            ('2026-01-03 10:00:00'),
            ('2026-01-04 10:00:00'),
            ('2026-01-05 10:00:00');
    """)

    res = profile_datetime_column(conn, "test_dt", "event_time", total_rows=5)
    assert res["null_count"] == 0
    m = res["datetime_metrics"]
    assert m.min_timestamp.startswith("2026-01-01")
    assert m.max_timestamp.startswith("2026-01-05")
    assert m.span_days == 4.0
    assert m.distinct_dates_count == 5
    assert m.detected_frequency == "daily"


def test_semantic_inference():
    # Monetary
    sem, conf, is_id, _ = infer_semantic_type(
        col_name="annual_revenue",
        physical_type="float",
        unique_count=100,
        total_non_null=100,
        cardinality_ratio=1.0,
        sample_values=[150000.0, 240000.0],
        min_val=1000.0,
        max_val=500000.0,
    )
    assert sem == "monetary"
    assert conf >= 0.85

    # Percentage
    sem_pct, conf_pct, _, _ = infer_semantic_type(
        col_name="profit_margin_pct",
        physical_type="float",
        unique_count=50,
        total_non_null=100,
        cardinality_ratio=0.5,
        sample_values=[15.5, 22.1],
        min_val=0.0,
        max_val=100.0,
    )
    assert sem_pct == "percentage"
    assert conf_pct >= 0.85

    # Identifier
    sem_id, conf_id, is_id, id_conf = infer_semantic_type(
        col_name="customer_id",
        physical_type="integer",
        unique_count=1000,
        total_non_null=1000,
        cardinality_ratio=1.0,
        sample_values=[1, 2, 3],
    )
    assert sem_id == "identifier"
    assert is_id is True
    assert id_conf >= 0.90

    # Email
    sem_email, conf_email, _, _ = infer_semantic_type(
        col_name="contact_email",
        physical_type="string",
        unique_count=100,
        total_non_null=100,
        cardinality_ratio=1.0,
        sample_values=["alice@test.com", "bob@test.org"],
    )
    assert sem_email == "email"

    # Geographic Latitude
    sem_lat, conf_lat, _, _ = infer_semantic_type(
        col_name="latitude",
        physical_type="float",
        unique_count=80,
        total_non_null=100,
        cardinality_ratio=0.8,
        sample_values=[37.77, 40.71],
        min_val=30.0,
        max_val=45.0,
    )
    assert sem_lat == "geographic_latitude"


def test_target_candidate_detection():
    # Binary classification candidate
    bin_col = ColumnProfile(
        name="churned",
        physical_type="string",
        semantic_type="boolean",
        unique_count=2,
        null_count=0,
        null_percentage=0.0,
        unique_percentage=2.0,
        cardinality_ratio=0.02,
        is_identifier_candidate=False,
    )
    cand_bin = evaluate_target_candidate(bin_col)
    assert cand_bin is not None
    assert cand_bin.task_type == "binary_classification"

    # Regression candidate
    from backend.app.schemas.profile import NumericMetrics
    reg_col = ColumnProfile(
        name="house_price",
        physical_type="float",
        semantic_type="monetary",
        unique_count=250,
        null_count=0,
        null_percentage=0.0,
        unique_percentage=50.0,
        cardinality_ratio=0.5,
        numeric_metrics=NumericMetrics(variance=45000000.0, min=100000.0, max=800000.0),
        is_identifier_candidate=False,
    )
    cand_reg = evaluate_target_candidate(reg_col)
    assert cand_reg is not None
    assert cand_reg.task_type == "regression"

    # Reject identifier
    id_col = ColumnProfile(
        name="order_id",
        physical_type="integer",
        semantic_type="identifier",
        unique_count=500,
        null_count=0,
        null_percentage=0.0,
        unique_percentage=100.0,
        cardinality_ratio=1.0,
        is_identifier_candidate=True,
    )
    assert evaluate_target_candidate(id_col) is None


def test_dataset_profiler_end_to_end():
    conn = duckdb.connect()
    conn.execute("""
        CREATE TABLE sales_test (
            id INT,
            product VARCHAR,
            amount DOUBLE,
            is_active BOOLEAN,
            sale_date DATE
        );
        INSERT INTO sales_test VALUES
            (1, 'Laptop', 1200.0, TRUE, '2026-01-01'),
            (2, 'Mouse', 25.0, TRUE, '2026-01-02'),
            (3, 'Monitor', 300.0, FALSE, '2026-01-03');
    """)

    profiler = DatasetProfiler()
    profile = profiler.profile_table(conn, "sales_test", dataset_id="ds_test_123")

    assert profile.dataset_id == "ds_test_123"
    assert profile.row_count == 3
    assert profile.column_count == 5
    assert profile.numeric_columns_count >= 2
    assert profile.categorical_columns_count >= 1
    assert profile.datetime_columns_count >= 1

    # Check that sample values are present
    amount_col = next(c for c in profile.columns if c.name == "amount")
    assert len(amount_col.sample_values) == 3
    assert amount_col.numeric_metrics.mean is not None
    assert amount_col.semantic_type == "monetary"
