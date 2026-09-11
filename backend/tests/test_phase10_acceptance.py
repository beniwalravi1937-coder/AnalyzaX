"""
AnalyzaX — Phase 10: Formal Acceptance Criteria Verification Suite
Tests STAT-01 through STAT-60 validating all statistical capabilities,
assumptions, effect sizes, interpretations, visualizations, and safety guarantees.
"""

import io
import math
import numpy as np
import polars as pl
import pytest
from starlette.testclient import TestClient

from backend.app.engines.statistics.assumptions.normality import check_normality
from backend.app.engines.statistics.assumptions.sample_size import check_sample_size_adequacy
from backend.app.engines.statistics.assumptions.variance import check_homogeneity_of_variance
from backend.app.engines.statistics.catalog import get_all_catalog_items
from backend.app.engines.statistics.engine import statistics_engine
from backend.app.engines.statistics.methods.categorical import run_categorical_association
from backend.app.engines.statistics.methods.confidence import compute_mean_ci
from backend.app.engines.statistics.methods.correlation import (
    compute_bivariate_correlation,
    compute_correlation_matrix,
)
from backend.app.engines.statistics.methods.descriptive import (
    compute_boolean_descriptive,
    compute_categorical_descriptive,
    compute_datetime_descriptive,
    compute_numeric_descriptive,
)
from backend.app.engines.statistics.methods.distribution import compute_distribution_analysis
from backend.app.engines.statistics.methods.effect_size import (
    compute_cohens_d,
    compute_cramers_v,
    compute_eta_squared,
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
    StatisticalResult,
)
from backend.app.main import app

client = TestClient(app)


# ── Core Architecture (STAT-01 to STAT-05) ──
def test_stat_01_to_05_core_architecture():
    req = StatisticalAnalysisRequest(
        dataset_id="ds_test",
        dataset_version_id="v1",
        analysis_type="descriptive",
        method="descriptive_summary",
        target_columns=["x"],
    )
    assert req.analysis_id.startswith("stat_")
    assert req.dataset_id == "ds_test"
    assert req.dataset_version_id == "v1"

    df = pl.DataFrame({"x": [10.0, 20.0, 30.0, 40.0, 50.0]})
    res = statistics_engine.execute_analysis(df, req)
    assert isinstance(res, StatisticalResult)
    assert res.dataset_version_id == "v1"
    assert res.provenance["deterministic_libraries"] == ["scipy", "statsmodels", "numpy", "polars"]


# ── Descriptive Statistics (STAT-06 to STAT-10) ──
def test_stat_06_numeric_descriptive():
    vals = np.array([10.0, 20.0, 30.0, 40.0, 50.0, np.nan])
    res = compute_numeric_descriptive(vals, "num_col")
    assert res["count"] == 5
    assert res["missing_count"] == 1
    assert res["mean"] == 30.0
    assert res["median"] == 30.0
    assert res["min"] == 10.0
    assert res["max"] == 50.0
    assert res["range"] == 40.0
    assert res["std"] > 0
    assert res["variance"] > 0
    assert res["iqr"] > 0
    assert res["se"] > 0
    assert res["confidence_interval_mean"] is not None


def test_stat_07_categorical_descriptive():
    s = pl.Series("fruit", ["Apple", "Banana", "Apple", "Orange", None])
    res = compute_categorical_descriptive(s, "fruit")
    assert res["count"] == 4
    assert res["missing_count"] == 1
    assert res["unique_count"] == 3
    assert "Apple" in res["frequencies"]
    assert res["frequencies"]["Apple"] == 2


def test_stat_08_boolean_descriptive():
    s = pl.Series("flag", [True, False, True, True, None])
    res = compute_boolean_descriptive(s, "flag")
    assert res["count"] == 4
    assert res["true_count"] == 3
    assert res["false_count"] == 1
    assert res["true_percentage"] == 75.0


def test_stat_09_datetime_descriptive():
    s = pl.Series("dates", ["2026-01-01", "2026-01-02", "2026-01-10"])
    res = compute_datetime_descriptive(s, "dates")
    assert res["count"] == 3
    assert res["span_days"] == 9
    assert res["unique_periods"] == 3


def test_stat_10_missing_reporting():
    vals = np.array([1.0, 2.0, np.nan, 4.0, np.inf])
    res = compute_numeric_descriptive(vals, "col")
    rep = res["missing_report"]
    assert rep["original_observations"] == 5
    assert rep["used_observations"] == 3
    assert rep["excluded_observations"] == 2


# ── Inferential & Tests (STAT-11 to STAT-21) ──
def test_stat_11_confidence_intervals():
    vals = np.array([10.0, 12.0, 11.0, 13.0, 10.5, 12.5])
    ci_90 = compute_mean_ci(vals, confidence_level=0.90)
    ci_95 = compute_mean_ci(vals, confidence_level=0.95)
    ci_99 = compute_mean_ci(vals, confidence_level=0.99)
    assert ci_90.margin_of_error < ci_95.margin_of_error < ci_99.margin_of_error


def test_stat_12_and_13_hypotheses_and_decision():
    g1 = np.array([10.0, 12.0, 11.0, 13.0])
    g2 = np.array([20.0, 22.0, 21.0, 23.0])
    res = run_independent_ttest(g1, g2, "G1", "G2", "Y", equal_var=False, alpha=0.05)
    assert "null_hypothesis" in res
    assert "alternative_hypothesis" in res
    assert "statistic" in res
    assert "p_value" in res
    assert res["alpha"] == 0.05
    assert res["decision"] == "Reject Null Hypothesis"


def test_stat_14_effect_sizes():
    g1 = np.array([10.0, 12.0, 11.0, 13.0])
    g2 = np.array([20.0, 22.0, 21.0, 23.0])
    d = compute_cohens_d(g1, g2)
    assert d.metric_name == "cohen_d"
    assert d.interpretation == "large"


def test_stat_15_multiple_testing():
    pvals = [0.005, 0.03, 0.04, 0.20]
    bonf = adjust_p_values(pvals, method="bonferroni")
    assert len(bonf) == 4
    assert bonf[0]["adjusted_p_value"] == 0.02


def test_stat_16_to_19_group_comparisons():
    g1 = np.array([10.0, 12.0, 11.0, 13.0, 12.0])
    g2 = np.array([18.0, 20.0, 19.0, 21.0, 22.0])
    g3 = np.array([28.0, 30.0, 29.0, 31.0, 32.0])

    # Independent tests
    welch = run_independent_ttest(g1, g2, "G1", "G2", "Y", equal_var=False)
    assert welch["status"] == "COMPLETED"
    mw = run_mann_whitney_u(g1, g2, "G1", "G2", "Y")
    assert mw["status"] == "COMPLETED"

    # Paired tests
    paired = run_paired_ttest(g1, g2, "Pre", "Post", "Y")
    assert paired["status"] == "COMPLETED"
    wilc = run_wilcoxon_signed_rank(g1, g2, "Pre", "Post", "Y")
    assert wilc["status"] == "COMPLETED"

    # ANOVA and Kruskal
    anova = run_oneway_anova({"G1": g1, "G2": g2, "G3": g3}, "Y")
    assert anova["status"] == "COMPLETED"
    assert len(anova["post_hoc_comparisons"]) == 3

    kruskal = run_kruskal_wallis({"G1": g1, "G2": g2, "G3": g3}, "Y")
    assert kruskal["status"] == "COMPLETED"


def test_stat_20_and_21_categorical_association():
    v1 = ["A", "A", "B", "B"] * 10
    v2 = ["X", "Y", "X", "Y"] * 10
    res = run_categorical_association(v1, v2, "V1", "V2")
    assert res["status"] == "COMPLETED"
    assert "contingency_table" in res
    assert res["fisher_exact_test"] is not None


# ── Correlation (STAT-22 to STAT-26) ──
def test_stat_22_to_26_correlations():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    y = np.array([2.0, 4.0, 6.0, 8.0, 10.0, 12.0])
    p_res = compute_bivariate_correlation(x, y, "X", "Y", method="pearson")
    assert p_res["coefficient"] == 1.0
    s_res = compute_bivariate_correlation(x, y, "X", "Y", method="spearman")
    assert s_res["coefficient"] == 1.0
    assert p_res["sample_size"] == 6

    # Matrix
    mat = compute_correlation_matrix({"X": x, "Y": y})
    assert len(mat["ranked_pairs"]) == 1

    # Constant column handling
    const = np.array([5.0, 5.0, 5.0, 5.0, 5.0, 5.0])
    safe_res = compute_bivariate_correlation(const, y, "Const", "Y")
    assert safe_res["status"] == "CONSTANT_VARIABLE"
    assert safe_res["is_valid"] is False


# ── Regression (STAT-27 to STAT-34) ──
def test_stat_27_to_34_regression():
    np.random.seed(42)
    n = 60
    x1 = np.random.normal(10, 2, n)
    x2 = np.random.normal(20, 3, n)
    y = 2.0 + 1.5 * x1 + 0.8 * x2 + np.random.normal(0, 0.5, n)
    X = np.column_stack([x1, x2])

    reg = run_ols_regression(y, X, "Y", ["X1", "X2"])
    assert reg["status"] == "COMPLETED"
    assert reg["r_squared"] > 0.8
    assert reg["adjusted_r_squared"] > 0.8
    assert len(reg["coefficients"]) == 3
    for c in reg["coefficients"]:
        assert "standard_error" in c
        assert "p_value" in c
        assert "confidence_interval" in c

    # Diagnostics
    diag = reg["diagnostics"]
    assert "vif" in diag
    assert "breusch_pagan" in diag
    assert "cooks_distance" in diag
    assert "residual_normality" in diag


# ── Assumptions & Limitations (STAT-35 to STAT-45) ──
def test_stat_35_to_45_assumptions_and_interpretations():
    vals = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    norm = check_normality(vals, "var")
    assert norm.status in (AssumptionStatus.PASS, AssumptionStatus.WARNING)
    assert norm.recommendation is not None

    g_dict = {"A": vals, "B": vals * 2}
    var_chk = check_homogeneity_of_variance(g_dict, "y")
    assert var_chk.status in (AssumptionStatus.PASS, AssumptionStatus.WARNING, AssumptionStatus.VIOLATION)

    sz_chk = check_sample_size_adequacy({"A": 4}, "comparison")
    assert sz_chk.status == AssumptionStatus.VIOLATION

    # Full execution narrative check
    df = pl.DataFrame({"A": [1, 2, 3, 4, 5], "B": [2, 4, 6, 8, 10]})
    req = StatisticalAnalysisRequest(
        dataset_id="ds_a",
        dataset_version_id="v1",
        analysis_type="correlation",
        method="pearson",
        target_columns=["A", "B"],
    )
    res = statistics_engine.execute_analysis(df, req)
    interp = res.interpretation
    assert "causality_caveat" in interp
    assert "association" in interp["causality_caveat"].lower()
    assert "limitations" in interp


# ── Visualization Integration (STAT-46 to STAT-50) ──
def test_stat_46_to_50_chart_specs():
    df = pl.DataFrame({"score": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]})
    req = StatisticalAnalysisRequest(
        dataset_id="ds_v",
        dataset_version_id="v1",
        analysis_type="distribution",
        method="distribution_analysis",
        target_columns=["score"],
    )
    res = statistics_engine.execute_analysis(df, req)
    assert len(res.chart_specs) >= 2
    spec = res.chart_specs[0]
    assert "chart_type" in spec
    assert "title" in spec
    assert "data" in spec


# ── Safety & Numerical Robustness (STAT-56 to STAT-60) ──
def test_stat_56_to_60_numerical_safety():
    # 1. NaN/Inf handling
    nan_data = np.array([np.nan, np.inf, -np.inf, np.nan])
    res = compute_numeric_descriptive(nan_data, "bad")
    assert res["count"] == 0
    assert res["mean"] is None

    # 2. Insufficient group size
    tiny_g1 = np.array([5.0])
    tiny_g2 = np.array([10.0])
    res_tt = run_independent_ttest(tiny_g1, tiny_g2, "A", "B", "Y")
    assert res_tt["status"] == "INSUFFICIENT_DATA"

    # 3. Zero variance
    zv1 = np.array([2.0, 2.0, 2.0])
    zv2 = np.array([2.0, 2.0, 2.0])
    res_zv = run_independent_ttest(zv1, zv2, "A", "B", "Y")
    assert res_zv["status"] == "ZERO_VARIANCE_ERROR"
