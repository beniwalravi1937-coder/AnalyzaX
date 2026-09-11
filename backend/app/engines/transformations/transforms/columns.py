"""
Column Operations Transformers
Drop, rename, and reorder dataset columns.
"""

from typing import Any, Dict, List, Tuple
import polars as pl
from backend.app.engines.transformations.models import TransformationType
from backend.app.engines.transformations.transforms.base import BaseTransformer


class DropColumnsTransformer(BaseTransformer):
    """
    Drops one or more specified columns from the dataset.
    Protects against dropping ALL columns in the dataset.
    """

    transformation_type = TransformationType.DROP_COLUMNS

    def validate(self, schema: Dict[str, pl.DataType], parameters: Dict[str, Any]) -> List[str]:
        errors = []
        columns = parameters.get("columns")

        if not columns or not isinstance(columns, list):
            errors.append("Parameter 'columns' must be a non-empty list of column names to drop.")
        else:
            missing = [c for c in columns if c not in schema]
            if missing:
                errors.append(f"Columns not found in dataset: {missing}")

            if len(columns) >= len(schema):
                errors.append("Cannot drop all columns from the dataset.")

        return errors

    def apply(
        self,
        df: pl.DataFrame,
        parameters: Dict[str, Any],
    ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        columns_to_drop = [c for c in parameters["columns"] if c in df.columns]
        result_df = df.drop(columns_to_drop)

        return result_df, {
            "dropped_columns": columns_to_drop,
            "remaining_columns": len(result_df.columns),
        }


class RenameColumnTransformer(BaseTransformer):
    """
    Renames a single column or multiple columns using a mapping dictionary {old_name: new_name}.
    """

    transformation_type = TransformationType.RENAME_COLUMN

    def validate(self, schema: Dict[str, pl.DataType], parameters: Dict[str, Any]) -> List[str]:
        errors = []
        mapping = parameters.get("mapping")
        # Also support single rename via column + new_name
        column = parameters.get("column")
        new_name = parameters.get("new_name")

        if mapping and isinstance(mapping, dict):
            for old_col, target_col in mapping.items():
                if old_col not in schema:
                    errors.append(f"Column '{old_col}' does not exist in dataset schema.")
                if not str(target_col).strip():
                    errors.append(f"New name for column '{old_col}' cannot be empty.")
        elif column and new_name:
            if column not in schema:
                errors.append(f"Column '{column}' does not exist in dataset schema.")
            if not str(new_name).strip():
                errors.append("Parameter 'new_name' cannot be empty.")
        else:
            errors.append("Must provide either 'mapping' dictionary or 'column' and 'new_name'.")

        return errors

    def apply(
        self,
        df: pl.DataFrame,
        parameters: Dict[str, Any],
    ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        if "mapping" in parameters and isinstance(parameters["mapping"], dict):
            mapping = {str(k): str(v).strip() for k, v in parameters["mapping"].items()}
        else:
            mapping = {str(parameters["column"]): str(parameters["new_name"]).strip()}

        # Filter to existing columns
        valid_mapping = {k: v for k, v in mapping.items() if k in df.columns}
        result_df = df.rename(valid_mapping)

        return result_df, {
            "renamed_columns": valid_mapping,
            "total_renamed": len(valid_mapping),
        }


class ReorderColumnsTransformer(BaseTransformer):
    """
    Reorders dataset columns according to an explicit ordered list.
    Unspecified columns are appended at the end in their original order.
    """

    transformation_type = TransformationType.REORDER_COLUMNS

    def validate(self, schema: Dict[str, pl.DataType], parameters: Dict[str, Any]) -> List[str]:
        errors = []
        columns = parameters.get("columns")

        if not columns or not isinstance(columns, list):
            errors.append("Parameter 'columns' must be an ordered list of column names.")
        else:
            missing = [c for c in columns if c not in schema]
            if missing:
                errors.append(f"Columns not found in dataset: {missing}")

        return errors

    def apply(
        self,
        df: pl.DataFrame,
        parameters: Dict[str, Any],
    ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        requested_order = [c for c in parameters["columns"] if c in df.columns]
        # Append remaining columns not explicitly in requested list
        remaining = [c for c in df.columns if c not in requested_order]
        final_order = requested_order + remaining

        result_df = df.select(final_order)

        return result_df, {
            "columns_order": final_order,
            "total_columns": len(final_order),
        }
