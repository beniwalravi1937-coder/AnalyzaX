"""
AnalyzaX — Phase 7: Automated EDA Planner
Determines prioritized analytical scope based on column profiles, cardinality,
semantic roles, and computational budgets to prevent combinatorial explosion.
"""

from typing import List, Optional
import polars as pl

from backend.app.engines.eda.models import EDAPlan
from backend.app.schemas.profile import DatasetProfileResponse


class EDAPlanner:
    """
    Intelligent planner that inspects schema metadata and selects bounded analyses.
    """

    MAX_NUMERIC_COLS = 30
    MAX_CATEGORICAL_COLS = 20
    MAX_DATETIME_COLS = 5
    MAX_NUMERIC_PAIRS = 15
    MAX_NUM_CAT_PAIRS = 10
    SCATTER_SAMPLE_SIZE = 1000

    @classmethod
    def create_plan(
        cls,
        df: pl.DataFrame,
        dataset_id: str = "",
        version_id: str = "v1",
        profile: Optional[DatasetProfileResponse] = None,
    ) -> EDAPlan:
        columns = df.columns
        schema = df.schema

        numeric_cols: List[str] = []
        categorical_cols: List[str] = []
        datetime_cols: List[str] = []

        # Classify columns by Polars dtype
        for col in columns:
            dtype = schema[col]
            if dtype.is_numeric():
                numeric_cols.append(col)
            elif dtype.is_temporal():
                datetime_cols.append(col)
            elif dtype == pl.Utf8 or dtype == pl.Categorical or dtype == pl.Boolean:
                categorical_cols.append(col)

        # Check if string columns are dates/datetimes
        unresolved_categorical = list(categorical_cols)
        for col in unresolved_categorical:
            name_lower = col.lower()
            is_date_name = (
                name_lower.endswith("_date")
                or name_lower.endswith("_time")
                or name_lower.endswith("_at")
                or "timestamp" in name_lower
                or name_lower in ["date", "datetime", "time"]
            )
            if is_date_name:
                try:
                    s_clean = df[col].drop_nulls().head(10)
                    if len(s_clean) > 0:
                        parsed = s_clean.str.to_datetime(strict=False)
                        if parsed.null_count() == len(s_clean):
                            parsed = s_clean.str.to_date(strict=False)
                        if parsed.null_count() == 0:
                            datetime_cols.append(col)
                            categorical_cols.remove(col)
                except Exception:
                    pass

        # Apply profile semantic overrides if available
        if profile and hasattr(profile, "columns") and profile.columns:
            for c_prof in profile.columns:
                name = c_prof.name
                if name not in columns:
                    continue
                # If marked as datetime semantic but stored as string, include in datetime
                if c_prof.semantic_type in ["datetime", "date"] and name not in datetime_cols:
                    datetime_cols.append(name)
                    if name in categorical_cols:
                        categorical_cols.remove(name)

        # Apply budget limits
        selected_numeric = numeric_cols[: cls.MAX_NUMERIC_COLS]
        selected_categorical = categorical_cols[: cls.MAX_CATEGORICAL_COLS]
        selected_datetime = datetime_cols[: cls.MAX_DATETIME_COLS]

        # Prioritize numeric pairs (for correlation & scatter)
        numeric_pairs: List[List[str]] = []
        for i in range(len(selected_numeric)):
            for j in range(i + 1, len(selected_numeric)):
                numeric_pairs.append([selected_numeric[i], selected_numeric[j]])
                if len(numeric_pairs) >= cls.MAX_NUMERIC_PAIRS:
                    break
            if len(numeric_pairs) >= cls.MAX_NUMERIC_PAIRS:
                break

        # Prioritize numeric-categorical pairs (for group comparisons)
        num_cat_pairs: List[List[str]] = []
        for num_c in selected_numeric:
            for cat_c in selected_categorical:
                num_cat_pairs.append([num_c, cat_c])
                if len(num_cat_pairs) >= cls.MAX_NUM_CAT_PAIRS:
                    break
            if len(num_cat_pairs) >= cls.MAX_NUM_CAT_PAIRS:
                break

        return EDAPlan(
            dataset_id=dataset_id,
            version_id=version_id,
            selected_numeric_columns=selected_numeric,
            selected_categorical_columns=selected_categorical,
            selected_datetime_columns=selected_datetime,
            selected_numeric_pairs=numeric_pairs,
            selected_num_cat_pairs=num_cat_pairs,
            run_correlation=len(selected_numeric) >= 2,
            run_missingness=True,
            run_outliers=len(selected_numeric) > 0,
            max_scatter_points=cls.SCATTER_SAMPLE_SIZE,
        )
