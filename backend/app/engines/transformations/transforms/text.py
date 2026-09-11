"""
Text & String Normalization Transformers
Handles whitespace trimming, casing conversions (lower/upper/title), and substring replacements.
"""

from typing import Any, Dict, List, Tuple
import polars as pl
from backend.app.engines.transformations.models import TransformationType
from backend.app.engines.transformations.transforms.base import BaseTransformer


def _extract_columns(parameters: Dict[str, Any]) -> List[str]:
    cols = parameters.get("columns")
    if not cols and "column" in parameters:
        cols = [parameters["column"]]
    return cols or []


class TrimWhitespaceTransformer(BaseTransformer):
    transformation_type = TransformationType.TRIM_WHITESPACE

    def validate(self, schema: Dict[str, pl.DataType], parameters: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        cols = _extract_columns(parameters)
        if not cols:
            errors.append("Parameter 'columns' or 'column' is required.")
            return errors

        for col in cols:
            if col not in schema:
                errors.append(f"Column '{col}' does not exist in schema.")
            elif schema[col] not in (pl.Utf8, pl.String, pl.Categorical):
                errors.append(f"Column '{col}' is not a string type (got {schema[col]}).")

        mode = parameters.get("mode", "both").lower()
        if mode not in ("both", "leading", "trailing"):
            errors.append(f"Invalid mode '{mode}'. Must be 'both', 'leading', or 'trailing'.")

        return errors

    def apply(
        self,
        df: pl.DataFrame,
        parameters: Dict[str, Any],
    ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        cols = _extract_columns(parameters)
        mode = parameters.get("mode", "both").lower()

        exprs = []
        for col in cols:
            if mode == "leading":
                exprs.append(pl.col(col).str.strip_chars_start().alias(col))
            elif mode == "trailing":
                exprs.append(pl.col(col).str.strip_chars_end().alias(col))
            else:
                exprs.append(pl.col(col).str.strip_chars().alias(col))

        df = df.with_columns(exprs)
        return df, {
            "columns_affected": len(cols),
            "mode": mode,
            "columns": cols,
        }


class TextCaseTransformer(BaseTransformer):
    transformation_type = TransformationType.TEXT_CASE

    def validate(self, schema: Dict[str, pl.DataType], parameters: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        cols = _extract_columns(parameters)
        if not cols:
            errors.append("Parameter 'columns' or 'column' is required.")

        case = parameters.get("case", "lower").lower()
        if case not in ("lower", "upper", "title"):
            errors.append(f"Invalid case '{case}'. Must be 'lower', 'upper', or 'title'.")

        for col in cols:
            if col not in schema:
                errors.append(f"Column '{col}' does not exist in schema.")

        return errors

    def apply(
        self,
        df: pl.DataFrame,
        parameters: Dict[str, Any],
    ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        cols = _extract_columns(parameters)
        case = parameters.get("case", "lower").lower()

        exprs = []
        for col in cols:
            if case == "lower":
                exprs.append(pl.col(col).str.to_lowercase().alias(col))
            elif case == "upper":
                exprs.append(pl.col(col).str.to_uppercase().alias(col))
            elif case == "title":
                exprs.append(pl.col(col).str.to_titlecase().alias(col))

        df = df.with_columns(exprs)
        return df, {
            "columns_affected": len(cols),
            "case": case,
            "columns": cols,
        }


class ReplaceTextTransformer(BaseTransformer):
    transformation_type = TransformationType.REPLACE_TEXT

    def validate(self, schema: Dict[str, pl.DataType], parameters: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        cols = _extract_columns(parameters)
        if not cols:
            errors.append("Parameter 'columns' or 'column' is required.")

        if "find" not in parameters or "replace" not in parameters:
            errors.append("Parameters 'find' and 'replace' are required.")

        for col in cols:
            if col not in schema:
                errors.append(f"Column '{col}' does not exist in schema.")

        return errors

    def apply(
        self,
        df: pl.DataFrame,
        parameters: Dict[str, Any],
    ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        cols = _extract_columns(parameters)
        find_val = parameters["find"]
        replace_val = parameters["replace"]
        is_regex = parameters.get("is_regex", False)

        exprs = []
        for col in cols:
            if is_regex:
                exprs.append(pl.col(col).str.replace_all(find_val, replace_val).alias(col))
            else:
                exprs.append(pl.col(col).str.replace_all(pl.lit(find_val), pl.lit(replace_val), literal=True).alias(col))

        df = df.with_columns(exprs)
        return df, {
            "columns_affected": len(cols),
            "find": find_val,
            "replace": replace_val,
        }
