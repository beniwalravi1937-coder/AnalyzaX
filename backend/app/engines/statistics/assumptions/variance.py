"""
AnalyzaX — Phase 10: Homogeneity of Variance Assumption Diagnostics
Evaluates equal variance across groups using Levene's test (STAT-35, STAT-37).
"""

from typing import Any, Dict, List, Optional
import numpy as np
from scipy import stats

from backend.app.engines.statistics.models import AssumptionCheck, AssumptionStatus, FindingSeverity


def check_homogeneity_of_variance(
    groups_data: Dict[str, np.ndarray],
    outcome_name: str,
    alpha: float = 0.05,
) -> AssumptionCheck:
    """
    Evaluates whether group variances are equal using median-centered Levene's test.
    """
    clean_groups = {}
    variances = {}

    for g_name, vals in groups_data.items():
        c = vals[~np.isnan(vals) & ~np.isinf(vals)].astype(float)
        if len(c) >= 2:
            clean_groups[g_name] = c
            variances[g_name] = float(np.var(c, ddof=1))

    if len(clean_groups) < 2:
        return AssumptionCheck(
            check_id=f"variance_{outcome_name}",
            assumption="Homogeneity of Variance (Equal Variance)",
            status=AssumptionStatus.INSUFFICIENT_DATA,
            severity=FindingSeverity.HIGH,
            method="sample_size_check",
            statistic=None,
            p_value=None,
            evidence="Fewer than 2 groups with at least 2 valid observations.",
            description="Equal variance test requires at least 2 non-empty groups.",
            recommendation="Verify group sample sizes.",
        )

    # Variance ratio check
    var_values = list(variances.values())
    max_var = max(var_values)
    min_var = max(min(var_values), 1e-12)
    var_ratio = max_var / min_var

    try:
        arrays = list(clean_groups.values())
        res = stats.levene(*arrays, center="median")
        w_stat = float(res.statistic)
        p_val = float(res.pvalue)
    except Exception as e:
        return AssumptionCheck(
            check_id=f"variance_{outcome_name}",
            assumption="Homogeneity of Variance",
            status=AssumptionStatus.NOT_CHECKED,
            severity=FindingSeverity.LOW,
            method="levene_test",
            statistic=None,
            p_value=None,
            evidence=f"Could not compute Levene's test: {e}",
            description="Error running test.",
            recommendation="Use Welch's test by default.",
        )

    if p_val >= alpha and var_ratio < 3.0:
        status = AssumptionStatus.PASS
        severity = FindingSeverity.INFO
        evidence = (
            f"Levene's test shows no significant evidence of unequal variances "
            f"(W={round(w_stat, 4)}, p={round(p_val, 4)}, max/min variance ratio = {round(var_ratio, 2)})."
        )
        recommendation = "Standard equal-variance tests (e.g. Student's t, standard ANOVA) are acceptable."
    elif p_val < alpha and var_ratio >= 3.0:
        status = AssumptionStatus.VIOLATION
        severity = FindingSeverity.HIGH
        evidence = (
            f"Levene's test indicates significant variance inequality "
            f"(W={round(w_stat, 4)}, p={round(p_val, 4)}, max/min variance ratio = {round(var_ratio, 2)})."
        )
        recommendation = "Use Welch's t-test or non-parametric methods which do not assume equal variance."
    else:
        status = AssumptionStatus.WARNING
        severity = FindingSeverity.MEDIUM
        evidence = (
            f"Moderate variance inequality observed (W={round(w_stat, 4)}, p={round(p_val, 4)}, "
            f"variance ratio = {round(var_ratio, 2)})."
        )
        recommendation = "Welch's t-test is recommended to protect against type I error."

    return AssumptionCheck(
        check_id=f"variance_{outcome_name}",
        assumption="Homogeneity of Variance (Equal Variance)",
        status=status,
        severity=severity,
        method="Levene's Test (median-centered)",
        statistic=round(w_stat, 4),
        p_value=round(p_val, 6),
        evidence=evidence,
        description=f"Assesses whether '{outcome_name}' has equal variance across groups.",
        recommendation=recommendation,
    )
