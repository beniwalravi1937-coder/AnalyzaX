import os
import pytest

from backend.app.engines.ingestion import (
    detect_file_format,
    generate_dataset_id,
    generate_safe_sql_identifier,
    normalize_dataset,
    register_dataset_view,
    sanitize_filename,
    unregister_dataset_view,
    validate_dataset_content,
)
from backend.app.services.duckdb_service import duckdb_service

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_sanitize_filename():
    assert sanitize_filename("normal_file.csv") == "normal_file.csv"
    assert sanitize_filename("../../etc/passwd.csv") == "passwd.csv"
    assert sanitize_filename("C:\\Windows\\System32\\bad.xlsx") == "bad.xlsx"
    assert sanitize_filename("my test  file (1).json") == "my_test_file_1.json"
    assert sanitize_filename("file\x00with_null.csv") == "filewith_null.csv"


def test_generate_dataset_id():
    id1 = generate_dataset_id()
    id2 = generate_dataset_id()
    assert id1.startswith("ds_")
    assert id2.startswith("ds_")
    assert id1 != id2
    assert len(id1) >= 16


def test_generate_safe_sql_identifier():
    dataset_id = "ds_66dd8f12a3bc49f81b"
    table_name = generate_safe_sql_identifier(dataset_id)
    assert table_name == "dataset_ds_66dd8f12a3bc49f81b"

    # Must reject dangerous characters
    with pytest.raises(ValueError):
        generate_safe_sql_identifier("ds; DROP TABLE users;--")


def test_detector_supported_formats():
    sales_csv = os.path.join(FIXTURES_DIR, "small_sales.csv")
    customers_csv = os.path.join(FIXTURES_DIR, "small_customers.csv")
    sample_json = os.path.join(FIXTURES_DIR, "sample.json")
    sample_parquet = os.path.join(FIXTURES_DIR, "sample.parquet")
    sample_xlsx = os.path.join(FIXTURES_DIR, "sample.xlsx")

    assert detect_file_format(sales_csv, "small_sales.csv") == "csv"
    assert detect_file_format(customers_csv, "small_customers.csv") == "csv"
    assert detect_file_format(sample_json, "sample.json") == "json"
    assert detect_file_format(sample_parquet, "sample.parquet") == "parquet"
    assert detect_file_format(sample_xlsx, "sample.xlsx") == "xlsx"


def test_detector_unsupported_format():
    unsupported = os.path.join(FIXTURES_DIR, "unsupported.txt")
    with pytest.raises(ValueError, match="Unsupported file format"):
        detect_file_format(unsupported, "unsupported.txt")


def test_validator_csv():
    sales_csv = os.path.join(FIXTURES_DIR, "small_sales.csv")
    meta = validate_dataset_content(sales_csv, "csv")
    assert meta["format"] == "csv"
    assert meta["delimiter"] == ","
    assert meta["has_header"] is True

    customers_csv = os.path.join(FIXTURES_DIR, "small_customers.csv")
    meta_cust = validate_dataset_content(customers_csv, "csv")
    assert meta_cust["delimiter"] == ";"


def test_validator_empty_csv():
    invalid_csv = os.path.join(FIXTURES_DIR, "invalid.csv")
    with pytest.raises(ValueError, match="CSV file is empty"):
        validate_dataset_content(invalid_csv, "csv")


def test_validator_parquet():
    sample_parquet = os.path.join(FIXTURES_DIR, "sample.parquet")
    meta = validate_dataset_content(sample_parquet, "parquet")
    assert meta["format"] == "parquet"
    assert "employee_id" in meta["columns"]
    assert "salary" in meta["columns"]


def test_validator_json():
    sample_json = os.path.join(FIXTURES_DIR, "sample.json")
    meta = validate_dataset_content(sample_json, "json")
    assert meta["format"] == "json"
    assert "order_id" in meta["columns"]
    assert "total" in meta["columns"]


def test_validator_xlsx():
    sample_xlsx = os.path.join(FIXTURES_DIR, "sample.xlsx")
    meta = validate_dataset_content(sample_xlsx, "xlsx")
    assert meta["format"] == "xlsx"
    assert meta["selected_sheet"] == "MonthlyRevenue"


def test_normalizer_and_duckdb_registration(tmp_path):
    # Test CSV registration directly
    sales_csv = os.path.join(FIXTURES_DIR, "small_sales.csv")
    table_csv = "dataset_test_sales_csv"

    reg_csv = register_dataset_view(duckdb_service, table_csv, sales_csv, "csv")
    assert reg_csv["status"] == "ready"
    assert reg_csv["row_count"] == 3

    # Query DuckDB
    with duckdb_service.get_connection() as conn:
        res = conn.execute(f"SELECT sum(quantity) FROM {table_csv};").fetchone()
        assert res[0] == 8

    unregister_dataset_view(duckdb_service, table_csv)

    # Test Parquet registration directly
    sample_parquet = os.path.join(FIXTURES_DIR, "sample.parquet")
    table_pq = "dataset_test_pq"
    reg_pq = register_dataset_view(duckdb_service, table_pq, sample_parquet, "parquet")
    assert reg_pq["row_count"] == 3
    unregister_dataset_view(duckdb_service, table_pq)

    # Test XLSX normalization to Parquet
    sample_xlsx = os.path.join(FIXTURES_DIR, "sample.xlsx")
    norm_pq = normalize_dataset(sample_xlsx, "xlsx", str(tmp_path), sheet_name="MonthlyRevenue")
    assert norm_pq is not None
    assert os.path.exists(norm_pq)

    table_xlsx = "dataset_test_xlsx"
    reg_xlsx = register_dataset_view(duckdb_service, table_xlsx, norm_pq, "parquet")
    assert reg_xlsx["row_count"] == 3
    unregister_dataset_view(duckdb_service, table_xlsx)
