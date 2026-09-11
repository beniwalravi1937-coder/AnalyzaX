"""
Date & Time Transformers
Specialized transformers for temporal parsing and feature extraction.
"""

from typing import Any, Dict, List, Tuple
import polars as pl
from backend.app.engines.transformations.models import TransformationType
from backend.app.engines.transformations.transforms.base import BaseTransformer


class ParseDateTransformer(BaseTransformer):
    """
    Parses a string column into a Date or Datetime column with optional explicit format.
    """

    transformation_type = TransformationType.PARSE_DATE

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
        date_format = parameters.get("format")
        as_datetime = bool(parameters.get("as_datetime", False))

        series = df[column].cast(pl.Utf8)
        null_count_before = series.null_count()

        if as_datetime:
            parsed = series.str.to_datetime(format=date_format, strict=False)
        else:
            parsed = series.str.to_date(format=date_format, strict=False)

        null_count_after = parsed.null_count()
        failed_parses = max(0, null_count_after - null_count_before)

        result_df = df.with_columns(parsed.alias(column))

        return result_df, {
            "column": column,
            "failed_parses": int(failed_parses),
            "target_type": "datetime" if as_datetime else "date",
            "format_used": date_format or "inferred_iso",
        }


class ExtractDatePartsTransformer(BaseTransformer):
    """
    Extracts calendar components from a date or datetime column:
    year, month, day, day_of_week, hour, quarter, is_weekend.
    """

    transformation_type = TransformationType.EXTRACT_DATE_PARTS

    SUPPORTED_PARTS = {"year", "month", "day", "day_of_week", "hour", "quarter", "is_weekend"}

    def validate(self, schema: Dict[str, pl.DataType], parameters: Dict[str, Any]) -> List[str]:
        errors = []
        column = parameters.get("column")
        parts = parameters.get("parts")

        if not column:
            errors.append("Parameter 'column' is required.")
        elif column not in schema:
            errors.append(f"Column '{column}' does not exist in dataset schema.")

        if not parts or not isinstance(parts, list):
            errors.append("Parameter 'parts' must be a non-empty list of date parts to extract.")
        else:
            invalid_parts = [p for p in parts if str(p).lower() not in self.SUPPORTED_PARTS]
            if invalid_parts:
                errors.append(
                    f"Unsupported date parts: {invalid_parts}. Supported: {sorted(self.SUPPORTED_PARTS)}"
                )

        return errors

    def apply(
        self,
        df: pl.DataFrame,
        parameters: Dict[str, Any],
    ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        column = parameters["column"]
        parts = [str(p).lower() for p in parameters["parts"]]

        col_expr = pl.col(column)
        # If string, attempt quick parse first
        if df[column].dtype == pl.Utf8:
            col_expr = col_expr.str.to_datetime(strict=False)

        new_exprs = []
        created_columns = []

        for part in parts:
            new_col_name = f"{column}_{part}"
            created_columns.append(new_col_name)

            if part == "year":
                new_exprs.append(col_expr.dt.year().alias(new_col_name))
            elif part == "month":
                new_exprs.append(col_expr.dt.month().alias(new_col_name))
            elif part == "day":
                new_exprs.append(col_expr.dt.day().alias(new_col_name))
            elif part == "day_of_week":
                new_exprs.append(col_expr.dt.weekday().alias(new_col_name))
            elif part == "hour":
                new_exprs.append(col_expr.dt.hour().alias(new_col_name))
            elif part == "quarter":
                new_exprs.append(col_expr.dt.quarter().alias(new_col_name))
            elif part == "is_weekend":
                # weekday: Monday=1, Sunday=7 in Polars
                new_exprs.append((col_expr.dt.weekday() >= 6).alias(new_col_name))

        result_df = df.with_columns(new_exprs)

        return result_df, {
            "source_column": column,
            "created_columns": created_columns,
            "parts_extracted": parts,
        }
