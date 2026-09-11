"""
Tests for Phase 8 SQL Security & Semantic Validator.
"""

import pytest
from backend.app.engines.sql.validator import SQLValidator


@pytest.mark.parametrize(
    "sql,forbidden_word",
    [
        ("DROP TABLE customers;", "DROP"),
        ("DELETE FROM sales WHERE id = 1;", "DELETE"),
        ("UPDATE sales SET revenue = 0;", "UPDATE"),
        ("INSERT INTO sales VALUES (1, 'demo');", "INSERT"),
        ("ALTER TABLE sales ADD COLUMN test INT;", "ALTER"),
        ("CREATE TABLE evil (x INT);", "CREATE"),
        ("TRUNCATE TABLE sales;", "TRUNCATE"),
        ("COPY sales TO 'secret.csv';", "COPY"),
        ("ATTACH 'other.db';", "ATTACH"),
        ("DETACH other;", "DETACH"),
        ("INSTALL httpfs;", "INSTALL"),
        ("LOAD httpfs;", "LOAD"),
        ("PRAGMA show_tables;", "PRAGMA"),
        ("CALL custom_proc();", "CALL"),
        ("SELECT * FROM read_parquet('d:/passwords.txt');", "read_parquet"),
    ],
)
def test_validator_blocks_mutations_and_security_violations(sql, forbidden_word):
    result = SQLValidator.validate(sql)
    assert result.is_valid is False
    assert len(result.errors) > 0
    assert any(forbidden_word.lower() in e.message.lower() for e in result.errors)


def test_validator_accepts_clean_select():
    sql = "SELECT id, category, revenue FROM dataset WHERE revenue > 50 ORDER BY revenue DESC LIMIT 20;"
    result = SQLValidator.validate(
        sql,
        valid_tables=["dataset"],
        valid_columns=["id", "category", "revenue", "created_at"],
    )
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validator_suggests_column_typos():
    sql = "SELECT revenuu FROM dataset LIMIT 10;"
    result = SQLValidator.validate(
        sql,
        valid_tables=["dataset"],
        valid_columns=["revenue", "customer_id", "product_name"],
    )
    assert result.is_valid is True  # Query is executable, but warning emitted
    assert len(result.warnings) > 0
    typo_warning = next((w for w in result.warnings if w.warning_code == "COLUMN_TYPO"), None)
    assert typo_warning is not None
    assert typo_warning.suggestion == "revenue"


def test_validator_warns_on_unbounded_select():
    sql = "SELECT * FROM dataset;"
    result = SQLValidator.validate(sql)
    assert result.is_valid is True
    assert any(w.warning_code == "MISSING_LIMIT" for w in result.warnings)
