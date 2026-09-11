"""
AnalyzaX — Phase 7: Correlation Analyzer
Computes Pearson and Spearman correlation matrices and ranks statistically significant pairs.
"""

import math
from typing import List, Optional
import numpy as np
import polars as pl
from scipy import stats

from backend.app.engines.eda.models import (
    CorrelationMatrix,
    CorrelationMethod,
    RankedCorrelationPair,
)


class CorrelationAnalyzer:
    @staticmethod
    def analyze(
        df: pl.DataFrame,
        numeric_columns: List[str],
        method: CorrelationMethod = CorrelationMethod.PEARSON,
    ) -> Optional[CorrelationMatrix]:
        # Filter valid numeric columns with non-zero variance
        valid_cols: List[str] = []
        for col in numeric_columns:
            if col in df.columns:
                s = df[col].drop_nulls()
                if len(s) > 2 and s.n_unique() > 1:
                    valid_cols.append(col)

        if len(valid_cols) < 2:
            return None

        n = len(valid_cols)
        matrix: List[List[Optional[float]]] = [[None for _ in range(n)] for _ in range(n)]
        ranked_pairs: List[RankedCorrelationPair] = []

        # Convert to float numpy arrays
        col_arrays = {}
        for col in valid_cols:
            col_arrays[col] = df[col].cast(pl.Float64).to_numpy()

        for i in range(n):
            matrix[i][i] = 1.0
            col_i = valid_cols[i]
            arr_i = col_arrays[col_i]

            for j in range(i + 1, n):
                col_j = valid_cols[j]
                arr_j = col_arrays[col_j]

                # Mask nulls pair-wise
                mask = ~np.isnan(arr_i) & ~np.isnan(arr_j)
                clean_i = arr_i[mask]
                clean_j = arr_j[mask]

                if len(clean_i) < 3:
                    corr_val = None
                else:
                    try:
                        if method == CorrelationMethod.SPEARMAN:
                            res = stats.spearmanr(clean_i, clean_j)
                        else:
                            res = stats.pearsonr(clean_i, clean_j)
                        val = float(res.statistic)
                        corr_val = None if (math.isnan(val) or math.isinf(val)) else round(val, 4)
                    except Exception:
                        corr_val = None

                matrix[i][j] = corr_val
                matrix[j][i] = corr_val

                if corr_val is not None:
                    abs_val = abs(corr_val)
                    if abs_val >= 0.8:
                        strength = "very_strong"
                    elif abs_val >= 0.6:
                        strength = "strong"
                    elif abs_val >= 0.4:
                        strength = "moderate"
                    elif abs_val >= 0.2:
                        strength = "weak"
                    else:
                        strength = "negligible"

                    ranked_pairs.append(
                        RankedCorrelationPair(
                            column_x=col_i,
                            column_y=col_j,
                            correlation=corr_val,
                            abs_correlation=round(abs_val, 4),
                            strength=strength,
                            method=method,
                        )
                    )

        # Sort ranked pairs by absolute correlation descending
        ranked_pairs.sort(key=lambda x: x.abs_correlation, reverse=True)

        return CorrelationMatrix(
            method=method,
            columns=valid_cols,
            matrix=matrix,
            ranked_pairs=ranked_pairs,
        )
