"""
AnalyzaX — Phase 10: Normality Assumption Diagnostics
Evaluates distribution normality using Shapiro-Wilk, D'Agostino-Pearson, and skewness/kurtosis.
Surfaces sample-size power limitations and large-sample sensitivity (STAT-35, STAT-36, STAT-38).
"""

import math
from typing import Any, Dict, Optional, Tuple
import numpy as np
from scipy import stats

from backend.app.engines.statistics.models import AssumptionCheck, AssumptionStatus, FindingSeverity


def check_normality(
    values: np.ndarray,
    variable_name: str,
    alpha: float = 0.05,
) -> AssumptionCheck:
    """
    Evaluates whether a numeric sample conforms to a normal distribution.
    Does not rely solely on p-value; considers sample size, skewness, and kurtosis.
    """
    clean = values[~np.isnan(values) & ~np.isinf(values)].astype(float)
    n = len(clean)

    if n < 3:
        return AssumptionCheck(
            check_id=f"normality_{variable_name}",
            assumption="Normality of Distribution",
            status=AssumptionStatus.INSUFFICIENT_DATA,
            severity=FindingSeverity.HIGH,
            method="sample_size_check",
            statistic=None,
            p_value=None,
            evidence=f"Sample size (n={n}) is too small to assess normality.",
            description="Normality tests require at least 3 valid observations.",
            recommendation="Collect more data or consider non-parametric methods.",
        )

    # Compute skewness & excess kurtosis
    std_val = float(np.std(clean, ddof=1)) if n > 1 else 0.0
    if std_val == 0.0 or math.isclose(std_val, 0.0):
        return AssumptionCheck(
            check_id=f"normality_{variable_name}",
            assumption="Normality of Distribution",
            status=AssumptionStatus.VIOLATION,
            severity=FindingSeverity.HIGH,
            method="variance_check",
            statistic=0.0,
            p_value=0.0,
            evidence=f"Variable '{variable_name}' is constant (zero variance).",
            description="Constant values do not follow a continuous normal distribution.",
            recommendation="Verify data collection; exclude constant variables from inferential modeling.",
        )

    # Select test method based on sample size
    if n <= 5000:
        test_name = "Shapiro-Wilk Test"
        res = stats.shapiro(clean)
        test_stat = float(res.statistic)
        p_val = float(res.pvalue)
    else:
        test_name = "D'Agostino-Pearson Omnibus Test"
        res = stats.normaltest(clean)
        test_stat = float(res.statistic)
        p_val = float(res.pvalue)

    # Skewness and kurtosis
    sk = float(stats.skew(clean, bias=False))
    kt = float(stats.kurtosis(clean, bias=False, fisher=True))

    # Evaluate status taking sample size caveats into account (STAT-10, STAT-36)
    if n < 20:
        if p_val < alpha:
            status = AssumptionStatus.VIOLATION
            severity = FindingSeverity.HIGH
            evidence = (
                f"{test_name} rejected normality (W={round(test_stat, 4)}, p={round(p_val, 4)}). "
                f"Small sample size (n={n}) limits test power."
            )
            recommendation = "Consider non-parametric tests (e.g. Mann-Whitney U or Wilcoxon) due to small sample non-normality."
        else:
            status = AssumptionStatus.WARNING
            severity = FindingSeverity.LOW
            evidence = (
                f"{test_name} did not reject normality (p={round(p_val, 4)}), but small sample size (n={n}) "
                f"has limited statistical power to detect meaningful non-normality."
            )
            recommendation = "Inspect Q-Q plot and distribution histogram before relying strictly on parametric assumptions."

    elif n > 500:
        # Large sample sensitivity caveat
        moderate_skew = abs(sk) < 1.0 and abs(kt) < 1.5
        if p_val < alpha:
            if moderate_skew:
                status = AssumptionStatus.WARNING
                severity = FindingSeverity.LOW
                evidence = (
                    f"{test_name} p={round(p_val, 6)} < {alpha}, but skewness ({round(sk, 2)}) and kurtosis ({round(kt, 2)}) "
                    f"show only mild departure from normality. In large samples (n={n}), the Central Limit Theorem generally ensures robustness of t/F tests."
                )
                recommendation = "Parametric tests are generally robust under CLT for this sample size."
            else:
                status = AssumptionStatus.VIOLATION
                severity = FindingSeverity.MEDIUM
                evidence = (
                    f"{test_name} p={round(p_val, 6)} with marked skewness ({round(sk, 2)}) and kurtosis ({round(kt, 2)}) "
                    f"in large sample (n={n})."
                )
                recommendation = "Consider non-parametric methods or robust standard errors."
        else:
            status = AssumptionStatus.PASS
            severity = FindingSeverity.INFO
            evidence = f"{test_name} indicates consistency with a normal distribution (W={round(test_stat, 4)}, p={round(p_val, 4)}, n={n})."
            recommendation = "Parametric methods (t-test, ANOVA, OLS) are appropriate."

    else:
        # Moderate sample size (20 <= n <= 500)
        if p_val >= alpha:
            status = AssumptionStatus.PASS
            severity = FindingSeverity.INFO
            evidence = f"{test_name} shows no evidence of non-normality (W={round(test_stat, 4)}, p={round(p_val, 4)}, n={n})."
            recommendation = "Standard parametric assumptions hold."
        else:
            status = AssumptionStatus.VIOLATION
            severity = FindingSeverity.MEDIUM
            evidence = f"{test_name} indicates departure from normality (W={round(test_stat, 4)}, p={round(p_val, 4)}, skew={round(sk, 2)}, kurtosis={round(kt, 2)})."
            recommendation = "Consider non-parametric alternative or verify residual distribution."

    return AssumptionCheck(
        check_id=f"normality_{variable_name}",
        assumption="Normality of Distribution",
        status=status,
        severity=severity,
        method=test_name,
        statistic=round(test_stat, 4),
        p_value=round(p_val, 6),
        evidence=evidence,
        description=f"Assesses whether '{variable_name}' follows a Gaussian distribution.",
        recommendation=recommendation,
    )
