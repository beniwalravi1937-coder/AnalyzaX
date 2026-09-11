"""
AnalyzaX — Phase 10: Covariance Analysis
Calculates sample covariance and covariance matrices with explicit notes on scale dependence (STAT-23).
"""

from typing import Any, Dict, List, Optional
import numpy as np

from backend.app.engines.statistics.models import MissingDataReport


def compute_covariance_matrix(
    data: Dict[str, np.ndarray],
    max_columns: int = 50,
) -> Dict[str, Any]:
    """
    Computes sample covariance matrix over numeric columns.
    """
    cols = list(data.keys())[:max_columns]
    matrix = []
    pairs = []

    for i, col_a in enumerate(cols):
        row = []
        for j, col_b in enumerate(cols):
            x = data[col_a]
            y = data[col_b]
            mask = ~np.isnan(x) & ~np.isinf(x) & ~np.isnan(y) & ~np.isinf(y)
            x_c = x[mask].astype(float)
            y_c = y[mask].astype(float)
            n = len(x_c)

            if n < 2:
                row.append({"cov": None, "n": n, "is_valid": False})
            else:
                cov_val = float(np.cov(x_c, y_c, ddof=1)[0, 1])
                row.append({"cov": round(cov_val, 4), "n": n, "is_valid": True})
                if i < j:
                    pairs.append({
                        "var1": col_a,
                        "var2": col_b,
                        "covariance": round(cov_val, 4),
                        "sample_size": n,
                    })
        matrix.append(row)

    return {
        "columns": cols,
        "matrix": matrix,
        "pairwise_covariance": pairs,
        "scale_limitation_note": (
            "Covariance values depend directly on the units and scale of measurement. "
            "They indicate direction of joint variation (+ or -) but their magnitude cannot be directly compared across different variables."
        ),
    }
