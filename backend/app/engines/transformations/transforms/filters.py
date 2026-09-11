"""
Filter Rows Transformer
Applies structured declarative filter criteria without SQL strings or eval().
"""

from typing import Any, Dict, List, Tuple
import polars as pl
from backend.app.engines.transformations.models import TransformationType
from backend.app.engines.transformations.transforms.base import BaseTransformer

SUPPORTED_OPERATORS = {
    "==", "eq", "=",
    "!=", "neq", "<>",
    ">", "gt",
    ">=", "gte",
    "<", "lt",
    "<=", "lte",
    "in", "not_in",
    "is_null", "is_not_null",
    "contains", "starts_with", "ends_with"
}


class FilterRowsTransformer(BaseTransformer):
    """
    Filters rows based on structured predicate conditions: column, operator, and value.
    Rejects raw SQL text or arbitrary lambdas, ensuring complete safety.
    """

    transformation_type = TransformationType.FILTER_ROWS

    def validate(self, schema: Dict[str, pl.DataType], parameters: Dict[str, Any]) -> List[str]:
        errors = []
        column = parameters.get("column")
        operator = str(parameters.get("operator", "")).lower()

        if not column:
            errors.append("Parameter 'column' is required.")
        elif column not in schema:
            errors.append(f"Column '{column}' does not exist in dataset schema.")

        if not operator:
            errors.append("Parameter 'operator' is required.")
        elif operator not in SUPPORTED_OPERATORS:
            errors.append(f"Unsupported operator '{operator}'. Supported: {sorted(SUPPORTED_OPERATORS)}")

        if operator in ("in", "not_in"):
            values = parameters.get("value")
            if not isinstance(values, list):
                errors.append(f"Operator '{operator}' requires 'value' to be a list.")

        return errors

    def apply(
        self,
        df: pl.DataFrame,
        parameters: Dict[str, Any],
    ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        column = parameters["column"]
        op = str(parameters["operator"]).lower()
        val = parameters.get("value")

        c = pl.col(column)
        condition = None

        if op in ("==", "eq", "="):
            condition = (c == val)
        elif op in ("!=", "neq", "<>"):
            condition = (c != val)
        elif op in (">", "gt"):
            condition = (c > val)
        elif op in (">=", "gte"):
            condition = (c >= val)
        elif op in ("<", "lt"):
            condition = (c < val)
        elif op in ("<=", "lte"):
            condition = (c <= val)
        elif op == "in":
            condition = c.is_in(val)
        elif op == "not_in":
            condition = ~c.is_in(val)
        elif op == "is_null":
            condition = c.is_null()
        elif op == "is_not_null":
            condition = c.is_not_null()
        elif op == "contains":
            condition = c.cast(pl.Utf8).str.contains(str(val), literal=True)
        elif op == "starts_with":
            condition = c.cast(pl.Utf8).str.starts_with(str(val))
        elif op == "ends_with":
            condition = c.cast(pl.Utf8).str.ends_with(str(val))
        else:
            raise ValueError(f"Unsupported operator: {op}")

        rows_before = len(df)
        filtered_df = df.filter(condition)
        rows_after = len(filtered_df)
        rows_removed = rows_before - rows_after

        return filtered_df, {
            "column": column,
            "operator": op,
            "rows_before": rows_before,
            "rows_after": rows_after,
            "rows_removed": rows_removed,
        }
