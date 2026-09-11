"""
Tests for Safe Arithmetic Expression Parser
Validates safe AST evaluation and strict rejection of dangerous code.
"""

import pytest
import polars as pl
from backend.app.engines.transformations.expression_parser import (
    SafeExpressionParser,
    UnsafeExpressionError,
)


def test_safe_arithmetic_compilation():
    df = pl.DataFrame({
        "price": [10.0, 20.0, 30.0],
        "quantity": [2, 3, 4],
        "discount": [1.0, 2.0, 5.0],
    })

    # Test basic multiplication
    expr = SafeExpressionParser.compile_expression("price * quantity", df.columns)
    res = df.select(expr.alias("total"))
    assert res["total"].to_list() == [20.0, 60.0, 120.0]

    # Test nested formula
    expr2 = SafeExpressionParser.compile_expression("(price * quantity) - discount", df.columns)
    res2 = df.select(expr2.alias("net"))
    assert res2["net"].to_list() == [19.0, 58.0, 115.0]

    # Test numeric constants and unary negation
    expr3 = SafeExpressionParser.compile_expression("-(price + 5) / 2", df.columns)
    res3 = df.select(expr3.alias("calc"))
    assert res3["calc"].to_list() == [-7.5, -12.5, -17.5]


def test_extract_referenced_columns():
    cols = SafeExpressionParser.extract_referenced_columns("(revenue - cost) * (1 + tax_rate)")
    assert cols == {"revenue", "cost", "tax_rate"}


def test_reject_unsafe_expressions():
    available = ["price", "quantity"]

    # Reject function calls
    with pytest.raises(UnsafeExpressionError):
        SafeExpressionParser.compile_expression("__import__('os').system('ls')", available)

    with pytest.raises(UnsafeExpressionError):
        SafeExpressionParser.compile_expression("eval('2 + 2')", available)

    # Reject attribute access
    with pytest.raises(UnsafeExpressionError):
        SafeExpressionParser.compile_expression("price.__class__", available)

    # Reject non-existent columns
    with pytest.raises(UnsafeExpressionError):
        SafeExpressionParser.compile_expression("price + unknown_column", available)

    # Reject empty expressions
    with pytest.raises(UnsafeExpressionError):
        SafeExpressionParser.compile_expression("", available)
