"""
AnalyzaX — Phase 7: Univariate Numeric Analyzer
Computes comprehensive descriptive statistics, quantiles, shape detection,
deterministic histogram binning, and 5-number box plot summaries.
"""

import math
from typing import List, Optional
import numpy as np
import polars as pl

from backend.app.engines.eda.models import (
    BoxPlotData,
    HistogramBin,
    HistogramData,
    UnivariateNumeric,
)
from backend.app.engines.eda.statistics import (
    calculate_histogram_bins,
    calculate_kurtosis,
    calculate_skewness,
)


class NumericAnalyzer:
    @staticmethod
    def analyze(df: pl.DataFrame, column: str) -> Optional[UnivariateNumeric]:
        return NumericAnalyzer.analyze_column(df, column)

    @staticmethod
    def analyze_column(df: pl.DataFrame, column: str) -> Optional[UnivariateNumeric]:
        if column not in df.columns:
            return None

        col_series = df[column]
        total_len = len(col_series)
        null_cnt = col_series.null_count()
        null_pct = round((null_cnt / total_len * 100.0), 2) if total_len > 0 else 0.0

        clean_s = col_series.drop_nulls()
        valid_cnt = len(clean_s)
        if valid_cnt == 0:
            return UnivariateNumeric(
                column=column,
                count=0,
                null_count=null_cnt,
                null_percentage=null_pct,
                unique_count=0,
                distribution_shape="empty",
            )

        unique_cnt = clean_s.n_unique()

        # Convert to numpy float array for stats
        np_vals = clean_s.cast(pl.Float64).to_numpy()

        min_val = float(np.min(np_vals))
        max_val = float(np.max(np_vals))
        mean_val = float(np.mean(np_vals))
        median_val = float(np.median(np_vals))
        std_val = float(np.std(np_vals, ddof=1)) if valid_cnt > 1 else 0.0
        var_val = float(np.var(np_vals, ddof=1)) if valid_cnt > 1 else 0.0
        rng_val = float(max_val - min_val)

        q25, q75 = float(np.percentile(np_vals, 25)), float(np.percentile(np_vals, 75))
        iqr_val = float(q75 - q25)

        skew_val = calculate_skewness(np_vals)
        kurt_val = calculate_kurtosis(np_vals)

        cv_val = round((std_val / mean_val), 4) if mean_val != 0.0 and not math.isclose(mean_val, 0.0) else None

        zero_cnt = int(np.sum(np_vals == 0.0))
        neg_cnt = int(np.sum(np_vals < 0.0))
        pos_cnt = int(np.sum(np_vals > 0.0))

        # Classify distribution shape
        shape = "normal"
        if math.isclose(min_val, max_val):
            shape = "constant"
        elif skew_val is not None:
            if skew_val > 1.0:
                shape = "right_skewed"
            elif skew_val < -1.0:
                shape = "left_skewed"
            elif abs(skew_val) <= 0.5:
                shape = "normal"
            else:
                shape = "moderate_skew"

        # Histogram data
        bins_raw, bin_count, bin_method, b_min, b_max = calculate_histogram_bins(np_vals, max_bins=30)
        hist_data = HistogramData(
            bins=[HistogramBin(**b) for b in bins_raw],
            bin_count=bin_count,
            bin_method=bin_method,
            min_value=round(b_min, 4),
            max_value=round(b_max, 4),
        )

        # Box plot outliers
        lower_fence = q25 - 1.5 * iqr_val
        upper_fence = q75 + 1.5 * iqr_val
        outlier_vals = np_vals[(np_vals < lower_fence) | (np_vals > upper_fence)]
        # Sample max 20 outliers for bounded payload
        sample_outliers = [round(float(x), 4) for x in outlier_vals[:20]]

        box_data = BoxPlotData(
            min=round(min_val, 4),
            q1=round(q25, 4),
            median=round(median_val, 4),
            q3=round(q75, 4),
            max=round(max_val, 4),
            iqr=round(iqr_val, 4),
            outlier_points=sample_outliers,
        )

        return UnivariateNumeric(
            column=column,
            count=valid_cnt,
            null_count=null_cnt,
            null_percentage=null_pct,
            unique_count=unique_cnt,
            min=round(min_val, 4),
            max=round(max_val, 4),
            mean=round(mean_val, 4),
            median=round(median_val, 4),
            stddev=round(std_val, 4),
            variance=round(var_val, 4),
            range=round(rng_val, 4),
            q1=round(q25, 4),
            q3=round(q75, 4),
            iqr=round(iqr_val, 4),
            skewness=skew_val,
            kurtosis=kurt_val,
            coefficient_of_variation=cv_val,
            zero_count=zero_cnt,
            negative_count=neg_cnt,
            positive_count=pos_cnt,
            distribution_shape=shape,
            histogram=hist_data,
            box_plot=box_data,
        )

    @classmethod
    def analyze_all(cls, df: pl.DataFrame, columns: List[str]) -> List[UnivariateNumeric]:
        results = []
        for col in columns:
            res = cls.analyze_column(df, col)
            if res is not None:
                results.append(res)
        return results
