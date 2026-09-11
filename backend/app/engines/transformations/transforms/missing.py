"""
Missing Value Transformers
Handles statistical imputation (mean, median, mode), constant filling, and row/column dropping.
"""

from typing import Any, Dict, List, Tuple
import polars as pl
from backend.app.engines.transformations.models import TransformationType
from backend.app.engines.transformations.transforms.base import BaseTransformer


class FillMissingTransformer(BaseTransformer):
    transformation_type = TransformationType.FILL_MISSING

    def validate(self, schema: Dict[str, pl.DataType], parameters: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        col = parameters.get("column")
        if not col or col not in schema:
            errors.append(f"Target column '{col}' does not exist in dataset schema.")
            return errors

        strategy = parameters.get("strategy", "").lower()
        valid_strategies = ("mean", "median", "mode", "constant", "zero", "unknown", "forward_fill", "backward_fill")
        if strategy not in valid_strategies:
            errors.append(f"Invalid strategy '{strategy}'. Must be one of: {', '.join(valid_strategies)}.")

        col_dtype = schema[col]
        is_numeric = col_dtype in (pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64, pl.Float32, pl.Float64)

        if strategy in ("mean", "median") and not is_numeric:
            errors.append(f"Strategy '{strategy}' can only be applied to numeric columns (column '{col}' is {col_dtype}).")

        if strategy == "constant" and "constant_value" not in parameters:
            errors.append("Strategy 'constant' requires 'constant_value' parameter.")

        return errors

    def apply(
        self,
        df: pl.DataFrame,
        parameters: Dict[str, Any],
    ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        col = parameters["column"]
        strategy = parameters["strategy"].lower()
        null_count = df[col].null_count()

        if null_count == 0 or len(df) == 0:
            return df, {"rows_affected": 0, "imputed_value": None}

        col_series = df[col]
        replacement: Any = None

        if strategy == "mean":
            replacement = col_series.mean()
            df = df.with_columns(pl.col(col).fill_null(replacement))
        elif strategy == "median":
            replacement = col_series.median()
            df = df.with_columns(pl.col(col).fill_null(replacement))
        elif strategy == "mode":
            mode_s = col_series.mode()
            replacement = mode_s[0] if len(mode_s) > 0 else None
            if replacement is not None:
                df = df.with_columns(pl.col(col).fill_null(replacement))
        elif strategy == "zero":
            replacement = 0
            df = df.with_columns(pl.col(col).fill_null(replacement))
        elif strategy == "unknown":
            replacement = "Unknown"
            df = df.with_columns(pl.col(col).cast(pl.Utf8).fill_null(replacement))
        elif strategy == "constant":
            replacement = parameters.get("constant_value") if "constant_value" in parameters else parameters.get("value")
            # Cast constant to column dtype if possible
            df = df.with_columns(pl.col(col).fill_null(pl.lit(replacement)))
        elif strategy == "forward_fill":
            df = df.with_columns(pl.col(col).forward_fill())
        elif strategy == "backward_fill":
            df = df.with_columns(pl.col(col).backward_fill())

        return df, {
            "rows_affected": null_count,
            "column": col,
            "strategy": strategy,
            "imputed_value": str(replacement) if replacement is not None else None,
        }


class DropMissingTransformer(BaseTransformer):
    transformation_type = TransformationType.DROP_MISSING

    def validate(self, schema: Dict[str, pl.DataType], parameters: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        strategy = parameters.get("strategy", "drop_rows").lower()
        cols = parameters.get("columns", [])

        if strategy not in ("drop_rows", "drop_column", "drop_columns"):
            errors.append(f"Invalid strategy '{strategy}'. Must be 'drop_rows' or 'drop_columns'.")

        if cols and cols != "all":
            for c in cols:
                if c not in schema:
                    errors.append(f"Specified column '{c}' does not exist in schema.")

        return errors

    def apply(
        self,
        df: pl.DataFrame,
        parameters: Dict[str, Any],
    ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        strategy = parameters.get("strategy", "drop_rows").lower()
        cols = parameters.get("columns", [])
        initial_rows = len(df)
        initial_cols = len(df.columns)

        if strategy == "drop_rows":
            if not cols or cols == "all":
                df = df.drop_nulls()
            else:
                df = df.drop_nulls(subset=cols)
            affected_rows = initial_rows - len(df)
            return df, {"rows_affected": affected_rows, "columns_affected": 0}

        else:  # drop_columns
            cols_to_drop = [c for c in cols if c in df.columns] if cols != "all" else []
            if cols == "all":
                # Drop columns that are 100% null
                cols_to_drop = [c for c in df.columns if df[c].null_count() == len(df)]

            df = df.drop(cols_to_drop)
            return df, {
                "rows_affected": 0,
                "columns_affected": len(cols_to_drop),
                "dropped_columns": cols_to_drop,
            }
