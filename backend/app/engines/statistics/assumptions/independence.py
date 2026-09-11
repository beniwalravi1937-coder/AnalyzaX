"""
AnalyzaX — Phase 10: Independence Assumption Diagnostics
Evaluates residual independence / autocorrelation using the Durbin-Watson statistic (STAT-35).
"""

from typing import Any, Dict, Optional
import numpy as np

from backend.app.engines.statistics.models import AssumptionCheck, AssumptionStatus, FindingSeverity


def check_residual_independence(
    residuals: np.ndarray,
    model_name: str = "Linear Regression",
) -> AssumptionCheck:
    """
    Evaluates independence of error terms using Durbin-Watson statistic.
    DW values near 2.0 indicate no autocorrelation. Values < 1.5 or > 2.5 suggest autocorrelation.
    """
    n = len(residuals)
    if n < 4:
        return AssumptionCheck(
            check_id="independence_residuals",
            assumption="Independence of Errors",
            status=AssumptionStatus.INSUFFICIENT_DATA,
            severity=FindingSeverity.LOW,
            method="sample_size_check",
            statistic=None,
            p_value=None,
            evidence="Too few residuals to compute autocorrelation.",
            description="Requires at least 4 observations.",
            recommendation="Review study design.",
        )

    diff = np.diff(residuals)
    sum_diff2 = float(np.sum(diff ** 2))
    sum_res2 = float(np.sum(residuals ** 2))
    dw_stat = sum_diff2 / sum_res2 if sum_res2 > 0 else 2.0

    if 1.5 <= dw_stat <= 2.5:
        status = AssumptionStatus.PASS
        severity = FindingSeverity.INFO
        evidence = f"Durbin-Watson statistic ({round(dw_stat, 2)}) is close to 2.0, suggesting independent residuals."
        recommendation = "Independence assumption is reasonably satisfied."
    elif 1.0 <= dw_stat < 1.5 or 2.5 < dw_stat <= 3.0:
        status = AssumptionStatus.WARNING
        severity = FindingSeverity.MEDIUM
        evidence = f"Durbin-Watson statistic ({round(dw_stat, 2)}) indicates potential mild autocorrelation."
        recommendation = "Check for time-series ordering or clustered observations."
    else:
        status = AssumptionStatus.VIOLATION
        severity = FindingSeverity.HIGH
        evidence = f"Durbin-Watson statistic ({round(dw_stat, 2)}) indicates strong residual autocorrelation."
        recommendation = "Standard errors may be underestimated. Consider time-series or generalized linear models."

    return AssumptionCheck(
        check_id="independence_residuals",
        assumption="Independence of Errors",
        status=status,
        severity=severity,
        method="Durbin-Watson Test",
        statistic=round(dw_stat, 4),
        p_value=None,
        evidence=evidence,
        description="Assesses whether residuals are mutually independent across sequential observations.",
        recommendation=recommendation,
    )
