"""
AnalyzaX — Phase 10: Deterministic Effect Size Engine
Calculates Cohen's d, Hedges' g, Eta squared, Partial eta squared,
Rank-biserial correlation, Cramér's V, and standardized correlations.
Classifies effect magnitude using standard academic conventions (STAT-14, STAT-20).
"""

import math
from typing import Any, Dict, Optional, Tuple
import numpy as np

from backend.app.engines.statistics.models import EffectSize


def classify_magnitude(val: float, thresholds: Dict[str, float]) -> str:
    """Classifies effect size magnitude by absolute value."""
    abs_val = abs(val)
    if abs_val < thresholds.get("small", 0.2):
        return "negligible"
    elif abs_val < thresholds.get("medium", 0.5):
        return "small"
    elif abs_val < thresholds.get("large", 0.8):
        return "medium"
    return "large"


def compute_cohens_d(
    group1: np.ndarray,
    group2: np.ndarray,
    paired: bool = False,
) -> Optional[EffectSize]:
    """
    Computes Cohen's d for independent or paired samples.
    """
    if paired:
        mask = ~np.isnan(group1) & ~np.isnan(group2)
        diff = group1[mask] - group2[mask]
        n = len(diff)
        if n < 2:
            return None
        mean_d = float(np.mean(diff))
        std_d = float(np.std(diff, ddof=1))
        if std_d == 0.0 or math.isclose(std_d, 0.0):
            d_val = 0.0
        else:
            d_val = mean_d / std_d
    else:
        c1 = group1[~np.isnan(group1)]
        c2 = group2[~np.isnan(group2)]
        n1, n2 = len(c1), len(c2)
        if n1 < 2 or n2 < 2:
            return None

        m1, m2 = float(np.mean(c1)), float(np.mean(c2))
        v1, v2 = float(np.var(c1, ddof=1)), float(np.var(c2, ddof=1))
        sp = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
        if sp == 0.0 or math.isclose(sp, 0.0):
            d_val = 0.0
        else:
            d_val = (m1 - m2) / sp

    interp = classify_magnitude(d_val, {"small": 0.20, "medium": 0.50, "large": 0.80})
    return EffectSize(
        metric_name="cohen_d",
        value=round(float(d_val), 4),
        interpretation=interp,
    )


def compute_hedges_g(
    group1: np.ndarray,
    group2: np.ndarray,
) -> Optional[EffectSize]:
    """
    Computes Hedges' g (small sample bias-corrected Cohen's d).
    """
    c1 = group1[~np.isnan(group1)]
    c2 = group2[~np.isnan(group2)]
    n1, n2 = len(c1), len(c2)
    if n1 < 2 or n2 < 2:
        return None

    d_obj = compute_cohens_d(c1, c2, paired=False)
    if not d_obj:
        return None

    # Correction factor J = 1 - 3 / (4 * (n1 + n2) - 9)
    df = n1 + n2 - 2
    j = 1.0 - (3.0 / (4.0 * df - 1.0))
    g_val = d_obj.value * j

    interp = classify_magnitude(g_val, {"small": 0.20, "medium": 0.50, "large": 0.80})
    return EffectSize(
        metric_name="hedges_g",
        value=round(float(g_val), 4),
        interpretation=interp,
    )


def compute_eta_squared(
    ss_between: float,
    ss_total: float,
) -> Optional[EffectSize]:
    """
    Computes Eta squared for ANOVA models: SS_between / SS_total.
    """
    if ss_total <= 0.0:
        return None
    val = max(0.0, min(1.0, ss_between / ss_total))
    interp = classify_magnitude(val, {"small": 0.01, "medium": 0.06, "large": 0.14})
    return EffectSize(
        metric_name="eta_squared",
        value=round(float(val), 4),
        interpretation=interp,
    )


def compute_rank_biserial_mann_whitney(
    u_stat: float,
    n1: int,
    n2: int,
) -> Optional[EffectSize]:
    """
    Computes rank-biserial correlation for Mann-Whitney U: r_rb = 1 - (2U / (n1 * n2)).
    """
    if n1 <= 0 or n2 <= 0:
        return None
    r_rb = 1.0 - (2.0 * u_stat / (n1 * n2))
    interp = classify_magnitude(r_rb, {"small": 0.10, "medium": 0.30, "large": 0.50})
    return EffectSize(
        metric_name="rank_biserial_r",
        value=round(float(r_rb), 4),
        interpretation=interp,
    )


def compute_cramers_v(
    chi2_stat: float,
    n: int,
    r: int,
    k: int,
) -> Optional[EffectSize]:
    """
    Computes Cramér's V measure of association for contingency tables.
    """
    if n <= 0:
        return None
    min_dim = min(r - 1, k - 1)
    if min_dim <= 0:
        return EffectSize(
            metric_name="cramer_v",
            value=0.0,
            interpretation="negligible",
        )
    v = math.sqrt(chi2_stat / (n * min_dim))
    v_clamped = min(1.0, max(0.0, v))
    interp = classify_magnitude(v_clamped, {"small": 0.10, "medium": 0.30, "large": 0.50})
    return EffectSize(
        metric_name="cramer_v",
        value=round(float(v_clamped), 4),
        interpretation=interp,
    )


def compute_pearson_r_effect_size(r: float) -> EffectSize:
    """Classifies Pearson or Spearman r as an effect size."""
    interp = classify_magnitude(r, {"small": 0.10, "medium": 0.30, "large": 0.50})
    return EffectSize(
        metric_name="pearson_r",
        value=round(float(r), 4),
        interpretation=interp,
    )
