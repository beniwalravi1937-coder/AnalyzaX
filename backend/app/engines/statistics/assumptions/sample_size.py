"""
AnalyzaX — Phase 10: Sample Size & Statistical Power Diagnostics
Surfaces sample size adequacy checks and statistical power warnings (STAT-34, STAT-38).
"""

from typing import Any, Dict, List, Optional
from backend.app.engines.statistics.models import AssumptionCheck, AssumptionStatus, FindingSeverity


def check_sample_size_adequacy(
    sample_sizes: Dict[str, int],
    analysis_type: str,
    min_per_group: int = 15,
) -> AssumptionCheck:
    """
    Evaluates whether the sample size is adequate for reliable inference.
    Prevents overconfident conclusions from tiny samples (STAT-34, STAT-38).
    """
    total_n = sum(sample_sizes.values())
    min_found = min(sample_sizes.values()) if sample_sizes else 0
    k_groups = len(sample_sizes)

    if min_found < 5:
        status = AssumptionStatus.VIOLATION
        severity = FindingSeverity.HIGH
        evidence = f"Extremely small sample size detected (minimum group n={min_found}, total N={total_n})."
        description = "Statistical power is severely limited; type II error rates are high."
        recommendation = "Results must be treated with extreme caution. Statistical significance may not be reliable."
    elif min_found < min_per_group:
        status = AssumptionStatus.WARNING
        severity = FindingSeverity.MEDIUM
        evidence = f"Small sample size detected (minimum group n={min_found} < recommended {min_per_group}, total N={total_n})."
        description = "Small samples have limited power to detect subtle effect sizes."
        recommendation = "Interpret confidence intervals rather than relying solely on p-values. Non-parametric methods may be safer."
    else:
        status = AssumptionStatus.PASS
        severity = FindingSeverity.INFO
        evidence = f"Adequate sample size (minimum group n={min_found}, total N={total_n})."
        description = "Sample size satisfies standard thresholds for statistical power."
        recommendation = "Sufficient power for medium-to-large effects."

    return AssumptionCheck(
        check_id=f"sample_size_{analysis_type}",
        assumption="Sample Size & Statistical Power Adequacy",
        status=status,
        severity=severity,
        method="sample_size_heuristic",
        statistic=float(total_n),
        p_value=None,
        evidence=evidence,
        description=description,
        recommendation=recommendation,
    )
