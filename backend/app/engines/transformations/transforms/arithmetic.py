"""
Derived Column & Arithmetic Transformer
Calculates derived features and columns using verified AST mathematical expressions.
"""

from typing import Any, Dict, List, Tuple
import polars as pl
from backend.app.engines.transformations.models import TransformationType
from backend.app.engines.transformations.transforms.base import BaseTransformer
from backend.app.engines.transformations.expression_parser import (
    SafeExpressionParser,
    UnsafeExpressionError,
)


class DerivedColumnTransformer(BaseTransformer):
    """
    Computes a new calculated column from existing numeric columns via safe arithmetic formulas.
    Strictly uses AST allowlisting to prevent arbitrary code execution or injection.
    """

    transformation_type = TransformationType.DERIVED_COLUMN

    def validate(self, schema: Dict[str, pl.DataType], parameters: Dict[str, Any]) -> List[str]:
        errors = []
        new_column = parameters.get("new_column")
        expression = parameters.get("expression")

        if not new_column or not str(new_column).strip():
            errors.append("Parameter 'new_column' is required and cannot be empty.")

        if not expression or not str(expression).strip():
            errors.append("Parameter 'expression' is required.")
        else:
            try:
                ref_cols = SafeExpressionParser.extract_referenced_columns(expression)
                missing = [c for c in ref_cols if c not in schema]
                if missing:
                    errors.append(f"Referenced columns not in dataset schema: {missing}")

                # Also compile to verify AST structure
                SafeExpressionParser.compile_expression(expression, list(schema.keys()))
            except UnsafeExpressionError as e:
                errors.append(f"Invalid arithmetic expression: {str(e)}")

        return errors

    def apply(
        self,
        df: pl.DataFrame,
        parameters: Dict[str, Any],
    ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        new_column = str(parameters["new_column"]).strip()
        expression = str(parameters["expression"]).strip()

        compiled_expr = SafeExpressionParser.compile_expression(expression, df.columns)
        result_df = df.with_columns(compiled_expr.alias(new_column))

        return result_df, {
            "new_column": new_column,
            "expression": expression,
            "total_rows": len(result_df),
        }
