"""
Normalize Categories Transformer
Harmonizes and maps categorical values to canonical representations.
"""

from typing import Any, Dict, List, Tuple
import polars as pl
from backend.app.engines.transformations.models import TransformationType
from backend.app.engines.transformations.transforms.base import BaseTransformer


class NormalizeCategoriesTransformer(BaseTransformer):
    """
    Standardizes categorical values using an explicit mapping dictionary.
    Supports optional case-insensitive matching and fallback values for unmapped entries.
    """

    transformation_type = TransformationType.NORMALIZE_CATEGORIES

    def validate(self, schema: Dict[str, pl.DataType], parameters: Dict[str, Any]) -> List[str]:
        errors = []
        column = parameters.get("column")
        mapping = parameters.get("mapping")

        if not column:
            errors.append("Parameter 'column' is required.")
        elif column not in schema:
            errors.append(f"Column '{column}' does not exist in dataset schema.")

        if not mapping or not isinstance(mapping, dict):
            errors.append("Parameter 'mapping' must be a non-empty dictionary of {original_value: new_value}.")

        return errors

    def apply(
        self,
        df: pl.DataFrame,
        parameters: Dict[str, Any],
    ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        column = parameters["column"]
        mapping = parameters["mapping"]
        case_insensitive = bool(parameters.get("case_insensitive", False))
        fallback = parameters.get("fallback")

        # Ensure column is string-castable or converted to string for mapping
        s = df[column].cast(pl.Utf8)

        if case_insensitive:
            norm_mapping = {str(k).strip().lower(): str(v) for k, v in mapping.items()}
            # Expression with lower
            expr = s.str.to_lowercase().replace_strict(norm_mapping, default=s if fallback is None else pl.lit(fallback))
        else:
            str_mapping = {str(k): str(v) for k, v in mapping.items()}
            expr = s.replace_strict(str_mapping, default=s if fallback is None else pl.lit(fallback))

        # Count how many rows actually changed
        modified_count = (s != expr).sum()

        result_df = df.with_columns(expr.alias(column))

        return result_df, {
            "column": column,
            "modified_rows": int(modified_count) if modified_count is not None else 0,
            "mapping_size": len(mapping),
        }
