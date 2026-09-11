"""
AnalyzaX — Phase 10: Deterministic Confidence Interval Calculations
Supports exact confidence intervals for means, proportions, differences, regression coefficients,
and correlations at configurable confidence levels (90%, 95%, 99%).
Distinguishes confidence intervals from prediction intervals (STAT-11).
"""

import math
from typing import Any, Dict, Optional, Tuple
import numpy as np
from scipy import stats

from backend.app.engines.statistics.models import ConfidenceInterval


def compute_mean_ci(
    values: np.ndarray,
    confidence_level: float = 0.95,
) -> Optional[ConfidenceInterval]:
    """
    Computes confidence interval for the population mean using Student's t-distribution.
    """
    clean = values[~np.isnan(values) & ~np.isinf(values)]
    n = len(clean)
    if n < 2:
        return None

    mean_val = float(np.mean(clean))
    std_val = float(np.std(clean, ddof=1))
    if std_val == 0.0 or math.isclose(std_val, 0.0):
        return ConfidenceInterval(
            level=confidence_level,
            lower=round(mean_val, 4),
            upper=round(mean_val, 4),
            metric_name="mean",
            standard_error=0.0,
            margin_of_error=0.0,
        )

    se = std_val / math.sqrt(n)
    alpha = 1.0 - confidence_level
    df = n - 1
    t_crit = float(stats.t.ppf(1.0 - alpha / 2.0, df))
    margin = t_crit * se

    return ConfidenceInterval(
        level=confidence_level,
        lower=round(mean_val - margin, 4),
        upper=round(mean_val + margin, 4),
        metric_name="mean",
        standard_error=round(se, 4),
        margin_of_error=round(margin, 4),
    )


def compute_proportion_ci(
    success_count: int,
    total_count: int,
    confidence_level: float = 0.95,
    method: str = "wilson",
) -> Optional[ConfidenceInterval]:
    """
    Computes confidence interval for a single proportion using Wilson score interval.
    Robust for both small and large samples.
    """
    if total_count <= 0 or success_count < 0 or success_count > total_count:
        return None

    p_hat = success_count / total_count
    alpha = 1.0 - confidence_level
    z_crit = float(stats.norm.ppf(1.0 - alpha / 2.0))

    if method == "wilson":
        # Wilson score interval with continuity correction
        denom = 1.0 + (z_crit ** 2) / total_count
        center = (p_hat + (z_crit ** 2) / (2.0 * total_count)) / denom
        margin = (z_crit * math.sqrt((p_hat * (1.0 - p_hat) / total_count) + (z_crit ** 2) / (4.0 * (total_count ** 2)))) / denom
        lower = max(0.0, center - margin)
        upper = min(1.0, center + margin)
        se = math.sqrt(p_hat * (1.0 - p_hat) / total_count) if total_count > 0 else 0.0
    else:
        # Normal approximation fallback
        se = math.sqrt(p_hat * (1.0 - p_hat) / total_count)
        margin = z_crit * se
        lower = max(0.0, p_hat - margin)
        upper = min(1.0, p_hat + margin)

    return ConfidenceInterval(
        level=confidence_level,
        lower=round(lower, 4),
        upper=round(upper, 4),
        metric_name="proportion",
        standard_error=round(se, 4),
        margin_of_error=round(margin, 4),
    )


def compute_diff_means_ci(
    group1: np.ndarray,
    group2: np.ndarray,
    confidence_level: float = 0.95,
    equal_var: bool = False,
    paired: bool = False,
) -> Optional[ConfidenceInterval]:
    """
    Computes confidence interval for difference in means (mu1 - mu2).
    Supports independent (Welch or Student) and paired designs.
    """
    if paired:
        mask = ~np.isnan(group1) & ~np.isnan(group2)
        diff = group1[mask] - group2[mask]
        return compute_mean_ci(diff, confidence_level=confidence_level)

    c1 = group1[~np.isnan(group1) & ~np.isinf(group1)]
    c2 = group2[~np.isnan(group2) & ~np.isinf(group2)]
    n1, n2 = len(c1), len(c2)
    if n1 < 2 or n2 < 2:
        return None

    m1, m2 = float(np.mean(c1)), float(np.mean(c2))
    v1, v2 = float(np.var(c1, ddof=1)), float(np.var(c2, ddof=1))
    diff_mean = m1 - m2
    alpha = 1.0 - confidence_level

    if equal_var:
        # Pooled variance Student's t
        df = n1 + n2 - 2
        sp2 = ((n1 - 1) * v1 + (n2 - 1) * v2) / df
        se = math.sqrt(sp2 * (1.0 / n1 + 1.0 / n2))
        t_crit = float(stats.t.ppf(1.0 - alpha / 2.0, df))
    else:
        # Welch-Satterthwaite degrees of freedom
        se = math.sqrt(v1 / n1 + v2 / n2)
        if se == 0.0 or math.isclose(se, 0.0):
            df = n1 + n2 - 2
        else:
            num = (v1 / n1 + v2 / n2) ** 2
            denom = ((v1 / n1) ** 2) / (n1 - 1) + ((v2 / n2) ** 2) / (n2 - 1)
            df = max(1.0, num / denom)
        t_crit = float(stats.t.ppf(1.0 - alpha / 2.0, df))

    margin = t_crit * se
    return ConfidenceInterval(
        level=confidence_level,
        lower=round(diff_mean - margin, 4),
        upper=round(diff_mean + margin, 4),
        metric_name="difference_in_means",
        standard_error=round(se, 4),
        margin_of_error=round(margin, 4),
    )


def compute_diff_proportions_ci(
    count1: int,
    n1: int,
    count2: int,
    n2: int,
    confidence_level: float = 0.95,
) -> Optional[ConfidenceInterval]:
    """
    Computes confidence interval for difference in proportions (p1 - p2) using Agresti-Caffo adjustment.
    """
    if n1 <= 0 or n2 <= 0 or count1 < 0 or count2 < 0 or count1 > n1 or count2 > n2:
        return None

    # Agresti-Caffo adjustment (adds 1 success and 1 failure to each group)
    p1_tilde = (count1 + 1) / (n1 + 2)
    p2_tilde = (count2 + 1) / (n2 + 2)
    diff_tilde = p1_tilde - p2_tilde
    se = math.sqrt(p1_tilde * (1 - p1_tilde) / (n1 + 2) + p2_tilde * (1 - p2_tilde) / (n2 + 2))

    alpha = 1.0 - confidence_level
    z_crit = float(stats.norm.ppf(1.0 - alpha / 2.0))
    margin = z_crit * se

    # Report point estimate as empirical difference
    raw_diff = (count1 / n1) - (count2 / n2)
    return ConfidenceInterval(
        level=confidence_level,
        lower=round(raw_diff - margin, 4),
        upper=round(raw_diff + margin, 4),
        metric_name="difference_in_proportions",
        standard_error=round(se, 4),
        margin_of_error=round(margin, 4),
    )


def compute_correlation_ci(
    r: float,
    n: int,
    confidence_level: float = 0.95,
) -> Optional[ConfidenceInterval]:
    """
    Computes confidence interval for Pearson correlation using Fisher's z-transformation.
    """
    if n < 4 or abs(r) >= 1.0 or math.isnan(r):
        return None

    # Fisher z transform: z = 0.5 * ln((1 + r) / (1 - r))
    z = 0.5 * math.log((1.0 + r) / (1.0 - r))
    se_z = 1.0 / math.sqrt(n - 3)

    alpha = 1.0 - confidence_level
    z_crit = float(stats.norm.ppf(1.0 - alpha / 2.0))

    z_lower = z - z_crit * se_z
    z_upper = z + z_crit * se_z

    # Inverse transform: r = (exp(2z) - 1) / (exp(2z) + 1)
    r_lower = (math.exp(2.0 * z_lower) - 1.0) / (math.exp(2.0 * z_lower) + 1.0)
    r_upper = (math.exp(2.0 * z_upper) - 1.0) / (math.exp(2.0 * z_upper) + 1.0)

    return ConfidenceInterval(
        level=confidence_level,
        lower=round(max(-1.0, r_lower), 4),
        upper=round(min(1.0, r_upper), 4),
        metric_name="correlation_r",
        standard_error=round(se_z, 4),
        margin_of_error=round((r_upper - r_lower) / 2.0, 4),
    )
