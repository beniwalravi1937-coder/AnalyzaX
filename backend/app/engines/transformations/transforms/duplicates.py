"""
Duplicate Removal Transformer
Removes identical duplicate records or key collisions based on full-row or subset criteria.
"""

from typing import Any, Dict, List, Tuple
import polars as pl
from backend.app.engines.transformations.models import TransformationType
from backend.app.engines.transformations.transforms.base import BaseTransformer


class DropDuplicatesTransformer(BaseTransformer):
    transformation_type = TransformationType.DROP_DUPLICATES

    def validate(self, schema: Dict[str, pl.DataType], parameters: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        subset = parameters.get("subset") or parameters.get("columns")
        if not subset and "column" in parameters:
            subset = [parameters["column"]]

        if subset:
            for col in subset:
                if col not in schema:
                    errors.append(f"Subset column '{col}' does not exist in schema.")

        keep = parameters.get("keep", "first").lower()
        if keep not in ("first", "last", "any"):
            errors.append(f"Invalid keep strategy '{keep}'. Must be 'first' or 'last'.")

        return errors

    def apply(
        self,
        df: pl.DataFrame,
        parameters: Dict[str, Any],
    ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        initial_rows = len(df)
        subset = parameters.get("subset") or parameters.get("columns")
        if not subset and "column" in parameters:
            subset = [parameters["column"]]
        keep = parameters.get("keep", "first").lower()

        maintain_order = True
        df = df.unique(subset=subset, keep=keep, maintain_order=maintain_order)

        affected_rows = initial_rows - len(df)
        return df, {
            "rows_affected": affected_rows,
            "keep": keep,
            "subset": subset or "all_columns",
        }
