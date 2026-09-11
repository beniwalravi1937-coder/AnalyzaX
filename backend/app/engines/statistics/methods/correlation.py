"""
AnalyzaX — Phase 10: Deterministic Correlation Engine
Computes Pearson, Spearman, and Kendall correlations with p-values, Fisher z CIs,
and pairwise correlation matrices. Handles constant/invalid variables safely (STAT-22 to STAT-26).
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats

from backend.app.engines.statistics.methods.confidence import compute_correlation_ci
from backend.app.engines.statistics.methods.effect_size import compute_pearson_r_effect_size
from backend.app.engines.statistics.models import MissingDataReport


def compute_bivariate_correlation(
    x: np.ndarray,
    y: np.ndarray,
    var_x_name: str,
    var_y_name: str,
    method: str = "pearson",
    confidence_level: float = 0.95,
    alpha: float = 0.05,
) -> Dict[str, Any]:
    """
    Computes Pearson, Spearman, or Kendall correlation between two variables.
    Handles constant variables and zero variance safely (STAT-26).
    """
    total_obs = len(x)
    valid_mask = ~np.isnan(x) & ~np.isinf(x) & ~np.isnan(y) & ~np.isinf(y)
    x_clean = x[valid_mask].astype(float)
    y_clean = y[valid_mask].astype(float)
    used_obs = len(x_clean)
    excluded = total_obs - used_obs

    missing_report = MissingDataReport(
        original_observations=total_obs,
        used_observations=used_obs,
        excluded_observations=excluded,
        missing_policy="pairwise_deletion",
        exclusion_reason="Missing/infinite pairs excluded" if excluded > 0 else None,
    )

    if used_obs < 3:
        return {
            "status": "INSUFFICIENT_DATA",
            "method": method,
            "missing_report": missing_report.model_dump(),
            "error": f"Correlation requires at least 3 valid pairs (found {used_obs}).",
            "is_valid": False,
        }

    std_x = float(np.std(x_clean, ddof=1))
    std_y = float(np.std(y_clean, ddof=1))

    if std_x == 0.0 or std_y == 0.0:
        constant_col = var_x_name if std_x == 0.0 else var_y_name
        return {
            "status": "CONSTANT_VARIABLE",
            "method": method,
            "missing_report": missing_report.model_dump(),
            "error": f"Variable '{constant_col}' has zero variance (constant). Correlation is mathematically undefined.",
            "is_valid": False,
            "r": None,
            "p_value": None,
        }

    try:
        if method.lower() == "spearman":
            res = stats.spearmanr(x_clean, y_clean)
            r_val = float(res.statistic)
            p_val = float(res.pvalue)
            ci = None
        elif method.lower() == "kendall":
            res = stats.kendalltau(x_clean, y_clean)
            r_val = float(res.statistic)
            p_val = float(res.pvalue)
            ci = None
        else:
            # Default Pearson
            method = "pearson"
            res = stats.pearsonr(x_clean, y_clean)
            r_val = float(res.statistic)
            p_val = float(res.pvalue)
            ci = compute_correlation_ci(r_val, used_obs, confidence_level=confidence_level)

        effect = compute_pearson_r_effect_size(r_val)

        return {
            "status": "COMPLETED",
            "method": method,
            "variable_x": var_x_name,
            "variable_y": var_y_name,
            "missing_report": missing_report.model_dump(),
            "coefficient": round(r_val, 4),
            "p_value": round(p_val, 6),
            "is_significant": bool(p_val < alpha),
            "alpha": alpha,
            "sample_size": used_obs,
            "confidence_interval": ci.model_dump() if ci else None,
            "effect_size": effect.model_dump(),
            "is_valid": True,
        }
    except Exception as e:
        return {
            "status": "NUMERICAL_FAILURE",
            "method": method,
            "missing_report": missing_report.model_dump(),
            "error": f"Correlation calculation failed: {str(e)}",
            "is_valid": False,
        }


def compute_correlation_matrix(
    data: Dict[str, np.ndarray],
    method: str = "pearson",
    alpha: float = 0.05,
    max_columns: int = 50,
) -> Dict[str, Any]:
    """
    Computes pairwise correlation matrix across multiple numeric variables.
    Satisfies STAT-24, STAT-25, STAT-26.
    """
    cols = list(data.keys())[:max_columns]
    n_cols = len(cols)
    matrix = []
    ranked_pairs = []

    for i, col_a in enumerate(cols):
        row = []
        for j, col_b in enumerate(cols):
            if i == j:
                row.append({"r": 1.0, "p_value": 0.0, "sample_size": len(data[col_a]), "is_valid": True})
            else:
                res = compute_bivariate_correlation(
                    data[col_a],
                    data[col_b],
                    col_a,
                    col_b,
                    method=method,
                    alpha=alpha,
                )
                if res.get("is_valid", False):
                    r_val = res["coefficient"]
                    p_val = res["p_value"]
                    row.append({
                        "r": r_val,
                        "p_value": p_val,
                        "sample_size": res["sample_size"],
                        "is_valid": True,
                    })
                    if i < j:
                        ranked_pairs.append({
                            "var1": col_a,
                            "var2": col_b,
                            "r": r_val,
                            "abs_r": abs(r_val),
                            "p_value": p_val,
                            "is_significant": res["is_significant"],
                            "sample_size": res["sample_size"],
                        })
                else:
                    row.append({
                        "r": None,
                        "p_value": None,
                        "error": res.get("error", "Undefined"),
                        "is_valid": False,
                    })
        matrix.append(row)

    # Sort ranked pairs by absolute correlation strength descending
    ranked_pairs.sort(key=lambda x: x["abs_r"], reverse=True)

    return {
        "columns": cols,
        "method": method,
        "matrix": matrix,
        "ranked_pairs": ranked_pairs,
    }
