"""
AnalyzaX — Phase 10: Categorical Association Engine
Implements Chi-Square Test of Independence with full contingency table decomposition
(observed, expected, standardized residuals, row/col percentages), Cramér's V,
sparse expected frequency warnings, and Fisher's Exact Test for 2x2 tables (STAT-20, STAT-21, STAT-24, STAT-25).
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats

from backend.app.engines.statistics.methods.effect_size import compute_cramers_v
from backend.app.engines.statistics.models import MissingDataReport


def run_categorical_association(
    var1_values: List[Any],
    var2_values: List[Any],
    var1_name: str,
    var2_name: str,
    alpha: float = 0.05,
    prefer_fisher: bool = False,
) -> Dict[str, Any]:
    """
    Computes contingency table, Chi-square test, and Fisher's exact test if 2x2.
    """
    total_obs = len(var1_values)
    clean_pairs = [
        (v1, v2) for v1, v2 in zip(var1_values, var2_values)
        if v1 is not None and v2 is not None and str(v1).strip() != "" and str(v2).strip() != ""
    ]
    used_obs = len(clean_pairs)
    excluded = total_obs - used_obs

    missing_report = MissingDataReport(
        original_observations=total_obs,
        used_observations=used_obs,
        excluded_observations=excluded,
        missing_policy="listwise_deletion",
        exclusion_reason="Null or empty categories excluded" if excluded > 0 else None,
    )

    if used_obs < 4:
        return {
            "status": "INSUFFICIENT_DATA",
            "missing_report": missing_report.model_dump(),
            "error": f"Categorical association requires at least 4 valid observation pairs (found {used_obs}).",
        }

    # Extract unique categories
    r_labels = sorted(list(set(str(p[0]) for p in clean_pairs)))
    c_labels = sorted(list(set(str(p[1]) for p in clean_pairs)))
    r_count = len(r_labels)
    c_count = len(c_labels)

    if r_count < 2 or c_count < 2:
        return {
            "status": "INSUFFICIENT_DATA",
            "missing_report": missing_report.model_dump(),
            "error": f"Both categorical variables must have at least 2 distinct levels (found {r_count} and {c_count}).",
        }

    # Construct contingency matrix
    r_map = {lbl: i for i, lbl in enumerate(r_labels)}
    c_map = {lbl: j for j, lbl in enumerate(c_labels)}
    contingency = np.zeros((r_count, c_count), dtype=int)

    for v1, v2 in clean_pairs:
        contingency[r_map[str(v1)], c_map[str(v2)]] += 1

    row_totals = contingency.sum(axis=1)
    col_totals = contingency.sum(axis=2 if contingency.ndim > 2 else 0)
    grand_total = float(used_obs)

    # Compute expected frequencies & standardized residuals
    expected = np.outer(row_totals, col_totals) / grand_total
    residuals = np.zeros_like(expected)
    cells_under_5 = 0
    cells_under_1 = 0

    for i in range(r_count):
        for j in range(c_count):
            exp_val = expected[i, j]
            if exp_val < 5.0:
                cells_under_5 += 1
            if exp_val < 1.0:
                cells_under_1 += 1
            if exp_val > 0:
                residuals[i, j] = (contingency[i, j] - exp_val) / math.sqrt(exp_val)

    total_cells = r_count * c_count
    pct_under_5 = round(cells_under_5 / total_cells * 100.0, 1)

    # Chi-square test
    chi2_stat, p_val, dof, _ = stats.chi2_contingency(contingency, correction=False)
    effect_v = compute_cramers_v(float(chi2_stat), used_obs, r_count, c_count)

    # Check 2x2 Fisher's Exact test
    fisher_res = None
    if r_count == 2 and c_count == 2:
        try:
            f_odds, f_pval = stats.fisher_exact(contingency)
            # Odds ratio 95% CI
            a, b = float(contingency[0, 0]), float(contingency[0, 1])
            c, d = float(contingency[1, 0]), float(contingency[1, 1])
            ci_odds = None
            if min(a, b, c, d) > 0 and f_odds > 0:
                se_ln_or = math.sqrt(1/a + 1/b + 1/c + 1/d)
                ln_or = math.log(f_odds)
                ci_odds = [
                    round(math.exp(ln_or - 1.96 * se_ln_or), 4),
                    round(math.exp(ln_or + 1.96 * se_ln_or), 4),
                ]

            fisher_res = {
                "odds_ratio": round(float(f_odds), 4),
                "p_value": round(float(f_pval), 6),
                "confidence_interval_95": ci_odds,
                "is_significant": bool(f_pval < alpha),
            }
        except Exception:
            fisher_res = None

    # Format detailed contingency table for presentation
    table_rows = []
    for i in range(r_count):
        row_cells = []
        r_tot = int(row_totals[i])
        for j in range(c_count):
            obs = int(contingency[i, j])
            exp = round(float(expected[i, j]), 2)
            res_val = round(float(residuals[i, j]), 2)
            row_pct = round((obs / r_tot * 100.0), 1) if r_tot > 0 else 0.0
            col_tot = int(col_totals[j])
            col_pct = round((obs / col_tot * 100.0), 1) if col_tot > 0 else 0.0

            row_cells.append({
                "column_category": c_labels[j],
                "observed": obs,
                "expected": exp,
                "residual": res_val,
                "row_percentage": row_pct,
                "column_percentage": col_pct,
            })

        table_rows.append({
            "row_category": r_labels[i],
            "cells": row_cells,
            "row_total": r_tot,
            "row_percentage_of_total": round(r_tot / grand_total * 100.0, 1),
        })

    column_summaries = [
        {
            "column_category": c_labels[j],
            "column_total": int(col_totals[j]),
            "column_percentage_of_total": round(int(col_totals[j]) / grand_total * 100.0, 1),
        }
        for j in range(c_count)
    ]

    warnings = []
    if pct_under_5 > 20.0 or cells_under_1 > 0:
        msg = f"Chi-square assumption warning: {pct_under_5}% of cells have expected frequency < 5 (Cochran's rule suggests < 20%)."
        if fisher_res:
            msg += " Fisher's exact test is recommended for exact inference."
        warnings.append(msg)

    decision = "Reject Null Hypothesis" if p_val < alpha else "Fail to Reject Null Hypothesis"

    return {
        "status": "COMPLETED",
        "method": "chi_square",
        "method_name": "Pearson's Chi-Square Test of Independence",
        "missing_report": missing_report.model_dump(),
        "null_hypothesis": f"{var1_name} and {var2_name} are statistically independent.",
        "alternative_hypothesis": f"{var1_name} and {var2_name} are not independent (associated).",
        "alpha": alpha,
        "statistic": round(float(chi2_stat), 4),
        "test_statistic_name": "Chi2",
        "degrees_of_freedom": dof,
        "p_value": round(float(p_val), 6),
        "decision": decision,
        "is_significant": bool(p_val < alpha),
        "contingency_table": {
            "row_variable": var1_name,
            "column_variable": var2_name,
            "row_categories": r_labels,
            "column_categories": c_labels,
            "rows": table_rows,
            "column_summaries": column_summaries,
            "grand_total": int(grand_total),
        },
        "sparsity_check": {
            "cells_under_5": cells_under_5,
            "cells_under_1": cells_under_1,
            "percentage_under_5": pct_under_5,
            "assumption_satisfied": bool(pct_under_5 <= 20.0 and cells_under_1 == 0),
        },
        "effect_sizes": [effect_v.model_dump()] if effect_v else [],
        "fisher_exact_test": fisher_res,
        "warnings": warnings,
    }
