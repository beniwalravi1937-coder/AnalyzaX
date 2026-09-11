"""
AnalyzaX — Phase 10: Comprehensive Statistical Engine Tests
Tests Fixtures A through I covering:
- Fixture A: Normal numeric data (Descriptive stats, mean CI)
- Fixture B: Two-group data (Student's t, Welch's t, Mann-Whitney U, Cohen's d, Hedges' g)
- Fixture C: Paired data (Paired t-test, Wilcoxon signed-rank)
- Fixture D: Multi-group data (One-way ANOVA, Tukey post-hoc, Kruskal-Wallis, Eta-squared)
- Fixture E: Correlated data (Pearson r, Spearman rho, Kendall tau, correlation matrix)
- Fixture F: Categorical data (Chi-Square test of independence, Cramér's V, Fisher's exact 2x2)
- Fixture G: Regression data (OLS simple and multiple regression, coefficients, R2, VIF, Cook's D)
- Fixture H: Assumption violations (Heteroscedasticity, non-normal residuals, outliers)
- Fixture I: Edge cases (Constant columns, zero variance, single observations, missing values)
"""

import math
import numpy as np
import polars as pl
import pytest
from scipy import stats

from backend.app.engines.statistics.assumptions.normality import check_normality
from backend.app.engines.statistics.assumptions.variance import check_homogeneity_of_variance
from backend.app.engines.statistics.engine import statistics_engine
from backend.app.engines.statistics.methods.categorical import run_categorical_association
from backend.app.engines.statistics.methods.confidence import (
    compute_diff_means_ci,
    compute_mean_ci,
    compute_proportion_ci,
)
from backend.app.engines.statistics.methods.correlation import (
    compute_bivariate_correlation,
    compute_correlation_matrix,
)
from backend.app.engines.statistics.methods.descriptive import (
    compute_boolean_descriptive,
    compute_categorical_descriptive,
    compute_numeric_descriptive,
)
from backend.app.engines.statistics.methods.distribution import compute_distribution_analysis
from backend.app.engines.statistics.methods.effect_size import (
    compute_cohens_d,
    compute_cramers_v,
    compute_eta_squared,
    compute_hedges_g,
)
from backend.app.engines.statistics.methods.group_comparison import (
    run_independent_ttest,
    run_kruskal_wallis,
    run_mann_whitney_u,
    run_oneway_anova,
    run_paired_ttest,
    run_wilcoxon_signed_rank,
)
from backend.app.engines.statistics.methods.multiple_testing import adjust_p_values
from backend.app.engines.statistics.methods.regression import run_ols_regression
from backend.app.engines.statistics.models import (
    AssumptionStatus,
    StatisticalAnalysisRequest,
)


# ── Fixture A: Normal Numeric Data ──
def test_fixture_a_descriptive_and_ci():
    np.random.seed(42)
    normal_data = np.random.normal(loc=100.0, scale=15.0, size=200)

    # 1. Numeric descriptive
    desc = compute_numeric_descriptive(normal_data, "score", confidence_level=0.95)
    assert desc["count"] == 200
    assert abs(desc["mean"] - 100.0) < 3.0
    assert abs(desc["std"] - 15.0) < 3.0
    assert desc["q25"] < desc["median"] < desc["q75"]
    assert desc["iqr"] > 0
    assert abs(desc["skewness"]) < 0.5
    assert abs(desc["kurtosis"]) < 0.8
    assert desc["confidence_interval_mean"] is not None

    ci = desc["confidence_interval_mean"]
    assert ci["lower"] < desc["mean"] < ci["upper"]
    assert ci["level"] == 0.95

    # 2. Distribution analysis
    dist = compute_distribution_analysis(normal_data, "score")
    assert len(dist["histogram_bins"]) >= 5
    assert len(dist["ecdf"]) > 10
    assert "mild_bounds" in dist["outliers"]


# ── Fixture B: Two-Group Comparison ──
def test_fixture_b_two_group_comparison():
    np.random.seed(42)
    group_a = np.random.normal(loc=50.0, scale=8.0, size=50)
    group_b = np.random.normal(loc=60.0, scale=12.0, size=50)  # Different mean & variance

    # Student's t-test
    res_ind = run_independent_ttest(
        group_a, group_b, "GroupA", "GroupB", "Metric", equal_var=True, alpha=0.05
    )
    assert res_ind["status"] == "COMPLETED"
    assert res_ind["test_statistic_name"] == "t"
    assert res_ind["is_significant"] is True
    assert res_ind["p_value"] < 0.001

    # Welch's t-test (unequal variance)
    res_welch = run_independent_ttest(
        group_a, group_b, "GroupA", "GroupB", "Metric", equal_var=False, alpha=0.05
    )
    assert res_welch["status"] == "COMPLETED"
    assert res_welch["is_significant"] is True
    assert res_welch["degrees_of_freedom"] < 98.0  # Satterthwaite adjustment

    # Effect sizes: Cohen's d & Hedges' g
    effects = {e["metric_name"]: e["value"] for e in res_welch["effect_sizes"]}
    assert "cohen_d" in effects
    assert "hedges_g" in effects
    assert abs(effects["cohen_d"]) > 0.8  # Large effect

    # Mann-Whitney U
    res_mw = run_mann_whitney_u(group_a, group_b, "GroupA", "GroupB", "Metric", alpha=0.05)
    assert res_mw["status"] == "COMPLETED"
    assert res_mw["is_significant"] is True
    assert res_mw["test_statistic_name"] == "U"


# ── Fixture C: Paired Data ──
def test_fixture_c_paired_data():
    np.random.seed(42)
    pre = np.random.normal(loc=120.0, scale=10.0, size=30)
    post = pre - np.random.normal(loc=8.0, scale=4.0, size=30)  # Significant drop

    # Paired t-test
    res_paired = run_paired_ttest(pre, post, "Pre", "Post", "BloodPressure", alpha=0.05)
    assert res_paired["status"] == "COMPLETED"
    assert res_paired["mean_difference"] > 0
    assert res_paired["is_significant"] is True
    assert res_paired["p_value"] < 0.001

    # Wilcoxon signed-rank test
    res_wilcoxon = run_wilcoxon_signed_rank(pre, post, "Pre", "Post", "BloodPressure", alpha=0.05)
    assert res_wilcoxon["status"] == "COMPLETED"
    assert res_wilcoxon["is_significant"] is True
    assert res_wilcoxon["test_statistic_name"] == "W"


# ── Fixture D: Multi-Group Data (ANOVA & Kruskal-Wallis) ──
def test_fixture_d_anova_and_kruskal():
    np.random.seed(42)
    groups = {
        "Control": np.random.normal(loc=10.0, scale=2.0, size=25),
        "LowDose": np.random.normal(loc=12.0, scale=2.0, size=25),
        "HighDose": np.random.normal(loc=16.0, scale=2.0, size=25),
    }

    # One-way ANOVA
    res_anova = run_oneway_anova(groups, "Response", alpha=0.05)
    assert res_anova["status"] == "COMPLETED"
    assert res_anova["is_significant"] is True
    assert res_anova["test_statistic_name"] == "F"
    assert res_anova["df_between"] == 2
    assert res_anova["df_within"] == 72
    assert len(res_anova["post_hoc_comparisons"]) == 3  # (Control-Low, Control-High, Low-High)

    # Eta squared
    eta_effect = res_anova["effect_sizes"][0]
    assert eta_effect["metric_name"] == "eta_squared"
    assert eta_effect["value"] > 0.14  # Large effect

    # Kruskal-Wallis
    res_kw = run_kruskal_wallis(groups, "Response", alpha=0.05)
    assert res_kw["status"] == "COMPLETED"
    assert res_kw["is_significant"] is True
    assert res_kw["test_statistic_name"] == "H"
    assert len(res_kw["post_hoc_comparisons"]) == 3


# ── Fixture E: Correlated Data ──
def test_fixture_e_correlations():
    np.random.seed(42)
    x = np.linspace(1, 100, 50)
    y = 2.5 * x + np.random.normal(0, 10, 50)  # Strong linear correlation
    z = np.random.normal(0, 1, 50)             # Uncorrelated

    # Pearson correlation
    res_pearson = compute_bivariate_correlation(x, y, "X", "Y", method="pearson", alpha=0.05)
    assert res_pearson["is_valid"] is True
    assert res_pearson["coefficient"] > 0.9
    assert res_pearson["is_significant"] is True
    assert res_pearson["confidence_interval"] is not None
    ci = res_pearson["confidence_interval"]
    assert ci["lower"] > 0.8

    # Spearman rank correlation
    res_spearman = compute_bivariate_correlation(x, y, "X", "Y", method="spearman", alpha=0.05)
    assert res_spearman["is_valid"] is True
    assert res_spearman["coefficient"] > 0.9

    # Kendall's tau
    res_kendall = compute_bivariate_correlation(x, y, "X", "Y", method="kendall", alpha=0.05)
    assert res_kendall["is_valid"] is True
    assert res_kendall["coefficient"] > 0.7

    # Correlation Matrix
    mat_res = compute_correlation_matrix({"X": x, "Y": y, "Z": z})
    assert len(mat_res["columns"]) == 3
    assert len(mat_res["ranked_pairs"]) == 3
    assert mat_res["ranked_pairs"][0]["var1"] in ("X", "Y")
    assert mat_res["ranked_pairs"][0]["var2"] in ("X", "Y")


# ── Fixture F: Categorical Data (Chi-Square & Fisher) ──
def test_fixture_f_categorical_association():
    # 2x2 table
    var_gender = ["Male"] * 50 + ["Female"] * 50
    var_preference = ["OptionA"] * 40 + ["OptionB"] * 10 + ["OptionA"] * 15 + ["OptionB"] * 35

    res_cat = run_categorical_association(var_gender, var_preference, "Gender", "Preference", alpha=0.05)
    assert res_cat["status"] == "COMPLETED"
    assert res_cat["test_statistic_name"] == "Chi2"
    assert res_cat["is_significant"] is True
    assert res_cat["degrees_of_freedom"] == 1
    assert len(res_cat["effect_sizes"]) > 0
    assert res_cat["effect_sizes"][0]["metric_name"] == "cramer_v"
    assert res_cat["fisher_exact_test"] is not None
    assert res_cat["fisher_exact_test"]["is_significant"] is True


# ── Fixture G: Regression Data ──
def test_fixture_g_ols_regression():
    np.random.seed(42)
    n = 100
    x1 = np.random.normal(10, 2, n)
    x2 = np.random.normal(50, 5, n)
    # y = 5 + 3*x1 - 1.5*x2 + noise
    y = 5.0 + 3.0 * x1 - 1.5 * x2 + np.random.normal(0, 1, n)
    X = np.column_stack([x1, x2])

    reg_res = run_ols_regression(y, X, "Y", ["X1", "X2"], confidence_level=0.95, alpha=0.05)
    assert reg_res["status"] == "COMPLETED"
    assert reg_res["sample_size"] == n
    assert reg_res["r_squared"] > 0.85
    assert reg_res["is_model_significant"] is True

    # Check coefficients
    coeffs = {c["parameter"]: c for c in reg_res["coefficients"]}
    assert "Intercept" in coeffs
    assert "X1" in coeffs
    assert "X2" in coeffs
    assert abs(coeffs["X1"]["coefficient"] - 3.0) < 0.5
    assert abs(coeffs["X2"]["coefficient"] - (-1.5)) < 0.5
    assert coeffs["X1"]["is_significant"] is True
    assert coeffs["X2"]["is_significant"] is True

    # Diagnostics
    diag = reg_res["diagnostics"]
    assert "vif" in diag
    assert diag["vif"]["X1"] < 3.0  # Low collinearity
    assert "breusch_pagan" in diag
    assert "durbin_watson" in diag
    assert "residual_normality" in diag


# ── Fixture H: Assumption Diagnostics ──
def test_fixture_h_assumption_diagnostics():
    np.random.seed(42)
    # 1. Normal data -> Pass
    norm_sample = np.random.normal(0, 1, 100)
    check_pass = check_normality(norm_sample, "normal_var")
    assert check_pass.status in (AssumptionStatus.PASS, AssumptionStatus.WARNING)

    # 2. Exponential / heavily skewed data -> Violation
    skewed_sample = np.random.exponential(scale=2.0, size=200)
    check_violation = check_normality(skewed_sample, "skewed_var")
    assert check_violation.status == AssumptionStatus.VIOLATION

    # 3. Variance check: Equal vs Unequal
    g1 = np.random.normal(0, 1.0, 50)
    g2 = np.random.normal(0, 1.0, 50)
    var_pass = check_homogeneity_of_variance({"g1": g1, "g2": g2}, "y")
    assert var_pass.status == AssumptionStatus.PASS

    g3_hetero = np.random.normal(0, 10.0, 50)  # 100x variance
    var_fail = check_homogeneity_of_variance({"g1": g1, "g3": g3_hetero}, "y")
    assert var_fail.status in (AssumptionStatus.VIOLATION, AssumptionStatus.WARNING)


# ── Fixture I: Edge Cases & Safety ──
def test_fixture_i_edge_cases():
    # 1. Constant variable correlation
    const_arr = np.array([5.0, 5.0, 5.0, 5.0, 5.0])
    normal_arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    corr_res = compute_bivariate_correlation(const_arr, normal_arr, "Const", "Norm")
    assert corr_res["status"] == "CONSTANT_VARIABLE"
    assert corr_res["is_valid"] is False

    # 2. Zero-variance t-test
    res_ttest = run_independent_ttest(const_arr, const_arr, "A", "B", "Metric")
    assert res_ttest["status"] == "ZERO_VARIANCE_ERROR"

    # 3. Tiny sample size (n=1)
    single_obs = np.array([42.0])
    res_single = run_independent_ttest(single_obs, normal_arr, "Single", "Norm", "Metric")
    assert res_single["status"] == "INSUFFICIENT_DATA"

    # 4. Singular regression matrix (collinear features)
    x1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    x2 = x1 * 2.0  # Perfectly collinear
    y = np.array([2.0, 4.0, 6.0, 8.0, 10.0, 12.0])
    X_collinear = np.column_stack([x1, x2])
    reg_err = run_ols_regression(y, X_collinear, "Y", ["X1", "X2"])
    assert reg_err["status"] == "SINGULAR_MATRIX_ERROR"


# ── Multiple Testing Adjustments ──
def test_multiple_testing_adjustments():
    raw_p = [0.001, 0.012, 0.045, 0.080, 0.250]

    # Bonferroni
    adj_bonf = adjust_p_values(raw_p, method="bonferroni", alpha=0.05)
    assert adj_bonf[0]["adjusted_p_value"] == round(0.001 * 5, 6)
    assert adj_bonf[1]["adjusted_p_value"] == round(0.012 * 5, 6)
    assert adj_bonf[2]["adjusted_p_value"] == round(min(1.0, 0.045 * 5), 6)

    # Holm
    adj_holm = adjust_p_values(raw_p, method="holm", alpha=0.05)
    assert adj_holm[0]["adjusted_p_value"] <= adj_bonf[0]["adjusted_p_value"]

    # Benjamini-Hochberg (FDR)
    adj_fdr = adjust_p_values(raw_p, method="fdr_bh", alpha=0.05)
    assert adj_fdr[0]["adjusted_p_value"] <= adj_fdr[1]["adjusted_p_value"]
    assert adj_fdr[0]["rejected"] is True
