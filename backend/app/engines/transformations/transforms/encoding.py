"""
Categorical Encoding Transformers
One-hot dummy encoding and deterministic integer label encoding.
"""

from typing import Any, Dict, List, Tuple
import polars as pl
from backend.app.core.config import settings
from backend.app.engines.transformations.models import TransformationType
from backend.app.engines.transformations.transforms.base import BaseTransformer


class OneHotEncodeTransformer(BaseTransformer):
    """
    Creates binary dummy columns for each category in a categorical column.
    Guarded by cardinality limit (<= 50) to prevent combinatorial explosion.
    """

    transformation_type = TransformationType.ONE_HOT_ENCODE

    def validate(self, schema: Dict[str, pl.DataType], parameters: Dict[str, Any]) -> List[str]:
        errors = []
        column = parameters.get("column")

        if not column:
            errors.append("Parameter 'column' is required.")
        elif column not in schema:
            errors.append(f"Column '{column}' does not exist in dataset schema.")

        return errors

    def apply(
        self,
        df: pl.DataFrame,
        parameters: Dict[str, Any],
    ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        column = parameters["column"]
        drop_original = bool(parameters.get("drop_original", False))
        max_cardinality = int(parameters.get("max_cardinality", settings.MAX_ONE_HOT_CARDINALITY))

        # Determine unique non-null categories
        unique_values = (
            df[column]
            .drop_nulls()
            .unique()
            .sort()
            .to_list()
        )

        if len(unique_values) > max_cardinality:
            raise ValueError(
                f"Column '{column}' has {len(unique_values)} unique categories, "
                f"exceeding max allowable cardinality ({max_cardinality})."
            )

        new_exprs = []
        created_columns = []

        for val in unique_values:
            sanitized_val = str(val).strip().replace(" ", "_").replace("-", "_").lower()
            dummy_col_name = f"{column}_{sanitized_val}"
            created_columns.append(dummy_col_name)
            new_exprs.append(
                (pl.col(column) == val).cast(pl.Int8).alias(dummy_col_name)
            )

        result_df = df.with_columns(new_exprs)
        if drop_original:
            result_df = result_df.drop(column)

        return result_df, {
            "source_column": column,
            "created_columns": created_columns,
            "num_dummies": len(created_columns),
            "dropped_original": drop_original,
        }


class LabelEncodeTransformer(BaseTransformer):
    """
    Assigns sequential integer labels [0, N-1] to unique categorical values in sorted order.
    Null values can remain null or be assigned a special code (-1).
    """

    transformation_type = TransformationType.LABEL_ENCODE

    def validate(self, schema: Dict[str, pl.DataType], parameters: Dict[str, Any]) -> List[str]:
        errors = []
        column = parameters.get("column")

        if not column:
            errors.append("Parameter 'column' is required.")
        elif column not in schema:
            errors.append(f"Column '{column}' does not exist in dataset schema.")

        return errors

    def apply(
        self,
        df: pl.DataFrame,
        parameters: Dict[str, Any],
    ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        column = parameters["column"]
        null_value = parameters.get("null_value", None)  # None or -1

        unique_vals = (
            df[column]
            .drop_nulls()
            .unique()
            .sort()
            .to_list()
        )

        mapping = {val: idx for idx, val in enumerate(unique_vals)}

        # Build when-then expression for mapping
        expr = pl.col(column).replace_strict(
            mapping,
            default=null_value,
            return_dtype=pl.Int64
        )

        result_df = df.with_columns(expr.alias(column))

        return result_df, {
            "column": column,
            "categories_encoded": len(unique_vals),
            "mapping": {str(k): v for k, v in list(mapping.items())[:50]},  # cap dict in metrics
        }
