"""
Scaling & Outlier Transformers
Standardization, normalization, log scaling, and robust outlier clipping/filtering.
"""

from typing import Any, Dict, List, Tuple
import polars as pl
from backend.app.engines.transformations.models import TransformationType
from backend.app.engines.transformations.transforms.base import BaseTransformer

SUPPORTED_SCALING_METHODS = {"min_max", "standard", "z_score", "robust", "log", "log1p", "abs"}
SUPPORTED_OUTLIER_METHODS = {"clip_quantiles", "winsorize", "clip_bounds", "clip_iqr", "clip_zscore", "drop_outliers"}


class ScaleNumericTransformer(BaseTransformer):
    """
    Scales and standardizes continuous numerical columns using mathematical transformations.
    """

    transformation_type = TransformationType.SCALE_NUMERIC

    def validate(self, schema: Dict[str, pl.DataType], parameters: Dict[str, Any]) -> List[str]:
        errors = []
        column = parameters.get("column")
        method = str(parameters.get("method", "")).lower()

        if not column:
            errors.append("Parameter 'column' is required.")
        elif column not in schema:
            errors.append(f"Column '{column}' does not exist in dataset schema.")

        if not method:
            errors.append("Parameter 'method' is required.")
        elif method not in SUPPORTED_SCALING_METHODS:
            errors.append(
                f"Unsupported scaling method '{method}'. Supported: {sorted(SUPPORTED_SCALING_METHODS)}"
            )

        return errors

    def apply(
        self,
        df: pl.DataFrame,
        parameters: Dict[str, Any],
    ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        column = parameters["column"]
        method = str(parameters["method"]).lower()
        col_expr = pl.col(column).cast(pl.Float64)

        if method == "min_max":
            col_min = df[column].min()
            col_max = df[column].max()
            denom = col_max - col_min if col_max != col_min else 1.0
            scaled_expr = (col_expr - col_min) / denom
        elif method in ("standard", "z_score"):
            col_mean = df[column].mean()
            col_std = df[column].std()
            denom = col_std if col_std and col_std > 0 else 1.0
            scaled_expr = (col_expr - col_mean) / denom
        elif method == "robust":
            col_q25 = df[column].quantile(0.25)
            col_q75 = df[column].quantile(0.75)
            col_med = df[column].median()
            iqr = col_q75 - col_q25 if col_q75 != col_q25 else 1.0
            scaled_expr = (col_expr - col_med) / iqr
        elif method in ("log", "log1p"):
            scaled_expr = (col_expr.clip(lower_bound=0.0) + 1.0).log()
        elif method == "abs":
            scaled_expr = col_expr.abs()
        else:
            raise ValueError(f"Unsupported scaling method: {method}")

        result_df = df.with_columns(scaled_expr.alias(column))

        return result_df, {
            "column": column,
            "method": method,
            "total_rows": len(result_df),
        }


class HandleOutliersTransformer(BaseTransformer):
    """
    Clips (winsorizes) or drops extreme values using IQR, Z-Score, or explicit quantiles.
    """

    transformation_type = TransformationType.HANDLE_OUTLIERS

    def validate(self, schema: Dict[str, pl.DataType], parameters: Dict[str, Any]) -> List[str]:
        errors = []
        column = parameters.get("column")
        method = str(parameters.get("method", "clip_iqr")).lower()

        if not column:
            errors.append("Parameter 'column' is required.")
        elif column not in schema:
            errors.append(f"Column '{column}' does not exist in dataset schema.")

        if method not in SUPPORTED_OUTLIER_METHODS:
            errors.append(
                f"Unsupported outlier method '{method}'. Supported: {sorted(SUPPORTED_OUTLIER_METHODS)}"
            )

        return errors

    def apply(
        self,
        df: pl.DataFrame,
        parameters: Dict[str, Any],
    ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        column = parameters["column"]
        method = str(parameters.get("method", "clip_iqr")).lower()

        s = df[column].cast(pl.Float64)
        lower_bound = None
        upper_bound = None

        if method in ("clip_quantiles", "winsorize"):
            lower_q = float(parameters.get("lower_quantile", 0.01))
            upper_q = float(parameters.get("upper_quantile", 0.99))
            lower_bound = float(s.quantile(lower_q))
            upper_bound = float(s.quantile(upper_q))
        elif method == "clip_bounds":
            lower_bound = float(parameters["lower_bound"]) if "lower_bound" in parameters else None
            upper_bound = float(parameters["upper_bound"]) if "upper_bound" in parameters else None
        elif method == "clip_iqr":
            q25 = float(s.quantile(0.25))
            q75 = float(s.quantile(0.75))
            multiplier = float(parameters.get("iqr_multiplier", 1.5))
            iqr = q75 - q25
            lower_bound = q25 - (multiplier * iqr)
            upper_bound = q75 + (multiplier * iqr)
        elif method == "clip_zscore":
            mean_val = float(s.mean())
            std_val = float(s.std())
            threshold = float(parameters.get("z_threshold", 3.0))
            lower_bound = mean_val - (threshold * std_val)
            upper_bound = mean_val + (threshold * std_val)
        elif method == "drop_outliers":
            q25 = float(s.quantile(0.25))
            q75 = float(s.quantile(0.75))
            multiplier = float(parameters.get("iqr_multiplier", 1.5))
            iqr = q75 - q25
            lower_bound = q25 - (multiplier * iqr)
            upper_bound = q75 + (multiplier * iqr)

            rows_before = len(df)
            cond = (pl.col(column) >= lower_bound) & (pl.col(column) <= upper_bound)
            result_df = df.filter(cond)
            rows_after = len(result_df)

            return result_df, {
                "column": column,
                "method": method,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "rows_dropped": rows_before - rows_after,
            }

        # Otherwise perform clipping
        col_expr = pl.col(column).cast(pl.Float64)
        if lower_bound is not None and upper_bound is not None:
            clipped_expr = col_expr.clip(lower_bound=lower_bound, upper_bound=upper_bound)
        elif lower_bound is not None:
            clipped_expr = col_expr.clip(lower_bound=lower_bound)
        elif upper_bound is not None:
            clipped_expr = col_expr.clip(upper_bound=upper_bound)
        else:
            clipped_expr = col_expr

        # Calculate affected count
        affected = 0
        if lower_bound is not None:
            affected += int((s < lower_bound).sum() or 0)
        if upper_bound is not None:
            affected += int((s > upper_bound).sum() or 0)

        result_df = df.with_columns(clipped_expr.alias(column))

        return result_df, {
            "column": column,
            "method": method,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "values_clipped": affected,
        }
