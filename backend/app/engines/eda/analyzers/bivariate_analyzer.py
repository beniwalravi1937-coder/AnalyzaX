"""
AnalyzaX — Phase 7: Bivariate Analyzer
Computes relationships between pairs of variables:
- Numeric vs Numeric (Correlation, Linear Regression, Bounded Scatter Samples)
- Numeric vs Categorical (Group Aggregations, Category Boxplot Stats)
- Categorical vs Categorical (Contingency Tables, Cramér's V)
"""

import math
from typing import List, Optional
import numpy as np
import polars as pl
from scipy import stats

from backend.app.engines.eda.models import (
    CategoricalCategoricalRelationship,
    CategoryGroupStats,
    ChartSamplingMetadata,
    NumericCategoricalRelationship,
    NumericNumericRelationship,
    RegressionLine,
    ScatterPoint,
)
from backend.app.engines.eda.statistics import (
    calculate_cramers_v,
    calculate_linear_regression,
)


class BivariateAnalyzer:
    @staticmethod
    def analyze_numeric_numeric(
        df: pl.DataFrame,
        col_x: str,
        col_y: str,
        max_sample_points: int = 1000,
    ) -> Optional[NumericNumericRelationship]:
        if col_x not in df.columns or col_y not in df.columns:
            return None

        # Filter nulls from both columns
        pair_df = df.select([
            pl.col(col_x).cast(pl.Float64),
            pl.col(col_y).cast(pl.Float64),
        ]).drop_nulls()

        total_points = len(pair_df)
        if total_points < 3:
            return None

        arr_x = pair_df[col_x].to_numpy()
        arr_y = pair_df[col_y].to_numpy()

        # Check for non-zero variance
        if np.std(arr_x) == 0.0 or np.std(arr_y) == 0.0:
            return None

        # Correlation
        try:
            r_res = stats.pearsonr(arr_x, arr_y)
            corr_val = float(r_res.statistic)
            corr = 0.0 if (math.isnan(corr_val) or math.isinf(corr_val)) else round(corr_val, 4)
        except Exception:
            corr = 0.0

        # Regression line
        reg_dict = calculate_linear_regression(arr_x, arr_y)
        regression = (
            RegressionLine(
                slope=reg_dict["slope"],
                intercept=reg_dict["intercept"],
                r_squared=reg_dict["r_squared"],
            )
            if reg_dict
            else None
        )

        # Sampling points
        is_sampled = total_points > max_sample_points
        if is_sampled:
            sampled_df = pair_df.sample(n=max_sample_points, seed=42)
            pts_x = sampled_df[col_x].to_numpy()
            pts_y = sampled_df[col_y].to_numpy()
            sample_size = max_sample_points
        else:
            pts_x = arr_x
            pts_y = arr_y
            sample_size = total_points

        sample_points = [
            ScatterPoint(x=round(float(pts_x[i]), 4), y=round(float(pts_y[i]), 4))
            for i in range(len(pts_x))
        ]

        sampling = ChartSamplingMetadata(
            is_sampled=is_sampled,
            displayed_points=sample_size,
            original_row_count=total_points,
            sampling_method="uniform_random" if is_sampled else "deterministic",
        )

        return NumericNumericRelationship(
            column_x=col_x,
            column_y=col_y,
            correlation=corr,
            regression=regression,
            sample_points=sample_points,
            sampling=sampling,
        )

    @staticmethod
    def analyze_numeric_categorical(
        df: pl.DataFrame,
        num_col: str,
        cat_col: str,
        max_categories: int = 15,
    ) -> Optional[NumericCategoricalRelationship]:
        if num_col not in df.columns or cat_col not in df.columns:
            return None

        clean_df = df.select([
            pl.col(num_col).cast(pl.Float64),
            pl.col(cat_col).cast(pl.Utf8),
        ]).drop_nulls()

        if len(clean_df) < 3:
            return None

        # Find top categories by count
        top_cats = (
            clean_df.group_by(cat_col)
            .len()
            .sort("len", descending=True)
            .head(max_categories)
        )
        cat_names = set(top_cats[cat_col].to_list())

        group_stats: List[CategoryGroupStats] = []
        means: List[float] = []

        for row in top_cats.iter_rows(named=True):
            cat_name = str(row[cat_col])
            group_vals = (
                clean_df.filter(pl.col(cat_col) == cat_name)[num_col]
                .to_numpy()
            )
            g_count = len(group_vals)
            if g_count == 0:
                continue

            g_mean = float(np.mean(group_vals))
            g_median = float(np.median(group_vals))
            g_min = float(np.min(group_vals))
            g_max = float(np.max(group_vals))
            g_std = float(np.std(group_vals, ddof=1)) if g_count > 1 else 0.0
            g_q1, g_q3 = (
                float(q) for q in np.percentile(group_vals, [25, 75])
            )

            means.append(g_mean)

            group_stats.append(
                CategoryGroupStats(
                    category=cat_name,
                    count=g_count,
                    mean=round(g_mean, 4),
                    median=round(g_median, 4),
                    stddev=round(g_std, 4) if g_std is not None else None,
                    min=round(g_min, 4),
                    max=round(g_max, 4),
                    q1=round(g_q1, 4),
                    q3=round(g_q3, 4),
                )
            )

        if not group_stats:
            return None

        variance_across = float(np.var(means)) if len(means) > 1 else 0.0

        return NumericCategoricalRelationship(
            numeric_column=num_col,
            categorical_column=cat_col,
            group_stats=group_stats,
            variance_across_groups=round(variance_across, 4),
        )

    @staticmethod
    def analyze_categorical_categorical(
        df: pl.DataFrame,
        col_x: str,
        col_y: str,
        max_categories: int = 10,
    ) -> Optional[CategoricalCategoricalRelationship]:
        if col_x not in df.columns or col_y not in df.columns:
            return None

        clean_df = df.select([
            pl.col(col_x).cast(pl.Utf8),
            pl.col(col_y).cast(pl.Utf8),
        ]).drop_nulls()

        if len(clean_df) < 5:
            return None

        # Top categories for X and Y
        top_x = (
            clean_df.group_by(col_x)
            .len()
            .sort("len", descending=True)
            .head(max_categories)[col_x]
            .to_list()
        )
        top_y = (
            clean_df.group_by(col_y)
            .len()
            .sort("len", descending=True)
            .head(max_categories)[col_y]
            .to_list()
        )

        if not top_x or not top_y:
            return None

        # Build contingency table
        filtered_df = clean_df.filter(
            pl.col(col_x).is_in(top_x) & pl.col(col_y).is_in(top_y)
        )

        # Cross tab
        counts = (
            filtered_df.group_by([col_x, col_y])
            .len()
            .to_dicts()
        )
        lookup = {(c[col_x], c[col_y]): c["len"] for c in counts}

        contingency_matrix: List[List[int]] = []
        for x_val in top_x:
            row = []
            for y_val in top_y:
                row.append(lookup.get((x_val, y_val), 0))
            contingency_matrix.append(row)

        cramers_v = calculate_cramers_v(np.array(contingency_matrix))

        return CategoricalCategoricalRelationship(
            column_x=col_x,
            column_y=col_y,
            categories_x=[str(x) for x in top_x],
            categories_y=[str(y) for y in top_y],
            contingency_matrix=contingency_matrix,
            cramers_v=cramers_v,
        )
