"""
AnalyzaX — Phase 10: Statistical Method Catalog
Machine-readable catalog of supported deterministic statistical methods (STAT-58, STAT-80).
Drives frontend configuration and selector UI without duplicate hardcoded logic.
"""

from typing import Dict, List
from backend.app.engines.statistics.models import MethodCatalogItem

STATISTICAL_METHODS_CATALOG: Dict[str, MethodCatalogItem] = {
    # ── Descriptive ──
    "descriptive_summary": MethodCatalogItem(
        method="descriptive_summary",
        name="Summary Statistics",
        category="Descriptive",
        description="Comprehensive parametric and non-parametric summary metrics (mean, median, IQR, skewness, kurtosis, SE).",
        required_inputs={"target_columns": "1 or more numeric/categorical columns"},
        supported_data_types=["numeric", "categorical", "boolean", "datetime"],
        assumptions=["None (purely descriptive)"],
        supports_effect_size=False,
        supports_confidence_interval=True,
        supports_visualization=True,
    ),
    "distribution_analysis": MethodCatalogItem(
        method="distribution_analysis",
        name="Distribution & Outlier Analysis",
        category="Descriptive",
        description="Freedman-Diaconis binned histograms, ECDF, quantiles, and IQR outlier boundaries.",
        required_inputs={"target_columns": "1 numeric column"},
        supported_data_types=["numeric"],
        assumptions=["Continuous or discrete numeric measurement"],
        supports_effect_size=False,
        supports_confidence_interval=False,
        supports_visualization=True,
    ),

    # ── Group Comparison ──
    "t_test_welch": MethodCatalogItem(
        method="t_test_welch",
        name="Welch's Independent t-test",
        category="Comparison",
        description="Two-sample test comparing means without assuming equal population variances (robust default).",
        required_inputs={"target_columns": "1 numeric outcome", "group_columns": "1 binary grouping column"},
        supported_data_types=["numeric"],
        assumptions=["Independent observations", "Approximate normality (or moderate sample size by CLT)"],
        supports_effect_size=True,
        supports_confidence_interval=True,
        supports_visualization=True,
    ),
    "t_test_ind": MethodCatalogItem(
        method="t_test_ind",
        name="Student's Independent t-test",
        category="Comparison",
        description="Classical two-sample test for equal means assuming equal population variances.",
        required_inputs={"target_columns": "1 numeric outcome", "group_columns": "1 binary grouping column"},
        supported_data_types=["numeric"],
        assumptions=["Independent observations", "Normality of distributions", "Homogeneity of variance (Levene p >= 0.05)"],
        supports_effect_size=True,
        supports_confidence_interval=True,
        supports_visualization=True,
    ),
    "t_test_paired": MethodCatalogItem(
        method="t_test_paired",
        name="Paired Samples t-test",
        category="Comparison",
        description="Compares paired or repeated observations (e.g. pre vs post intervention) for a single cohort.",
        required_inputs={"target_columns": "2 numeric columns representing paired measurements"},
        supported_data_types=["numeric"],
        assumptions=["Paired observations", "Normality of paired differences"],
        supports_effect_size=True,
        supports_confidence_interval=True,
        supports_visualization=True,
    ),
    "mann_whitney_u": MethodCatalogItem(
        method="mann_whitney_u",
        name="Mann-Whitney U Test",
        category="Comparison",
        description="Non-parametric two-group test comparing rank distributions. Does not assume normality.",
        required_inputs={"target_columns": "1 numeric/ordinal outcome", "group_columns": "1 binary grouping column"},
        supported_data_types=["numeric", "ordinal"],
        assumptions=["Independent observations", "Ordinal or continuous measurement"],
        supports_effect_size=True,
        supports_confidence_interval=False,
        supports_visualization=True,
    ),
    "wilcoxon": MethodCatalogItem(
        method="wilcoxon",
        name="Wilcoxon Signed-Rank Test",
        category="Comparison",
        description="Non-parametric test for paired continuous or ordinal observations.",
        required_inputs={"target_columns": "2 paired numeric columns"},
        supported_data_types=["numeric", "ordinal"],
        assumptions=["Paired observations", "Symmetric distribution of differences"],
        supports_effect_size=False,
        supports_confidence_interval=False,
        supports_visualization=True,
    ),
    "anova_oneway": MethodCatalogItem(
        method="anova_oneway",
        name="One-Way ANOVA with Tukey HSD",
        category="Comparison",
        description="Tests equality of means across 3 or more independent groups with post-hoc pairwise comparisons.",
        required_inputs={"target_columns": "1 numeric outcome", "group_columns": "1 multi-level grouping column"},
        supported_data_types=["numeric"],
        assumptions=["Independent observations", "Normality within groups", "Homogeneity of variance"],
        supports_effect_size=True,
        supports_confidence_interval=True,
        supports_visualization=True,
    ),
    "kruskal_wallis": MethodCatalogItem(
        method="kruskal_wallis",
        name="Kruskal-Wallis ANOVA",
        category="Comparison",
        description="Non-parametric multi-group comparison of medians/ranks across 3 or more independent groups.",
        required_inputs={"target_columns": "1 numeric outcome", "group_columns": "1 multi-level grouping column"},
        supported_data_types=["numeric", "ordinal"],
        assumptions=["Independent observations", "Ordinal or continuous data"],
        supports_effect_size=True,
        supports_confidence_interval=False,
        supports_visualization=True,
    ),

    # ── Association & Correlation ──
    "pearson": MethodCatalogItem(
        method="pearson",
        name="Pearson Linear Correlation",
        category="Association",
        description="Measures linear association between two continuous variables with Fisher z confidence intervals.",
        required_inputs={"target_columns": "2 numeric columns"},
        supported_data_types=["numeric"],
        assumptions=["Linear relationship", "Bivariate normality", "Absence of extreme outliers"],
        supports_effect_size=True,
        supports_confidence_interval=True,
        supports_visualization=True,
    ),
    "spearman": MethodCatalogItem(
        method="spearman",
        name="Spearman Rank Correlation",
        category="Association",
        description="Measures monotonic relationship between two variables based on ranked values.",
        required_inputs={"target_columns": "2 numeric or ordinal columns"},
        supported_data_types=["numeric", "ordinal"],
        assumptions=["Monotonic relationship", "Ordinal or continuous measurement"],
        supports_effect_size=True,
        supports_confidence_interval=False,
        supports_visualization=True,
    ),
    "kendall": MethodCatalogItem(
        method="kendall",
        name="Kendall's Tau Correlation",
        category="Association",
        description="Robust concordance-based rank correlation, especially suitable for small sample sizes or ties.",
        required_inputs={"target_columns": "2 numeric or ordinal columns"},
        supported_data_types=["numeric", "ordinal"],
        assumptions=["Ordinal or continuous data"],
        supports_effect_size=True,
        supports_confidence_interval=False,
        supports_visualization=True,
    ),
    "correlation_matrix": MethodCatalogItem(
        method="correlation_matrix",
        name="Correlation Matrix",
        category="Association",
        description="Computes full pairwise correlation matrix and ranked pairs across multiple numeric variables.",
        required_inputs={"target_columns": "2 or more numeric columns"},
        supported_data_types=["numeric"],
        assumptions=["Linear or monotonic relationships"],
        supports_effect_size=True,
        supports_confidence_interval=False,
        supports_visualization=True,
    ),
    "chi_square": MethodCatalogItem(
        method="chi_square",
        name="Chi-Square Test of Independence",
        category="Association",
        description="Tests statistical association between two categorical variables with full contingency tables and Cramér's V.",
        required_inputs={"target_columns": "2 categorical columns"},
        supported_data_types=["categorical"],
        assumptions=["Independent observations", "Expected cell count >= 5 in at least 80% of cells"],
        supports_effect_size=True,
        supports_confidence_interval=False,
        supports_visualization=True,
    ),
    "fisher_exact": MethodCatalogItem(
        method="fisher_exact",
        name="Fisher's Exact Test (2×2)",
        category="Association",
        description="Exact test for association in 2×2 contingency tables, robust to sparse or small counts.",
        required_inputs={"target_columns": "2 binary categorical columns"},
        supported_data_types=["categorical", "boolean"],
        assumptions=["Independent observations", "2×2 contingency table"],
        supports_effect_size=True,
        supports_confidence_interval=True,
        supports_visualization=True,
    ),

    # ── Regression ──
    "ols_regression": MethodCatalogItem(
        method="ols_regression",
        name="Ordinary Least Squares (OLS) Linear Regression",
        category="Regression",
        description="Inferential linear regression with coefficient standard errors, t-tests, CIs, R², VIF, and heteroscedasticity diagnostics.",
        required_inputs={"target_columns": "1 numeric outcome (Y)", "group_columns": "1 or more numeric predictors (X)"},
        supported_data_types=["numeric"],
        assumptions=["Linearity", "Independence of errors", "Homoscedasticity (constant variance)", "Normal residuals", "No extreme multicollinearity (VIF < 5)"],
        supports_effect_size=True,
        supports_confidence_interval=True,
        supports_visualization=True,
    ),
}


def get_all_catalog_items() -> List[MethodCatalogItem]:
    """Returns list of all registered statistical methods in the catalog."""
    return list(STATISTICAL_METHODS_CATALOG.values())


def get_catalog_item(method_name: str) -> MethodCatalogItem:
    """Retrieves metadata for a specific method."""
    clean = method_name.lower().strip()
    return STATISTICAL_METHODS_CATALOG.get(clean, STATISTICAL_METHODS_CATALOG["descriptive_summary"])
