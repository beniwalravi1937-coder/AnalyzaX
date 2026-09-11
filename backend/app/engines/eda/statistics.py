"""
AnalyzaX — Phase 7: Pure Deterministic Statistical Engine
Vectorized statistical routines using Polars and SciPy/NumPy.
Zero LLM or non-deterministic calculations.
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import polars as pl
from scipy import stats


def calculate_skewness(values: np.ndarray) -> Optional[float]:
    """Calculates sample-adjusted Fisher-Pearson skewness coefficient."""
    clean = values[~np.isnan(values)]
    if len(clean) < 3:
        return None
    std = float(np.std(clean, ddof=1))
    if std == 0.0 or math.isclose(std, 0.0):
        return 0.0
    try:
        val = float(stats.skew(clean, bias=False))
        return None if (math.isnan(val) or math.isinf(val)) else round(val, 4)
    except Exception:
        return None


def calculate_kurtosis(values: np.ndarray) -> Optional[float]:
    """Calculates sample-adjusted excess kurtosis (normal distribution = 0.0)."""
    clean = values[~np.isnan(values)]
    if len(clean) < 4:
        return None
    std = float(np.std(clean, ddof=1))
    if std == 0.0 or math.isclose(std, 0.0):
        return 0.0
    try:
        val = float(stats.kurtosis(clean, bias=False, fisher=True))
        return None if (math.isnan(val) or math.isinf(val)) else round(val, 4)
    except Exception:
        return None


def calculate_histogram_bins(
    values: np.ndarray,
    max_bins: int = 30,
) -> Tuple[List[Dict[str, Any]], int, str, float, float]:
    """
    Computes deterministic histogram bins using Freedman-Diaconis rule with Sturges fallback.
    Clamps bin count between 5 and max_bins to ensure readable visualizations.
    """
    clean = values[~np.isnan(values)]
    n = len(clean)
    if n == 0:
        return [], 0, "none", 0.0, 0.0

    min_val = float(np.min(clean))
    max_val = float(np.max(clean))

    if math.isclose(min_val, max_val):
        # Constant distribution
        return [
            {
                "bin_start": round(min_val - 0.5, 4),
                "bin_end": round(max_val + 0.5, 4),
                "count": n,
                "percentage": 100.0,
            }
        ], 1, "constant", min_val, max_val

    # Freedman-Diaconis rule
    q75, q25 = np.percentile(clean, [75, 25])
    iqr = q75 - q25
    bin_method = "freedman_diaconis"

    if iqr > 0:
        bin_width = 2.0 * iqr * (n ** (-1.0 / 3.0))
        calculated_bins = int(math.ceil((max_val - min_val) / bin_width))
    else:
        # Sturges rule fallback
        bin_method = "sturges"
        calculated_bins = int(math.ceil(math.log2(n) + 1))

    bin_count = max(5, min(max_bins, calculated_bins))
    counts, bin_edges = np.histogram(clean, bins=bin_count)

    bins_data = []
    total = float(n)
    for i in range(len(counts)):
        b_start = float(bin_edges[i])
        b_end = float(bin_edges[i + 1])
        cnt = int(counts[i])
        pct = round((cnt / total) * 100.0, 2)
        bins_data.append({
            "bin_start": round(b_start, 4),
            "bin_end": round(b_end, 4),
            "count": cnt,
            "percentage": pct,
        })

    return bins_data, bin_count, bin_method, min_val, max_val


def calculate_linear_regression(
    x: np.ndarray, y: np.ndarray
) -> Optional[Dict[str, float]]:
    """Calculates linear slope, intercept, and R^2 correlation."""
    valid_mask = ~np.isnan(x) & ~np.isnan(y)
    x_c = x[valid_mask]
    y_c = y[valid_mask]

    if len(x_c) < 3:
        return None

    std_x = np.std(x_c)
    std_y = np.std(y_c)
    if std_x == 0.0 or std_y == 0.0:
        return None

    try:
        res = stats.linregress(x_c, y_c)
        r_squared = float(res.rvalue ** 2)
        return {
            "slope": round(float(res.slope), 4),
            "intercept": round(float(res.intercept), 4),
            "r_squared": round(r_squared, 4),
        }
    except Exception:
        return None


def calculate_cramers_v(contingency_matrix: np.ndarray) -> Optional[float]:
    """Calculates Cramér's V measure of association between two categorical variables."""
    if contingency_matrix.size == 0:
        return None
    n = contingency_matrix.sum()
    if n == 0:
        return None

    try:
        chi2, _, _, _ = stats.chi2_contingency(contingency_matrix, correction=False)
        r, k = contingency_matrix.shape
        min_dim = min(r - 1, k - 1)
        if min_dim == 0:
            return 0.0
        v = math.sqrt(chi2 / (n * min_dim))
        return round(float(min(1.0, max(0.0, v))), 4)
    except Exception:
        return None
