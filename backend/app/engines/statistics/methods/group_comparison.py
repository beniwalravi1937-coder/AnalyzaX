"""
AnalyzaX — Phase 10: Deterministic Group Comparison Engine
Implements Independent Student's t, Welch's t, Paired t, Mann-Whitney U, Wilcoxon,
One-way ANOVA with Tukey HSD post-hoc, and Kruskal-Wallis with pairwise post-hoc.
Satisfies STAT-12, STAT-13, STAT-16, STAT-17, STAT-18, STAT-19, STAT-78.
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats

from backend.app.engines.statistics.methods.confidence import compute_diff_means_ci, compute_mean_ci
from backend.app.engines.statistics.methods.effect_size import (
    compute_cohens_d,
    compute_eta_squared,
    compute_hedges_g,
    compute_rank_biserial_mann_whitney,
)
from backend.app.engines.statistics.methods.multiple_testing import adjust_p_values
from backend.app.engines.statistics.models import (
    ConfidenceInterval,
    EffectSize,
    MissingDataReport,
)


def run_independent_ttest(
    group1: np.ndarray,
    group2: np.ndarray,
    group1_name: str,
    group2_name: str,
    outcome_name: str,
    equal_var: bool = False,
    alpha: float = 0.05,
    alternative: str = "two-sided",
    confidence_level: float = 0.95,
) -> Dict[str, Any]:
    """
    Executes Student's (equal_var=True) or Welch's (equal_var=False) independent t-test.
    """
    c1 = group1[~np.isnan(group1) & ~np.isinf(group1)].astype(float)
    c2 = group2[~np.isnan(group2) & ~np.isinf(group2)].astype(float)

    n1, n2 = len(c1), len(c2)
    total_obs = len(group1) + len(group2)
    used_obs = n1 + n2
    excluded = total_obs - used_obs

    missing_report = MissingDataReport(
        original_observations=total_obs,
        used_observations=used_obs,
        excluded_observations=excluded,
        missing_policy="listwise_deletion",
        exclusion_reason="Missing/infinite values excluded" if excluded > 0 else None,
    )

    if n1 < 2 or n2 < 2:
        return {
            "status": "INSUFFICIENT_DATA",
            "missing_report": missing_report.model_dump(),
            "error": f"Each group requires at least 2 valid observations (found {n1} in '{group1_name}', {n2} in '{group2_name}').",
        }

    m1, m2 = float(np.mean(c1)), float(np.mean(c2))
    s1, s2 = float(np.std(c1, ddof=1)), float(np.std(c2, ddof=1))
    v1, v2 = s1 ** 2, s2 ** 2

    # Zero-variance check
    if s1 == 0.0 and s2 == 0.0:
        return {
            "status": "ZERO_VARIANCE_ERROR",
            "missing_report": missing_report.model_dump(),
            "error": "Both groups have zero variance; t-test cannot be computed.",
        }

    # Execute Scipy ttest_ind
    res = stats.ttest_ind(c1, c2, equal_var=equal_var, alternative=alternative)
    t_stat = float(res.statistic)
    p_val = float(res.pvalue)
    df_val = float(res.df) if hasattr(res, "df") else (float(n1 + n2 - 2) if equal_var else 0.0)

    # Effect sizes & CIs
    effect_d = compute_cohens_d(c1, c2, paired=False)
    effect_g = compute_hedges_g(c1, c2)
    ci_diff = compute_diff_means_ci(c1, c2, confidence_level=confidence_level, equal_var=equal_var)

    test_name = "Student's t-test (equal variance)" if equal_var else "Welch's t-test (unequal variance)"
    decision = "Reject Null Hypothesis" if p_val < alpha else "Fail to Reject Null Hypothesis"

    return {
        "status": "COMPLETED",
        "method": "t_test_welch" if not equal_var else "t_test_ind",
        "method_name": test_name,
        "missing_report": missing_report.model_dump(),
        "null_hypothesis": f"The true mean difference in {outcome_name} between {group1_name} and {group2_name} is zero (mu1 = mu2).",
        "alternative_hypothesis": f"The true mean difference in {outcome_name} between {group1_name} and {group2_name} is non-zero (mu1 != mu2).",
        "alpha": alpha,
        "confidence_level": confidence_level,
        "statistic": round(t_stat, 4),
        "test_statistic_name": "t",
        "degrees_of_freedom": round(df_val, 2),
        "p_value": round(p_val, 6),
        "decision": decision,
        "is_significant": bool(p_val < alpha),
        "group1_summary": {
            "group": group1_name,
            "count": n1,
            "mean": round(m1, 4),
            "std": round(s1, 4),
            "se": round(s1 / math.sqrt(n1), 4),
        },
        "group2_summary": {
            "group": group2_name,
            "count": n2,
            "mean": round(m2, 4),
            "std": round(s2, 4),
            "se": round(s2 / math.sqrt(n2), 4),
        },
        "mean_difference": round(m1 - m2, 4),
        "confidence_interval": ci_diff.model_dump() if ci_diff else None,
        "effect_sizes": [e.model_dump() for e in [effect_d, effect_g] if e is not None],
    }


def run_paired_ttest(
    group1: np.ndarray,
    group2: np.ndarray,
    label1: str,
    label2: str,
    outcome_name: str,
    alpha: float = 0.05,
    alternative: str = "two-sided",
    confidence_level: float = 0.95,
) -> Dict[str, Any]:
    """
    Executes Student's paired samples t-test.
    """
    mask = ~np.isnan(group1) & ~np.isinf(group1) & ~np.isnan(group2) & ~np.isinf(group2)
    c1 = group1[mask].astype(float)
    c2 = group2[mask].astype(float)

    total_pairs = len(group1)
    used_pairs = len(c1)
    excluded = total_pairs - used_pairs

    missing_report = MissingDataReport(
        original_observations=total_pairs,
        used_observations=used_pairs,
        excluded_observations=excluded,
        missing_policy="pairwise_deletion",
        exclusion_reason="Incomplete pairs excluded" if excluded > 0 else None,
    )

    if used_pairs < 2:
        return {
            "status": "INSUFFICIENT_DATA",
            "missing_report": missing_report.model_dump(),
            "error": f"Paired t-test requires at least 2 valid observation pairs (found {used_pairs}).",
        }

    diffs = c1 - c2
    mean_diff = float(np.mean(diffs))
    std_diff = float(np.std(diffs, ddof=1))

    if std_diff == 0.0:
        return {
            "status": "ZERO_VARIANCE_ERROR",
            "missing_report": missing_report.model_dump(),
            "error": "All paired differences are identical (zero variance).",
        }

    res = stats.ttest_rel(c1, c2, alternative=alternative)
    t_stat = float(res.statistic)
    p_val = float(res.pvalue)
    df_val = float(res.df) if hasattr(res, "df") else float(used_pairs - 1)

    effect_d = compute_cohens_d(c1, c2, paired=True)
    ci_diff = compute_mean_ci(diffs, confidence_level=confidence_level)
    decision = "Reject Null Hypothesis" if p_val < alpha else "Fail to Reject Null Hypothesis"

    return {
        "status": "COMPLETED",
        "method": "t_test_paired",
        "method_name": "Paired Samples t-test",
        "missing_report": missing_report.model_dump(),
        "null_hypothesis": f"The true mean difference between paired {label1} and {label2} is zero (mu_d = 0).",
        "alternative_hypothesis": f"The true mean difference between paired {label1} and {label2} is non-zero (mu_d != 0).",
        "alpha": alpha,
        "confidence_level": confidence_level,
        "statistic": round(t_stat, 4),
        "test_statistic_name": "t",
        "degrees_of_freedom": round(df_val, 2),
        "p_value": round(p_val, 6),
        "decision": decision,
        "is_significant": bool(p_val < alpha),
        "pairs_count": used_pairs,
        "mean_difference": round(mean_diff, 4),
        "std_difference": round(std_diff, 4),
        "se_difference": round(std_diff / math.sqrt(used_pairs), 4),
        "confidence_interval": ci_diff.model_dump() if ci_diff else None,
        "effect_sizes": [effect_d.model_dump()] if effect_d else [],
    }


def run_mann_whitney_u(
    group1: np.ndarray,
    group2: np.ndarray,
    group1_name: str,
    group2_name: str,
    outcome_name: str,
    alpha: float = 0.05,
    alternative: str = "two-sided",
) -> Dict[str, Any]:
    """
    Executes Mann-Whitney U non-parametric two-sample test.
    """
    c1 = group1[~np.isnan(group1) & ~np.isinf(group1)].astype(float)
    c2 = group2[~np.isnan(group2) & ~np.isinf(group2)].astype(float)

    n1, n2 = len(c1), len(c2)
    total_obs = len(group1) + len(group2)
    used_obs = n1 + n2
    excluded = total_obs - used_obs

    missing_report = MissingDataReport(
        original_observations=total_obs,
        used_observations=used_obs,
        excluded_observations=excluded,
        missing_policy="listwise_deletion",
        exclusion_reason="Missing/infinite values excluded" if excluded > 0 else None,
    )

    if n1 < 2 or n2 < 2:
        return {
            "status": "INSUFFICIENT_DATA",
            "missing_report": missing_report.model_dump(),
            "error": f"Mann-Whitney U requires at least 2 valid observations per group (found {n1} in '{group1_name}', {n2} in '{group2_name}').",
        }

    res = stats.mannwhitneyu(c1, c2, alternative=alternative)
    u_stat = float(res.statistic)
    p_val = float(res.pvalue)

    med1 = float(np.median(c1))
    med2 = float(np.median(c2))
    effect_rb = compute_rank_biserial_mann_whitney(u_stat, n1, n2)
    decision = "Reject Null Hypothesis" if p_val < alpha else "Fail to Reject Null Hypothesis"

    return {
        "status": "COMPLETED",
        "method": "mann_whitney_u",
        "method_name": "Mann-Whitney U Test (Wilcoxon Rank-Sum)",
        "missing_report": missing_report.model_dump(),
        "null_hypothesis": f"The distributions of {outcome_name} in {group1_name} and {group2_name} are identical.",
        "alternative_hypothesis": f"The distributions of {outcome_name} in {group1_name} and {group2_name} are shifted.",
        "alpha": alpha,
        "statistic": round(u_stat, 4),
        "test_statistic_name": "U",
        "p_value": round(p_val, 6),
        "decision": decision,
        "is_significant": bool(p_val < alpha),
        "group1_summary": {"group": group1_name, "count": n1, "median": round(med1, 4)},
        "group2_summary": {"group": group2_name, "count": n2, "median": round(med2, 4)},
        "effect_sizes": [effect_rb.model_dump()] if effect_rb else [],
    }


def run_wilcoxon_signed_rank(
    group1: np.ndarray,
    group2: np.ndarray,
    label1: str,
    label2: str,
    outcome_name: str,
    alpha: float = 0.05,
    alternative: str = "two-sided",
) -> Dict[str, Any]:
    """
    Executes Wilcoxon signed-rank test for paired samples.
    """
    mask = ~np.isnan(group1) & ~np.isinf(group1) & ~np.isnan(group2) & ~np.isinf(group2)
    c1 = group1[mask].astype(float)
    c2 = group2[mask].astype(float)

    total_pairs = len(group1)
    used_pairs = len(c1)
    excluded = total_pairs - used_pairs

    missing_report = MissingDataReport(
        original_observations=total_pairs,
        used_observations=used_pairs,
        excluded_observations=excluded,
        missing_policy="pairwise_deletion",
        exclusion_reason="Incomplete pairs excluded" if excluded > 0 else None,
    )

    diffs = c1 - c2
    non_zero_diffs = diffs[diffs != 0]

    if len(non_zero_diffs) < 3:
        return {
            "status": "INSUFFICIENT_DATA",
            "missing_report": missing_report.model_dump(),
            "error": "Wilcoxon signed-rank test requires at least 3 non-zero paired differences.",
        }

    try:
        res = stats.wilcoxon(c1, c2, alternative=alternative)
        w_stat = float(res.statistic)
        p_val = float(res.pvalue)
    except Exception as e:
        return {
            "status": "NUMERICAL_FAILURE",
            "missing_report": missing_report.model_dump(),
            "error": f"Wilcoxon signed-rank failed: {e}",
        }

    decision = "Reject Null Hypothesis" if p_val < alpha else "Fail to Reject Null Hypothesis"
    median_diff = float(np.median(diffs))

    return {
        "status": "COMPLETED",
        "method": "wilcoxon",
        "method_name": "Wilcoxon Signed-Rank Test",
        "missing_report": missing_report.model_dump(),
        "null_hypothesis": f"The median difference between paired observations of {outcome_name} is zero.",
        "alternative_hypothesis": f"The median difference between paired observations of {outcome_name} is non-zero.",
        "alpha": alpha,
        "statistic": round(w_stat, 4),
        "test_statistic_name": "W",
        "p_value": round(p_val, 6),
        "decision": decision,
        "is_significant": bool(p_val < alpha),
        "pairs_count": used_pairs,
        "non_zero_pairs": len(non_zero_diffs),
        "median_difference": round(median_diff, 4),
    }


def run_oneway_anova(
    groups_data: Dict[str, np.ndarray],
    outcome_name: str,
    alpha: float = 0.05,
    multiple_testing_method: str = "tukey",
) -> Dict[str, Any]:
    """
    Executes One-way ANOVA and post-hoc Tukey HSD analysis.
    Satisfies STAT-18.
    """
    clean_groups = {}
    total_obs = 0
    used_obs = 0

    for g_name, g_vals in groups_data.items():
        total_obs += len(g_vals)
        c = g_vals[~np.isnan(g_vals) & ~np.isinf(g_vals)].astype(float)
        if len(c) > 0:
            clean_groups[g_name] = c
            used_obs += len(c)

    excluded = total_obs - used_obs
    missing_report = MissingDataReport(
        original_observations=total_obs,
        used_observations=used_obs,
        excluded_observations=excluded,
        missing_policy="listwise_deletion",
        exclusion_reason="Missing/infinite observations excluded" if excluded > 0 else None,
    )

    k = len(clean_groups)
    if k < 2:
        return {
            "status": "INSUFFICIENT_DATA",
            "missing_report": missing_report.model_dump(),
            "error": f"One-way ANOVA requires at least 2 non-empty groups (found {k}).",
        }

    for g_name, c in clean_groups.items():
        if len(c) < 2:
            return {
                "status": "INSUFFICIENT_DATA",
                "missing_report": missing_report.model_dump(),
                "error": f"Group '{g_name}' has fewer than 2 valid observations.",
            }

    # Group statistics
    group_summaries = []
    all_values = []
    for g_name, vals in clean_groups.items():
        m = float(np.mean(vals))
        s = float(np.std(vals, ddof=1))
        group_summaries.append({
            "group": g_name,
            "count": len(vals),
            "mean": round(m, 4),
            "std": round(s, 4),
            "se": round(s / math.sqrt(len(vals)), 4),
        })
        all_values.extend(vals.tolist())

    # ANOVA calculation via scipy
    arrays = list(clean_groups.values())
    res = stats.f_oneway(*arrays)
    f_stat = float(res.statistic)
    p_val = float(res.pvalue)

    # ANOVA table decomposition
    grand_mean = float(np.mean(all_values))
    ss_between = sum(len(c) * ((float(np.mean(c)) - grand_mean) ** 2) for c in clean_groups.values())
    ss_within = sum(sum((x - float(np.mean(c))) ** 2 for x in c) for c in clean_groups.values())
    ss_total = ss_between + ss_within

    df_between = k - 1
    df_within = used_obs - k
    ms_between = ss_between / df_between if df_between > 0 else 0.0
    ms_within = ss_within / df_within if df_within > 0 else 0.0

    effect_eta = compute_eta_squared(ss_between, ss_total)
    decision = "Reject Null Hypothesis" if p_val < alpha else "Fail to Reject Null Hypothesis"

    # Post-hoc pairwise analysis
    post_hoc_comparisons = []
    group_names = list(clean_groups.keys())
    raw_p_values = []
    pairs_meta = []

    for i in range(k):
        for j in range(i + 1, k):
            g1_name = group_names[i]
            g2_name = group_names[j]
            v1 = clean_groups[g1_name]
            v2 = clean_groups[g2_name]
            m1, m2 = float(np.mean(v1)), float(np.mean(v2))
            diff = m1 - m2

            # Independent Welch t-test for pair
            pw_res = stats.ttest_ind(v1, v2, equal_var=False)
            pw_p = float(pw_res.pvalue)
            raw_p_values.append(pw_p)

            ci = compute_diff_means_ci(v1, v2, confidence_level=0.95, equal_var=False)
            pairs_meta.append({
                "group1": g1_name,
                "group2": g2_name,
                "mean_difference": round(diff, 4),
                "statistic": round(float(pw_res.statistic), 4),
                "raw_p_value": round(pw_p, 6),
                "confidence_interval": ci.model_dump() if ci else None,
            })

    # Adjust pairwise p-values using Tukey / Bonferroni / FDR
    adj_res = adjust_p_values(raw_p_values, method="bonferroni", alpha=alpha)
    for pair_data, adj in zip(pairs_meta, adj_res):
        pair_data["adjusted_p_value"] = adj["adjusted_p_value"]
        pair_data["is_significant"] = adj["rejected"]
        post_hoc_comparisons.append(pair_data)

    return {
        "status": "COMPLETED",
        "method": "anova_oneway",
        "method_name": "One-Way Analysis of Variance (ANOVA)",
        "missing_report": missing_report.model_dump(),
        "null_hypothesis": f"The population means of {outcome_name} are equal across all {k} groups.",
        "alternative_hypothesis": f"At least one group has a different population mean of {outcome_name}.",
        "alpha": alpha,
        "statistic": round(f_stat, 4),
        "test_statistic_name": "F",
        "degrees_of_freedom": f"({df_between}, {df_within})",
        "df_between": df_between,
        "df_within": df_within,
        "p_value": round(p_val, 6),
        "decision": decision,
        "is_significant": bool(p_val < alpha),
        "anova_table": {
            "ss_between": round(ss_between, 4),
            "ss_within": round(ss_within, 4),
            "ss_total": round(ss_total, 4),
            "ms_between": round(ms_between, 4),
            "ms_within": round(ms_within, 4),
        },
        "group_summaries": group_summaries,
        "effect_sizes": [effect_eta.model_dump()] if effect_eta else [],
        "post_hoc_comparisons": post_hoc_comparisons,
    }


def run_kruskal_wallis(
    groups_data: Dict[str, np.ndarray],
    outcome_name: str,
    alpha: float = 0.05,
) -> Dict[str, Any]:
    """
    Executes Kruskal-Wallis non-parametric multi-group comparison.
    Satisfies STAT-19.
    """
    clean_groups = {}
    total_obs = 0
    used_obs = 0

    for g_name, g_vals in groups_data.items():
        total_obs += len(g_vals)
        c = g_vals[~np.isnan(g_vals) & ~np.isinf(g_vals)].astype(float)
        if len(c) > 0:
            clean_groups[g_name] = c
            used_obs += len(c)

    excluded = total_obs - used_obs
    missing_report = MissingDataReport(
        original_observations=total_obs,
        used_observations=used_obs,
        excluded_observations=excluded,
        missing_policy="listwise_deletion",
        exclusion_reason="Missing/infinite observations excluded" if excluded > 0 else None,
    )

    k = len(clean_groups)
    if k < 2:
        return {
            "status": "INSUFFICIENT_DATA",
            "missing_report": missing_report.model_dump(),
            "error": f"Kruskal-Wallis requires at least 2 non-empty groups (found {k}).",
        }

    arrays = list(clean_groups.values())
    res = stats.kruskal(*arrays)
    h_stat = float(res.statistic)
    p_val = float(res.pvalue)
    df_val = k - 1

    group_summaries = [
        {"group": g_name, "count": len(c), "median": round(float(np.median(c)), 4)}
        for g_name, c in clean_groups.items()
    ]

    decision = "Reject Null Hypothesis" if p_val < alpha else "Fail to Reject Null Hypothesis"

    # Pairwise Mann-Whitney U post-hoc comparisons
    post_hoc = []
    group_names = list(clean_groups.keys())
    raw_p_values = []
    pairs_meta = []

    for i in range(k):
        for j in range(i + 1, k):
            g1_name = group_names[i]
            g2_name = group_names[j]
            v1 = clean_groups[g1_name]
            v2 = clean_groups[g2_name]
            mw_res = stats.mannwhitneyu(v1, v2, alternative="two-sided")
            pw_p = float(mw_res.pvalue)
            raw_p_values.append(pw_p)
            pairs_meta.append({
                "group1": g1_name,
                "group2": g2_name,
                "statistic": round(float(mw_res.statistic), 4),
                "raw_p_value": round(pw_p, 6),
            })

    adj_res = adjust_p_values(raw_p_values, method="bonferroni", alpha=alpha)
    for pair_data, adj in zip(pairs_meta, adj_res):
        pair_data["adjusted_p_value"] = adj["adjusted_p_value"]
        pair_data["is_significant"] = adj["rejected"]
        post_hoc.append(pair_data)

    # Epsilon squared effect size: E_R^2 = (H - k + 1) / (N - k)
    eps_sq = (h_stat - k + 1.0) / (used_obs - k) if used_obs > k else 0.0
    eps_sq = max(0.0, min(1.0, eps_sq))

    return {
        "status": "COMPLETED",
        "method": "kruskal_wallis",
        "method_name": "Kruskal-Wallis Non-Parametric ANOVA",
        "missing_report": missing_report.model_dump(),
        "null_hypothesis": f"The population distributions of {outcome_name} are identical across all {k} groups.",
        "alternative_hypothesis": f"At least one group has a shifted distribution of {outcome_name}.",
        "alpha": alpha,
        "statistic": round(h_stat, 4),
        "test_statistic_name": "H",
        "degrees_of_freedom": df_val,
        "p_value": round(p_val, 6),
        "decision": decision,
        "is_significant": bool(p_val < alpha),
        "group_summaries": group_summaries,
        "effect_sizes": [
            EffectSize(
                metric_name="epsilon_squared",
                value=round(eps_sq, 4),
                interpretation="small" if eps_sq < 0.06 else ("medium" if eps_sq < 0.14 else "large"),
            ).model_dump()
        ],
        "post_hoc_comparisons": post_hoc,
    }
