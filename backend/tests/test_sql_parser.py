"""
Tests for Phase 8 SQL Parser and AST extraction.
"""

import pytest
from backend.app.engines.sql.models import SQLStatementType
from backend.app.engines.sql.parser import SQLParser


def test_parse_simple_select():
    ast, errors = SQLParser.parse("SELECT customer_id, revenue FROM sales WHERE revenue > 100 LIMIT 10;")
    assert len(errors) == 0
    assert ast is not None
    assert ast.statement_type == SQLStatementType.SELECT
    assert ast.statement_count == 1
    assert "sales" in ast.tables
    assert "customer_id" in ast.columns or "revenue" in ast.columns
    assert ast.has_limit is True
    assert ast.limit_value == 10
    assert ast.has_cartesian_join is False


def test_parse_rejects_multiple_statements():
    ast, errors = SQLParser.parse("SELECT 1; DROP TABLE customers;")
    assert len(errors) > 0
    assert any("Multiple SQL statements" in e.message for e in errors)
    assert ast is None


def test_parse_empty_query():
    ast, errors = SQLParser.parse("   ")
    assert len(errors) > 0
    assert any("empty" in e.message for e in errors)
    assert ast is None


def test_parse_syntax_error():
    ast, errors = SQLParser.parse("SELECT FROM WHERE 123;")
    assert len(errors) > 0
    assert any(e.error_code == "SYNTAX_ERROR" for e in errors)


def test_parse_cte_query():
    sql = """
    WITH regional_sales AS (
        SELECT region, sum(revenue) as total_rev
        FROM sales
        GROUP BY region
    )
    SELECT * FROM regional_sales WHERE total_rev > 50000;
    """
    ast, errors = SQLParser.parse(sql)
    assert len(errors) == 0
    assert ast is not None
    assert ast.statement_type == SQLStatementType.SELECT
    assert "sales" in ast.tables or "regional_sales" in ast.tables


def test_detect_cartesian_join():
    sql = "SELECT * FROM table_a CROSS JOIN table_b;"
    ast, errors = SQLParser.parse(sql)
    assert len(errors) == 0
    assert ast.has_cartesian_join is True

    sql_comma = "SELECT * FROM table_a, table_b;"
    ast2, errors2 = SQLParser.parse(sql_comma)
    assert len(errors2) == 0
    assert ast2.has_cartesian_join is True
