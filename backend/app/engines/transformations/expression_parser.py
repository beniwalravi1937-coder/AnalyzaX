"""
Safe Arithmetic Expression Parser
Parses and compiles user-defined mathematical formulas into native Polars expressions
without using eval(), exec(), or allowing arbitrary Python execution.
"""

import ast
from typing import List, Set
import polars as pl


class UnsafeExpressionError(ValueError):
    """Raised when an expression contains disallowed syntax or operations."""
    pass


class SafeExpressionParser:
    """
    Compiles arithmetic formulas into native Polars expressions using an AST allowlist.
    Only basic mathematical operations (+, -, *, /, %, **) on columns and numeric literals are permitted.
    """

    ALLOWED_BINARY_OPS = {
        ast.Add: lambda left, right: left + right,
        ast.Sub: lambda left, right: left - right,
        ast.Mult: lambda left, right: left * right,
        ast.Div: lambda left, right: left / right,
        ast.Mod: lambda left, right: left % right,
        ast.Pow: lambda left, right: left ** right,
    }

    ALLOWED_UNARY_OPS = {
        ast.USub: lambda operand: -operand,
        ast.UAdd: lambda operand: operand,
    }

    @classmethod
    def extract_referenced_columns(cls, expr_str: str) -> Set[str]:
        """Extracts column names referenced in the expression."""
        try:
            tree = ast.parse(expr_str, mode="eval")
        except SyntaxError as e:
            raise UnsafeExpressionError(f"Malformed expression syntax: {e}")

        cols: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                cols.add(node.id)
        return cols

    @classmethod
    def compile_expression(cls, expr_str: str, available_columns: List[str]) -> pl.Expr:
        """
        Parses an expression string and compiles it to a Polars pl.Expr.
        Validates referenced variables exist in available_columns.
        """
        if not expr_str or not expr_str.strip():
            raise UnsafeExpressionError("Expression cannot be empty.")

        try:
            tree = ast.parse(expr_str.strip(), mode="eval")
        except SyntaxError as e:
            raise UnsafeExpressionError(f"Syntax error in expression: {e}")

        return cls._eval_node(tree.body, set(available_columns))

    @classmethod
    def _eval_node(cls, node: ast.AST, available_cols: Set[str]) -> pl.Expr:
        # 1. Column Identifier
        if isinstance(node, ast.Name):
            col_name = node.id
            if col_name not in available_cols:
                raise UnsafeExpressionError(
                    f"Referenced column '{col_name}' does not exist in the dataset schema."
                )
            return pl.col(col_name)

        # 2. Numeric Constant
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return pl.lit(node.value)
            raise UnsafeExpressionError(
                f"Only numeric constants are allowed in arithmetic expressions, got: {type(node.value).__name__}"
            )

        # For Python 3.7 compatibility fallback (Num)
        elif hasattr(ast, "Num") and isinstance(node, ast.Num):
            return pl.lit(node.n)

        # 3. Binary Operations (e.g. A + B, A * 2)
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in cls.ALLOWED_BINARY_OPS:
                raise UnsafeExpressionError(
                    f"Operation '{op_type.__name__}' is not permitted in arithmetic expressions."
                )
            left_expr = cls._eval_node(node.left, available_cols)
            right_expr = cls._eval_node(node.right, available_cols)
            return cls.ALLOWED_BINARY_OPS[op_type](left_expr, right_expr)

        # 4. Unary Operations (e.g. -A)
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in cls.ALLOWED_UNARY_OPS:
                raise UnsafeExpressionError(
                    f"Unary operation '{op_type.__name__}' is not permitted."
                )
            operand_expr = cls._eval_node(node.operand, available_cols)
            return cls.ALLOWED_UNARY_OPS[op_type](operand_expr)

        # 5. Strictly Disallowed Syntax
        else:
            raise UnsafeExpressionError(
                f"Disallowed expression syntax: '{type(node).__name__}'. "
                f"Arbitrary code execution, function calls, and attribute access are prohibited."
            )
