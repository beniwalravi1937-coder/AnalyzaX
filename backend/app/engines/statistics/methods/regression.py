"""
AnalyzaX — Phase 10: Inferential Linear Regression Engine
Implements Simple and Multiple OLS regression with full coefficient tables (beta, SE, t, p, 95% CI),
model metrics (R2, adj R2, F-stat), VIF multicollinearity, Breusch-Pagan heteroscedasticity,
Durbin-Watson autocorrelation, Cook's distance influence diagnostics, and residual normality (STAT-26 to STAT-34).
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats

from backend.app.engines.statistics.models import MissingDataReport


def run_ols_regression(
    y: np.ndarray,
    X: np.ndarray,
    y_name: str,
    x_names: List[str],
    confidence_level: float = 0.95,
    alpha: float = 0.05,
) -> Dict[str, Any]:
    """
    Computes deterministic OLS linear regression and comprehensive diagnostic statistics.
    """
    total_obs = len(y)
    p_features = len(x_names)

    # 1. Clean missing/infinite values across y and all X columns
    valid_mask = ~np.isnan(y) & ~np.isinf(y)
    for j in range(X.shape[1]):
        valid_mask &= ~np.isnan(X[:, j]) & ~np.isinf(X[:, j])

    y_clean = y[valid_mask].astype(float)
    X_clean = X[valid_mask].astype(float)
    n = len(y_clean)
    excluded = total_obs - n

    missing_report = MissingDataReport(
        original_observations=total_obs,
        used_observations=n,
        excluded_observations=excluded,
        missing_policy="listwise_deletion",
        exclusion_reason="Rows with missing/infinite values in dependent or independent variables excluded" if excluded > 0 else None,
    )

    p_params = p_features + 1  # features + intercept
    if n <= p_params:
        return {
            "status": "INSUFFICIENT_DATA",
            "missing_report": missing_report.model_dump(),
            "error": f"Regression requires more observations than parameters (n={n}, parameters={p_params}).",
        }

    # Check for constant dependent variable
    std_y = float(np.std(y_clean, ddof=1))
    if std_y == 0.0 or math.isclose(std_y, 0.0):
        return {
            "status": "ZERO_VARIANCE_ERROR",
            "missing_report": missing_report.model_dump(),
            "error": f"Dependent variable '{y_name}' is constant (zero variance). OLS cannot be fit.",
        }

    # Check for zero-variance independent variables
    for j, name in enumerate(x_names):
        std_xj = float(np.std(X_clean[:, j], ddof=1))
        if std_xj == 0.0 or math.isclose(std_xj, 0.0):
            return {
                "status": "CONSTANT_VARIABLE",
                "missing_report": missing_report.model_dump(),
                "error": f"Independent variable '{name}' has zero variance (constant).",
            }

    # 2. Construct design matrix X_mat with intercept column
    intercept_col = np.ones((n, 1), dtype=float)
    X_design = np.hstack([intercept_col, X_clean])

    # 3. Check for singular or collinear design matrix
    try:
        XtX = np.dot(X_design.T, X_design)
        cond_num = np.linalg.cond(XtX)
        if cond_num > 1e12 or np.linalg.matrix_rank(X_design) < p_params:
            return {
                "status": "SINGULAR_MATRIX_ERROR",
                "missing_report": missing_report.model_dump(),
                "error": "Design matrix is singular or exhibits exact collinearity. Check for redundant variables.",
            }
        inv_XtX = np.linalg.inv(XtX)
    except Exception as e:
        return {
            "status": "SINGULAR_MATRIX_ERROR",
            "missing_report": missing_report.model_dump(),
            "error": f"Matrix inversion failed: {e}",
        }

    # 4. Coefficients beta = (X'X)^(-1) X'y
    XtY = np.dot(X_design.T, y_clean)
    beta = np.dot(inv_XtX, XtY)

    # 5. Fitted values & Residuals
    y_fitted = np.dot(X_design, beta)
    residuals = y_clean - y_fitted
    ss_res = float(np.sum(residuals ** 2))
    y_mean = float(np.mean(y_clean))
    ss_tot = float(np.sum((y_clean - y_mean) ** 2))
    ss_reg = max(0.0, ss_tot - ss_res)

    df_resid = n - p_params
    df_model = p_features
    sigma2 = ss_res / df_resid if df_resid > 0 else 0.0
    se_regression = math.sqrt(sigma2) if sigma2 > 0 else 0.0

    # 6. Coefficient Variance-Covariance matrix & Standard Errors
    cov_beta = sigma2 * inv_XtX
    se_beta = np.sqrt(np.maximum(0.0, np.diag(cov_beta)))

    # t-statistics, p-values, and confidence intervals
    t_crit = float(stats.t.ppf(1.0 - (1.0 - confidence_level) / 2.0, df_resid))
    coeff_table = []
    param_names = ["Intercept"] + x_names

    for idx, name in enumerate(param_names):
        b = float(beta[idx])
        se = float(se_beta[idx])
        if se > 0:
            t_stat = b / se
            p_val = 2.0 * (1.0 - float(stats.t.cdf(abs(t_stat), df_resid)))
        else:
            t_stat = 0.0
            p_val = 1.0

        ci_lower = b - t_crit * se
        ci_upper = b + t_crit * se

        coeff_table.append({
            "parameter": name,
            "coefficient": round(b, 4),
            "standard_error": round(se, 4),
            "t_statistic": round(t_stat, 4),
            "p_value": round(p_val, 6),
            "confidence_interval": [round(ci_lower, 4), round(ci_upper, 4)],
            "is_significant": bool(p_val < alpha),
        })

    # 7. Model-level metrics: R2, adj R2, F-statistic
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    r_squared = max(0.0, min(1.0, r_squared))
    adj_r_squared = 1.0 - ((1.0 - r_squared) * (n - 1) / df_resid) if df_resid > 0 else 0.0
    adj_r_squared = max(0.0, min(1.0, adj_r_squared))

    if ss_res > 0 and df_resid > 0:
        f_stat = (ss_reg / df_model) / (ss_res / df_resid)
        f_p_val = 1.0 - float(stats.f.cdf(f_stat, df_model, df_resid))
    else:
        f_stat = 0.0
        f_p_val = 1.0

    # Log-likelihood, AIC, BIC
    log_lik = -0.5 * n * (math.log(2.0 * math.pi) + math.log(max(sigma2, 1e-12)) + 1.0)
    aic = 2.0 * p_params - 2.0 * log_lik
    bic = math.log(n) * p_params - 2.0 * log_lik

    # 8. Diagnostics: Leverage, Standardized Residuals, Cook's Distance
    # Hat matrix diagonal: h_ii = diag(X (X'X)^(-1) X')
    h_diag = np.sum(X_design * np.dot(X_design, inv_XtX), axis=1)
    std_residuals = np.zeros(n)
    cooks_d = np.zeros(n)

    for i in range(n):
        h_i = min(0.999, float(h_diag[i]))
        denom = se_regression * math.sqrt(1.0 - h_i) if se_regression > 0 else 1.0
        r_i = float(residuals[i]) / max(denom, 1e-12)
        std_residuals[i] = r_i
        cooks_d[i] = (r_i ** 2 / p_params) * (h_i / (1.0 - h_i))

    cooks_threshold = 4.0 / n
    influential_points_count = int(np.sum(cooks_d > cooks_threshold))

    # 9. Multicollinearity: Variance Inflation Factors (VIF)
    vif_results = {}
    has_multicollinearity_concern = False
    if p_features > 1:
        for j, name in enumerate(x_names):
            xj = X_clean[:, j]
            other_X = np.delete(X_clean, j, axis=1)
            other_design = np.hstack([intercept_col, other_X])
            try:
                inv_other = np.linalg.inv(np.dot(other_design.T, other_design))
                b_aux = np.dot(inv_other, np.dot(other_design.T, xj))
                y_aux_fitted = np.dot(other_design, b_aux)
                ss_aux_res = np.sum((xj - y_aux_fitted) ** 2)
                ss_aux_tot = np.sum((xj - np.mean(xj)) ** 2)
                r2_aux = 1.0 - (ss_aux_res / ss_aux_tot) if ss_aux_tot > 0 else 0.0
                r2_aux = max(0.0, min(0.9999, r2_aux))
                vif_val = 1.0 / (1.0 - r2_aux)
            except Exception:
                vif_val = 1.0

            vif_results[name] = round(float(vif_val), 2)
            if vif_val > 5.0:
                has_multicollinearity_concern = True

    # 10. Heteroscedasticity: Breusch-Pagan Test
    # Regress e_i^2 on X_clean
    e2 = residuals ** 2
    try:
        b_bp = np.dot(inv_XtX, np.dot(X_design.T, e2))
        e2_fitted = np.dot(X_design, b_bp)
        ss_bp_res = np.sum((e2 - e2_fitted) ** 2)
        ss_bp_tot = np.sum((e2 - np.mean(e2)) ** 2)
        r2_bp = 1.0 - (ss_bp_res / ss_bp_tot) if ss_bp_tot > 0 else 0.0
        bp_lm_stat = float(n * r2_bp)
        bp_p_val = 1.0 - float(stats.chi2.cdf(bp_lm_stat, p_features))
        bp_res = {
            "statistic": round(bp_lm_stat, 4),
            "p_value": round(bp_p_val, 6),
            "heteroscedasticity_concern": bool(bp_p_val < 0.05),
        }
    except Exception:
        bp_res = {"statistic": 0.0, "p_value": 1.0, "heteroscedasticity_concern": False}

    # 11. Autocorrelation: Durbin-Watson Statistic
    diff_res = np.diff(residuals)
    sum_e2 = np.sum(residuals ** 2)
    dw_stat = float(np.sum(diff_res ** 2) / sum_e2) if sum_e2 > 0 else 2.0
    dw_concern = bool(dw_stat < 1.5 or dw_stat > 2.5)

    # 12. Normality of Residuals (Shapiro-Wilk or D'Agostino)
    shapiro_sample = residuals[:min(n, 5000)]
    try:
        sh_stat, sh_pval = stats.shapiro(shapiro_sample)
        res_normality = {
            "test": "Shapiro-Wilk",
            "statistic": round(float(sh_stat), 4),
            "p_value": round(float(sh_pval), 6),
            "normal_residuals": bool(sh_pval >= 0.05),
        }
    except Exception:
        res_normality = {"test": "Shapiro-Wilk", "statistic": 1.0, "p_value": 1.0, "normal_residuals": True}

    # 13. Subsampled points for plotting (Residual vs Fitted & Q-Q)
    plot_points_count = min(150, n)
    step = max(1, n // plot_points_count)
    sampled_indices = list(range(0, n, step))

    scatter_fitted = []
    residual_points = []
    for idx in sampled_indices:
        scatter_fitted.append({
            "fitted": round(float(y_fitted[idx]), 4),
            "actual": round(float(y_clean[idx]), 4),
            "residual": round(float(residuals[idx]), 4),
            "standardized_residual": round(float(std_residuals[idx]), 4),
            "leverage": round(float(h_diag[idx]), 4),
            "cooks_distance": round(float(cooks_d[idx]), 4),
        })
        residual_points.append({
            "fitted": round(float(y_fitted[idx]), 4),
            "residual": round(float(residuals[idx]), 4),
        })

    # Summary decision & warnings
    warnings = []
    if bp_res["heteroscedasticity_concern"]:
        warnings.append("Breusch-Pagan test indicates potential heteroscedasticity (p < 0.05). Standard errors may be affected.")
    if has_multicollinearity_concern:
        warnings.append("One or more independent variables exhibit high multicollinearity (VIF > 5). Consider removing correlated features.")
    if not res_normality["normal_residuals"]:
        warnings.append("Residuals show significant deviation from normality (p < 0.05). Review for skewness or outliers.")
    if influential_points_count > 0:
        warnings.append(f"Detected {influential_points_count} potentially influential observations based on Cook's distance (threshold = {round(cooks_threshold, 4)}).")

    return {
        "status": "COMPLETED",
        "method": "ols_regression",
        "method_name": "Ordinary Least Squares (OLS) Linear Regression",
        "missing_report": missing_report.model_dump(),
        "dependent_variable": y_name,
        "independent_variables": x_names,
        "sample_size": n,
        "degrees_of_freedom_residuals": df_resid,
        "r_squared": round(r_squared, 4),
        "adjusted_r_squared": round(adj_r_squared, 4),
        "f_statistic": round(f_stat, 4),
        "f_p_value": round(f_p_val, 6),
        "is_model_significant": bool(f_p_val < alpha),
        "residual_standard_error": round(se_regression, 4),
        "aic": round(aic, 2),
        "bic": round(bic, 2),
        "coefficients": coeff_table,
        "diagnostics": {
            "vif": vif_results,
            "breusch_pagan": bp_res,
            "durbin_watson": {"statistic": round(dw_stat, 4), "autocorrelation_concern": dw_concern},
            "residual_normality": res_normality,
            "cooks_distance": {
                "threshold": round(cooks_threshold, 4),
                "influential_points_count": influential_points_count,
            },
        },
        "plot_data": {
            "residual_vs_fitted": residual_points,
            "fitted_vs_actual": scatter_fitted,
        },
        "warnings": warnings,
    }
