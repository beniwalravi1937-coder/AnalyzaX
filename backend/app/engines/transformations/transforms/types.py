"""
Cast Type Transformer
Converts column physical and semantic types with safe error handling and configurable strategies.
"""

from typing import Any, Dict, List, Tuple
import polars as pl
from backend.app.engines.transformations.models import TransformationType
from backend.app.engines.transformations.transforms.base import BaseTransformer

TYPE_MAP = {
    "int": pl.Int64,
    "integer": pl.Int64,
    "int64": pl.Int64,
    "int32": pl.Int32,
    "float": pl.Float64,
    "float64": pl.Float64,
    "float32": pl.Float32,
    "double": pl.Float64,
    "bool": pl.Boolean,
    "boolean": pl.Boolean,
    "str": pl.Utf8,
    "string": pl.Utf8,
    "text": pl.Utf8,
    "date": pl.Date,
    "datetime": pl.Datetime,
}

SUPPORTED_STRATEGIES = {"set_null", "keep_original", "fail_transformation"}


class CastTypeTransformer(BaseTransformer):
    """
    Casts a column to a target Polars data type.
    Supports configurable error strategies:
      - 'set_null': unparseable values become null (default)
      - 'keep_original': preserves original column and types if any conversion failures occur
      - 'fail_transformation': raises an error if any values cannot be cleanly cast
    """

    transformation_type = TransformationType.CAST_TYPE

    def validate(self, schema: Dict[str, pl.DataType], parameters: Dict[str, Any]) -> List[str]:
        errors = []
        column = parameters.get("column")
        target_type = str(parameters.get("target_type", "")).lower()
        strategy = str(parameters.get("strategy", "set_null")).lower()

        if not column:
            errors.append("Parameter 'column' is required.")
        elif column not in schema:
            errors.append(f"Column '{column}' does not exist in dataset schema.")

        if not target_type:
            errors.append("Parameter 'target_type' is required.")
        elif target_type not in TYPE_MAP:
            errors.append(
                f"Unsupported target type '{target_type}'. Supported: {', '.join(sorted(TYPE_MAP.keys()))}"
            )

        if strategy not in SUPPORTED_STRATEGIES:
            errors.append(
                f"Unsupported strategy '{strategy}'. Supported: {', '.join(sorted(SUPPORTED_STRATEGIES))}"
            )

        return errors

    def apply(
        self,
        df: pl.DataFrame,
        parameters: Dict[str, Any],
    ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        column = parameters["column"]
        target_type_str = str(parameters["target_type"]).lower()
        strategy = str(parameters.get("strategy", "set_null")).lower()
        pl_target_type = TYPE_MAP[target_type_str]

        original_series = df[column]
        null_count_before = original_series.null_count()

        # Handle date/datetime casting specifically if currently string
        if pl_target_type in (pl.Date, pl.Datetime) and original_series.dtype == pl.Utf8:
            date_format = parameters.get("date_format")
            if pl_target_type == pl.Date:
                new_series = original_series.str.to_date(format=date_format, strict=False)
            else:
                new_series = original_series.str.to_datetime(format=date_format, strict=False)
        elif pl_target_type == pl.Boolean and original_series.dtype == pl.Utf8:
            lower_s = original_series.str.to_lowercase().str.strip_chars()
            new_series = (
                pl.when(lower_s.is_in(["true", "1", "yes", "y", "t"]))
                .then(True)
                .when(lower_s.is_in(["false", "0", "no", "n", "f"]))
                .then(False)
                .otherwise(None)
            )
        else:
            new_series = original_series.cast(pl_target_type, strict=False)

        null_count_after = new_series.null_count()
        new_nulls = max(0, null_count_after - null_count_before)

        if new_nulls > 0:
            if strategy == "fail_transformation":
                raise ValueError(
                    f"Type conversion to '{target_type_str}' failed for {new_nulls} rows in column '{column}'."
                )
            elif strategy == "keep_original":
                # Do not mutate column
                return df, {
                    "column": column,
                    "target_type": str(original_series.dtype),
                    "polars_type": str(original_series.dtype),
                    "strategy": strategy,
                    "conversion_failed": True,
                    "failed_rows": int(new_nulls),
                    "total_rows": len(df),
                }

        # strategy == 'set_null'
        result_df = df.with_columns(new_series.alias(column))

        return result_df, {
            "column": column,
            "target_type": target_type_str,
            "polars_type": str(pl_target_type),
            "strategy": strategy,
            "new_nulls_introduced": int(new_nulls),
            "total_rows": len(df),
        }
