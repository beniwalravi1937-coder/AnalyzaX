"""
AnalyzaX — Phase 7: Outlier Analyzer
Detects univariate numerical outliers using standard IQR fences (Tukey's fences)
and extracts sample extreme values.
"""

from typing import List
import numpy as np
import polars as pl

from backend.app.engines.eda.models import OutlierAnalysis, OutlierColumnSummary


class OutliersAnalyzer:
    @staticmethod
    def analyze(df: pl.DataFrame, numeric_columns: List[str]) -> OutlierAnalysis:
        total_outliers = 0
        summaries: List[OutlierColumnSummary] = []
        n_rows = len(df)

        if n_rows == 0:
            return OutlierAnalysis(total_outlier_count=0, columns_with_outliers=[])

        for col in numeric_columns:
            if col not in df.columns:
                continue

            clean_series = df[col].cast(pl.Float64).drop_nulls()
            if len(clean_series) < 5:
                continue

            arr = clean_series.to_numpy()
            q25, q75 = np.percentile(arr, [25, 75])
            iqr = float(q75 - q25)

            if iqr <= 0.0:
                continue

            lower_bound = float(q25 - 1.5 * iqr)
            upper_bound = float(q75 + 1.5 * iqr)

            outlier_mask = (arr < lower_bound) | (arr > upper_bound)
            outlier_vals = arr[outlier_mask]
            outlier_count = int(len(outlier_vals))

            if outlier_count > 0:
                total_outliers += outlier_count
                pct = round((outlier_count / n_rows) * 100.0, 2)

                # Collect extreme samples (e.g. top 5 lowest and top 5 highest)
                sorted_outliers = np.sort(outlier_vals)
                if len(sorted_outliers) <= 10:
                    extremes = [round(float(v), 4) for v in sorted_outliers]
                else:
                    lowest = [round(float(v), 4) for v in sorted_outliers[:5]]
                    highest = [round(float(v), 4) for v in sorted_outliers[-5:]]
                    extremes = lowest + highest

                summaries.append(
                    OutlierColumnSummary(
                        column=col,
                        outlier_count=outlier_count,
                        outlier_percentage=pct,
                        lower_bound=round(lower_bound, 4),
                        upper_bound=round(upper_bound, 4),
                        method="IQR",
                        sample_extreme_values=extremes,
                    )
                )

        # Sort columns with outliers by percentage descending
        summaries.sort(key=lambda x: x.outlier_percentage, reverse=True)

        return OutlierAnalysis(
            total_outlier_count=total_outliers,
            columns_with_outliers=summaries,
        )
