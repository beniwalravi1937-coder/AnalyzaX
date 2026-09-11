"""
AnalyzaX — Phase 10: Deterministic Statistical Findings Engine
Generates and ranks structured StatisticalFinding objects from computed statistical results (STAT-36, STAT-40, STAT-65).
"""

import uuid
from typing import Any, Dict, List, Optional
from backend.app.engines.statistics.models import (
    AssumptionCheck,
    AssumptionStatus,
    FindingCategory,
    FindingSeverity,
    StatisticalFinding,
)


def generate_statistical_findings(
    analysis_type: str,
    method: str,
    target_columns: List[str],
    statistics: Dict[str, Any],
    p_values: Dict[str, Optional[float]],
    effect_sizes: List[Dict[str, Any]],
    assumptions: List[AssumptionCheck],
    missing_data: Dict[str, Any],
    alpha: float = 0.05,
) -> List[StatisticalFinding]:
    """
    Deterministically extracts and ranks statistical findings from completed analytical calculations.
    """
    findings: List[StatisticalFinding] = []

    # 1. Missing data finding
    excluded = missing_data.get("excluded_observations", 0)
    orig_obs = missing_data.get("original_observations", 0)
    if excluded > 0 and orig_obs > 0:
        pct_excl = round(excluded / orig_obs * 100.0, 1)
        if pct_excl > 15.0:
            findings.append(
                StatisticalFinding(
                    finding_id=f"find_missing_{uuid.uuid4().hex[:6]}",
                    category=FindingCategory.MISSING_DATA_CONCERN,
                    severity=FindingSeverity.HIGH if pct_excl > 30.0 else FindingSeverity.MEDIUM,
                    title=f"High missingness excluded ({pct_excl}% of observations)",
                    description=(
                        f"{excluded} of {orig_obs} total observations were excluded from analysis "
                        f"under the {missing_data.get('missing_policy', 'listwise_deletion')} policy. "
                        "High exclusion rates can introduce selection bias if data is not Missing Completely At Random (MCAR)."
                    ),
                    columns=target_columns,
                    method=method,
                    evidence=f"Excluded {excluded}/{orig_obs} rows ({pct_excl}%).",
                    confidence=0.9,
                    limitations=["Listwise deletion may reduce statistical power and bias estimates if missingness is systematic."],
                )
            )

    # 2. Assumption checks findings
    for check in assumptions:
        if check.status == AssumptionStatus.VIOLATION:
            category = FindingCategory.ASSUMPTION_WARNING
            if "normality" in check.check_id:
                category = FindingCategory.DISTRIBUTION_CONCERN
            elif "variance" in check.check_id:
                category = FindingCategory.HETEROSCEDASTICITY
            elif "sample_size" in check.check_id:
                category = FindingCategory.INSUFFICIENT_SAMPLE

            findings.append(
                StatisticalFinding(
                    finding_id=f"find_assump_{uuid.uuid4().hex[:6]}",
                    category=category,
                    severity=check.severity,
                    title=f"Assumption Violation: {check.assumption}",
                    description=f"{check.evidence} {check.description}",
                    columns=target_columns,
                    method=method,
                    p_value=check.p_value,
                    evidence=check.evidence,
                    confidence=1.0,
                    limitations=[check.recommendation] if check.recommendation else [],
                )
            )
        elif check.status == AssumptionStatus.WARNING and check.severity in (FindingSeverity.MEDIUM, FindingSeverity.HIGH):
            findings.append(
                StatisticalFinding(
                    finding_id=f"find_assump_{uuid.uuid4().hex[:6]}",
                    category=FindingCategory.ASSUMPTION_WARNING,
                    severity=FindingSeverity.LOW,
                    title=f"Assumption Notice: {check.assumption}",
                    description=check.evidence,
                    columns=target_columns,
                    method=method,
                    p_value=check.p_value,
                    evidence=check.evidence,
                    confidence=0.85,
                    limitations=[check.recommendation] if check.recommendation else [],
                )
            )

    # 3. Main statistical findings (group comparison / t-test / ANOVA / correlation / regression / chi-square)
    primary_p = p_values.get("primary") or statistics.get("p_value") or statistics.get("f_p_value")

    if primary_p is not None:
        is_significant = bool(primary_p < alpha)
        primary_effect = effect_sizes[0] if effect_sizes else None
        effect_val = primary_effect.get("value") if primary_effect else None
        effect_interp = primary_effect.get("interpretation", "unspecified") if primary_effect else None
        metric_name = primary_effect.get("metric_name", "effect") if primary_effect else "effect"

        if is_significant:
            severity = FindingSeverity.HIGH if effect_interp in ("medium", "large") else FindingSeverity.MEDIUM
            cat = FindingCategory.SIGNIFICANT_DIFFERENCE if "comparison" in analysis_type or "test" in method else FindingCategory.STRONG_ASSOCIATION

            # Distinguish practical vs statistical significance (STAT-42, STAT-66)
            if effect_interp == "negligible":
                title = "Statistically significant difference, but negligible practical effect size"
                desc = (
                    f"The test reached statistical significance at alpha={alpha} (p={round(primary_p, 4)}), "
                    f"however the measured effect ({metric_name} = {effect_val}) is classified as negligible. "
                    "In large samples, even trivial differences can achieve low p-values without practical importance."
                )
            else:
                title = f"Statistically significant difference detected with {effect_interp} effect ({metric_name}={effect_val})"
                desc = (
                    f"Evidence against the null hypothesis is statistically significant (p={round(primary_p, 4)} < {alpha}). "
                    f"The estimated effect magnitude is {effect_interp} ({metric_name} = {effect_val})."
                )

            findings.append(
                StatisticalFinding(
                    finding_id=f"find_sig_{uuid.uuid4().hex[:6]}",
                    category=cat,
                    severity=severity,
                    title=title,
                    description=desc,
                    columns=target_columns,
                    method=method,
                    statistics=statistics,
                    effect_size=primary_effect,
                    p_value=round(primary_p, 6),
                    evidence=f"p={round(primary_p, 6)}, test statistic={statistics.get('statistic')}, {metric_name}={effect_val}",
                    confidence=1.0,
                    limitations=[
                        "Statistical significance indicates evidence against the null model under test assumptions, not proof of causation."
                    ],
                )
            )
        else:
            findings.append(
                StatisticalFinding(
                    finding_id=f"find_nonsig_{uuid.uuid4().hex[:6]}",
                    category=FindingCategory.WEAK_ASSOCIATION,
                    severity=FindingSeverity.INFO,
                    title="No statistically significant difference observed",
                    description=(
                        f"The observed data is consistent with the null hypothesis at alpha={alpha} (p={round(primary_p, 4)} >= {alpha}). "
                        "There is insufficient statistical evidence to claim a true difference or association."
                    ),
                    columns=target_columns,
                    method=method,
                    statistics=statistics,
                    effect_size=primary_effect,
                    p_value=round(primary_p, 6),
                    evidence=f"p={round(primary_p, 6)} >= {alpha}",
                    confidence=0.9,
                    limitations=["Failure to reject null does not prove the null hypothesis is true (absence of evidence is not evidence of absence)."],
                )
            )

    # 4. Regression diagnostics findings
    if "ols" in method:
        diagnostics = statistics.get("diagnostics", {})
        bp = diagnostics.get("breusch_pagan", {})
        if bp.get("heteroscedasticity_concern"):
            findings.append(
                StatisticalFinding(
                    finding_id=f"find_bp_{uuid.uuid4().hex[:6]}",
                    category=FindingCategory.HETEROSCEDASTICITY,
                    severity=FindingSeverity.MEDIUM,
                    title="Potential heteroscedasticity detected (Breusch-Pagan test p < 0.05)",
                    description="Residual variance appears non-constant across fitted values. Standard errors and p-values may be somewhat biased.",
                    columns=target_columns,
                    method=method,
                    p_value=bp.get("p_value"),
                    evidence=f"Breusch-Pagan LM stat={bp.get('statistic')}, p={bp.get('p_value')}",
                    confidence=0.9,
                    limitations=["Consider robust standard errors (HC1/HC3) or log-transforming skewed variables."],
                )
            )

        vif = diagnostics.get("vif", {})
        high_vif = [k for k, v in vif.items() if v > 5.0]
        if high_vif:
            findings.append(
                StatisticalFinding(
                    finding_id=f"find_vif_{uuid.uuid4().hex[:6]}",
                    category=FindingCategory.MULTICOLLINEARITY,
                    severity=FindingSeverity.HIGH,
                    title=f"High multicollinearity in features: {', '.join(high_vif)}",
                    description="Features with VIF > 5 have inflated standard errors due to linear dependence on other predictors.",
                    columns=high_vif,
                    method=method,
                    evidence=f"VIF values: {', '.join(f'{k}={vif[k]}' for k in high_vif)}",
                    confidence=0.95,
                    limitations=["Collinear features should be consolidated, regularized, or selectively removed."],
                )
            )

    # Sort findings deterministically by severity priority
    sev_rank = {
        FindingSeverity.CRITICAL: 5,
        FindingSeverity.HIGH: 4,
        FindingSeverity.MEDIUM: 3,
        FindingSeverity.LOW: 2,
        FindingSeverity.INFO: 1,
    }
    findings.sort(key=lambda f: sev_rank.get(f.severity, 0), reverse=True)
    return findings
