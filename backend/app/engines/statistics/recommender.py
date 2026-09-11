"""
AnalyzaX — Phase 10: Deterministic Statistical Method Recommender
Suggests appropriate statistical tests based on variable types, sample size, group count,
and variance/distribution indicators without using an LLM (STAT-32, STAT-33).
"""

from typing import Any, Dict, List, Optional
import numpy as np
import polars as pl

from backend.app.engines.statistics.catalog import get_catalog_item
from backend.app.engines.statistics.models import MethodRecommendation


def recommend_statistical_method(
    df: pl.DataFrame,
    target_columns: List[str],
    group_columns: Optional[List[str]] = None,
    intent: Optional[str] = None,
) -> MethodRecommendation:
    """
    Deterministically recommends the optimal statistical method and plausible alternatives.
    """
    group_columns = group_columns or []
    target_cols_clean = [c for c in target_columns if c in df.columns]
    group_cols_clean = [c for c in group_columns if c in df.columns]

    n_targets = len(target_cols_clean)
    n_groups = len(group_cols_clean)
    n_rows = len(df)

    if n_targets == 0:
        return MethodRecommendation(
            recommended_method="descriptive_summary",
            recommended_name="Summary Statistics",
            alternative_methods=[],
            rationale=["No valid target columns selected. Defaulting to summary statistics."],
            required_assumptions=["None"],
            warnings=["Please select target columns."],
        )

    # Detect data types
    schema = df.schema
    target_types = [str(schema[c]).lower() for c in target_cols_clean]
    is_target_numeric = all(any(t in tt for t in ["int", "float", "decimal"]) for tt in target_types)

    # 1. Regression intent: 1 target outcome + 1 or more predictor columns
    if intent == "regression" or (n_targets == 1 and n_groups >= 1 and is_target_numeric and "compare" not in (intent or "")):
        # Check if group columns are numeric
        group_types = [str(schema[c]).lower() for c in group_cols_clean]
        is_group_numeric = all(any(t in gt for t in ["int", "float", "decimal"]) for gt in group_types)

        if is_group_numeric:
            return MethodRecommendation(
                recommended_method="ols_regression",
                recommended_name="Ordinary Least Squares (OLS) Linear Regression",
                alternative_methods=["pearson", "spearman"],
                rationale=[
                    f"Continuous numeric outcome '{target_cols_clean[0]}' with {len(group_cols_clean)} continuous predictor(s).",
                    "Provides coefficient estimates, confidence intervals, R², and formal regression diagnostics.",
                    "Allows assessing multiple predictors simultaneously.",
                ],
                required_assumptions=[
                    "Linearity of relationships",
                    "Homoscedasticity (constant error variance)",
                    "Independence of observations",
                    "Normal distribution of residuals",
                    "Absence of severe multicollinearity (VIF < 5)",
                ],
                warnings=["Review Breusch-Pagan and VIF diagnostics after model estimation."],
            )

    # 2. Group Comparison: 1 numeric target + 1 categorical/grouping column
    if n_targets == 1 and is_target_numeric and n_groups == 1:
        grp_col = group_cols_clean[0]
        n_levels = df[grp_col].n_unique()

        if n_levels == 2:
            return MethodRecommendation(
                recommended_method="t_test_welch",
                recommended_name="Welch's Independent t-test",
                alternative_methods=["mann_whitney_u", "t_test_ind"],
                rationale=[
                    f"Numeric outcome '{target_cols_clean[0]}' grouped by binary factor '{grp_col}' (exactly 2 groups).",
                    "Welch's t-test does not assume equal variances, protecting against Type I error rate inflation.",
                    f"Dataset has {n_rows} rows; sufficient for asymptotic robustness under the Central Limit Theorem.",
                ],
                required_assumptions=[
                    "Independent observations between groups",
                    "Continuous or interval-scale outcome measurement",
                    "Approximate normality in small samples (or moderate sample size)",
                ],
                warnings=[
                    "If distributions are severely skewed or ordinal, Mann-Whitney U is a viable non-parametric alternative."
                ],
            )
        elif n_levels > 2:
            return MethodRecommendation(
                recommended_method="anova_oneway",
                recommended_name="One-Way ANOVA with Tukey HSD",
                alternative_methods=["kruskal_wallis"],
                rationale=[
                    f"Numeric outcome '{target_cols_clean[0]}' evaluated across {n_levels} distinct groups in '{grp_col}'.",
                    "Omnibus F-test evaluates if any group mean differs, followed by Tukey HSD post-hoc pairwise adjustments.",
                ],
                required_assumptions=[
                    "Independent observations across groups",
                    "Normal distribution of values within each group",
                    "Homogeneity of variance across groups (Levene's test)",
                ],
                warnings=[
                    "If group variances are heavily unequal or data is ordinal, Kruskal-Wallis is recommended."
                ],
            )

    # 3. Categorical Association: 2 categorical targets or 1 categorical target + 1 categorical group
    is_categorical = lambda col: not any(t in str(schema[col]).lower() for t in ["int", "float", "decimal", "date"])
    if (n_targets == 2 and is_categorical(target_cols_clean[0]) and is_categorical(target_cols_clean[1])) or \
       (n_targets == 1 and n_groups == 1 and is_categorical(target_cols_clean[0]) and is_categorical(group_cols_clean[0])):

        col_a = target_cols_clean[0]
        col_b = target_cols_clean[1] if n_targets >= 2 else group_cols_clean[0]
        u_a = df[col_a].n_unique()
        u_b = df[col_b].n_unique()

        if u_a == 2 and u_b == 2 and n_rows < 100:
            return MethodRecommendation(
                recommended_method="fisher_exact",
                recommended_name="Fisher's Exact Test (2×2)",
                alternative_methods=["chi_square"],
                rationale=[
                    f"Two binary categorical variables '{col_a}' and '{col_b}' forming a 2×2 contingency table.",
                    "Small/moderate sample size: Fisher's exact test calculates exact hypergeometric probabilities without large-sample approximations.",
                ],
                required_assumptions=["Independent observations", "2×2 contingency structure"],
                warnings=[],
            )
        else:
            return MethodRecommendation(
                recommended_method="chi_square",
                recommended_name="Chi-Square Test of Independence",
                alternative_methods=["fisher_exact"] if (u_a == 2 and u_b == 2) else [],
                rationale=[
                    f"Testing association between two categorical variables: '{col_a}' ({u_a} levels) and '{col_b}' ({u_b} levels).",
                    "Evaluates whether row and column variables are statistically independent.",
                ],
                required_assumptions=[
                    "Independent observations",
                    "Expected cell frequencies >= 5 in at least 80% of cells (Cochran's criteria)",
                ],
                warnings=["Check sparsity warnings if small frequencies exist in contingency cells."],
            )

    # 4. Correlation: 2 numeric variables
    if n_targets == 2 and is_target_numeric and n_groups == 0:
        return MethodRecommendation(
            recommended_method="pearson",
            recommended_name="Pearson Linear Correlation",
            alternative_methods=["spearman", "kendall"],
            rationale=[
                f"Two continuous numeric variables: '{target_cols_clean[0]}' and '{target_cols_clean[1]}'.",
                "Assesses the strength and direction of linear association with Fisher z confidence intervals.",
            ],
            required_assumptions=[
                "Linear association",
                "Absence of extreme outliers",
                "Continuous measurement scale",
            ],
            warnings=[
                "If relationships are monotonic but non-linear, or outliers exist, Spearman rank correlation is preferred."
            ],
        )

    # 5. Multiple numeric variables: Correlation Matrix
    if n_targets > 2 and is_target_numeric and n_groups == 0:
        return MethodRecommendation(
            recommended_method="correlation_matrix",
            recommended_name="Pairwise Correlation Matrix",
            alternative_methods=["descriptive_summary"],
            rationale=[
                f"{n_targets} continuous numeric variables selected.",
                "Computes full pairwise correlation matrix and ranks strongest positive and negative associations.",
            ],
            required_assumptions=["Linear or monotonic relationships across numeric variables"],
            warnings=[],
        )

    # 6. Single numeric variable: Distribution / Summary
    if n_targets == 1 and is_target_numeric and n_groups == 0:
        return MethodRecommendation(
            recommended_method="distribution_analysis",
            recommended_name="Distribution & Outlier Analysis",
            alternative_methods=["descriptive_summary"],
            rationale=[
                f"Single numeric column '{target_cols_clean[0]}' selected.",
                "Evaluates histogram shape, normality, quantiles, and IQR outlier boundaries.",
            ],
            required_assumptions=["Numeric scale"],
            warnings=[],
        )

    # Fallback to general descriptive summary
    return MethodRecommendation(
        recommended_method="descriptive_summary",
        recommended_name="Summary Statistics",
        alternative_methods=[],
        rationale=[f"Computed descriptive summary across {n_targets} column(s)."],
        required_assumptions=["None"],
        warnings=[],
    )
