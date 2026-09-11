"""
AnalyzaX — Phase 10: Statistics Engine Coordinator
Central facade orchestrating deterministic statistical computations, assumption checks,
effect sizes, confidence intervals, structured interpretations, findings, and ChartSpecs.
Zero LLM or non-deterministic numerical computation (STAT-01 to STAT-05).
"""

from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional
import numpy as np
import polars as pl

from backend.app.engines.statistics.assumptions.independence import check_residual_independence
from backend.app.engines.statistics.assumptions.normality import check_normality
from backend.app.engines.statistics.assumptions.sample_size import check_sample_size_adequacy
from backend.app.engines.statistics.assumptions.variance import check_homogeneity_of_variance
from backend.app.engines.statistics.catalog import get_catalog_item
from backend.app.engines.statistics.interpretation.explanations import generate_structured_interpretation
from backend.app.engines.statistics.interpretation.findings import generate_statistical_findings
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
from backend.app.engines.statistics.methods.covariance import compute_covariance_matrix
from backend.app.engines.statistics.methods.descriptive import (
    compute_boolean_descriptive,
    compute_categorical_descriptive,
    compute_datetime_descriptive,
    compute_numeric_descriptive,
)
from backend.app.engines.statistics.methods.distribution import compute_distribution_analysis
from backend.app.engines.statistics.methods.group_comparison import (
    run_independent_ttest,
    run_kruskal_wallis,
    run_mann_whitney_u,
    run_oneway_anova,
    run_paired_ttest,
    run_wilcoxon_signed_rank,
)
from backend.app.engines.statistics.methods.regression import run_ols_regression
from backend.app.engines.statistics.models import (
    AssumptionCheck,
    AssumptionStatus,
    ConfidenceInterval,
    EffectSize,
    MissingDataReport,
    StatisticalAnalysisRequest,
    StatisticalResult,
)
from backend.app.engines.statistics.visualization.chart_specs import (
    build_contingency_chart_specs,
    build_correlation_chart_specs,
    build_distribution_chart_specs,
    build_group_comparison_chart_specs,
    build_regression_chart_specs,
)


class StatisticsEngine:
    """
    Pure analytical engine for statistical calculations.
    """
    ENGINE_VERSION = "10.0.0"

    def execute_analysis(
        self,
        df: pl.DataFrame,
        request: StatisticalAnalysisRequest,
    ) -> StatisticalResult:
        """
        Executes deterministic statistical computation according to request parameters.
        """
        method = str(request.method).lower().strip()
        analysis_type = str(request.analysis_type).lower().strip()
        params = request.parameters or {}
        alpha = float(params.get("alpha", 0.05))
        conf_level = float(params.get("confidence_level", 0.95))
        raw_alt = str(params.get("alternative", "two-sided"))
        alternative = raw_alt.replace("_", "-") if raw_alt in ("two_sided", "two-sided") else raw_alt

        # Initialize tracking structures
        assumptions: List[AssumptionCheck] = []
        effect_sizes: List[EffectSize] = []
        confidence_intervals: List[ConfidenceInterval] = []
        chart_specs: List[Dict[str, Any]] = []
        stats_dict: Dict[str, Any] = {}
        p_values_dict: Dict[str, Optional[float]] = {}
        diagnostics_dict: Dict[str, Any] = {}
        status_str = "COMPLETED"
        warnings_list: List[str] = []
        limitations_list: List[str] = []
        missing_report = MissingDataReport(
            original_observations=len(df),
            used_observations=len(df),
            excluded_observations=0,
            missing_policy=params.get("missing_data_policy", "listwise_deletion"),
        )

        catalog_item = get_catalog_item(method)
        method_name = catalog_item.name

        # ── 1. Descriptive Summary ──
        if method in ("descriptive_summary", "descriptive"):
            col_results = {}
            for col in request.target_columns:
                if col not in df.columns:
                    continue
                s = df[col]
                dtype_str = str(s.dtype).lower()
                if any(t in dtype_str for t in ["int", "float", "decimal"]):
                    arr = s.to_numpy()
                    res = compute_numeric_descriptive(arr, col, confidence_level=conf_level)
                    ci_data = res.get("confidence_interval_mean")
                    if ci_data:
                        confidence_intervals.append(ConfidenceInterval(**ci_data))
                elif "bool" in dtype_str:
                    res = compute_boolean_descriptive(s, col)
                elif any(t in dtype_str for t in ["date", "time"]):
                    res = compute_datetime_descriptive(s, col)
                else:
                    res = compute_categorical_descriptive(s, col)

                col_results[col] = res

            stats_dict = {"columns": col_results, **col_results}

        # ── 2. Distribution Analysis ──
        elif method in ("distribution_analysis", "distribution"):
            target_col = request.target_columns[0]
            arr = df[target_col].to_numpy()
            dist_res = compute_distribution_analysis(arr, target_col)
            stats_dict = dist_res

            # Assumption: Normality test
            norm_check = check_normality(arr, target_col, alpha=alpha)
            assumptions.append(norm_check)

            # Generate ChartSpecs
            chart_specs = build_distribution_chart_specs(
                dist_res, request.dataset_id, request.dataset_version_id, target_col
            )

        # ── 3. Independent Group Comparison (Welch / Student t / Mann-Whitney) ──
        elif method in ("t_test_welch", "t_test_ind", "mann_whitney_u"):
            target_col = request.target_columns[0]
            group_col = request.group_columns[0]

            unique_groups = df[group_col].drop_nulls().unique().to_list()
            if len(unique_groups) != 2:
                status_str = "INSUFFICIENT_DATA"
                stats_dict = {"error": f"Two-group comparison requires exactly 2 levels in '{group_col}', found {len(unique_groups)}."}
            else:
                g1_name, g2_name = str(unique_groups[0]), str(unique_groups[1])
                g1_vals = df.filter(pl.col(group_col) == unique_groups[0])[target_col].to_numpy()
                g2_vals = df.filter(pl.col(group_col) == unique_groups[1])[target_col].to_numpy()

                # Run test
                if method == "mann_whitney_u":
                    comp_res = run_mann_whitney_u(
                        g1_vals, g2_vals, g1_name, g2_name, target_col, alpha=alpha, alternative=alternative
                    )
                else:
                    equal_v = bool(method == "t_test_ind")
                    comp_res = run_independent_ttest(
                        g1_vals, g2_vals, g1_name, g2_name, target_col, equal_var=equal_v, alpha=alpha, alternative=alternative, confidence_level=conf_level
                    )

                stats_dict = comp_res
                status_str = comp_res.get("status", "COMPLETED")
                if "missing_report" in comp_res:
                    missing_report = MissingDataReport(**comp_res["missing_report"])

                p_val = comp_res.get("p_value")
                p_values_dict["primary"] = p_val

                # Assumptions: Normality in each group & Equal Variance
                assumptions.append(check_normality(g1_vals, f"{target_col} ({g1_name})", alpha=alpha))
                assumptions.append(check_normality(g2_vals, f"{target_col} ({g2_name})", alpha=alpha))
                assumptions.append(check_homogeneity_of_variance({g1_name: g1_vals, g2_name: g2_vals}, target_col, alpha=alpha))
                assumptions.append(check_sample_size_adequacy({g1_name: len(g1_vals), g2_name: len(g2_vals)}, "two_group_comparison"))

                # Effect sizes & CIs
                for eff in comp_res.get("effect_sizes", []):
                    effect_sizes.append(EffectSize(**eff))
                ci_data = comp_res.get("confidence_interval")
                if ci_data:
                    confidence_intervals.append(ConfidenceInterval(**ci_data))

                # ChartSpecs
                chart_specs = build_group_comparison_chart_specs(
                    comp_res, request.dataset_id, request.dataset_version_id, target_col, group_col
                )

        # ── 4. Paired Group Comparison (Paired t / Wilcoxon) ──
        elif method in ("t_test_paired", "wilcoxon"):
            col1 = request.target_columns[0]
            col2 = request.target_columns[1]
            v1 = df[col1].to_numpy()
            v2 = df[col2].to_numpy()

            if method == "wilcoxon":
                comp_res = run_wilcoxon_signed_rank(v1, v2, col1, col2, f"{col1} vs {col2}", alpha=alpha, alternative=alternative)
            else:
                comp_res = run_paired_ttest(v1, v2, col1, col2, f"{col1} vs {col2}", alpha=alpha, alternative=alternative, confidence_level=conf_level)

            stats_dict = comp_res
            status_str = comp_res.get("status", "COMPLETED")
            if "missing_report" in comp_res:
                missing_report = MissingDataReport(**comp_res["missing_report"])

            p_values_dict["primary"] = comp_res.get("p_value")

            # Assumptions: Normality of differences
            diffs = v1 - v2
            assumptions.append(check_normality(diffs, f"Differences ({col1} - {col2})", alpha=alpha))
            assumptions.append(check_sample_size_adequacy({"paired_cohort": len(diffs)}, "paired_comparison"))

            for eff in comp_res.get("effect_sizes", []):
                effect_sizes.append(EffectSize(**eff))
            ci_data = comp_res.get("confidence_interval")
            if ci_data:
                confidence_intervals.append(ConfidenceInterval(**ci_data))

        # ── 5. Multi-group Comparison (ANOVA / Kruskal-Wallis) ──
        elif method in ("anova_oneway", "kruskal_wallis"):
            target_col = request.target_columns[0]
            group_col = request.group_columns[0]

            unique_groups = df[group_col].drop_nulls().unique().to_list()
            groups_dict = {
                str(g): df.filter(pl.col(group_col) == g)[target_col].to_numpy()
                for g in unique_groups
            }

            if method == "kruskal_wallis":
                comp_res = run_kruskal_wallis(groups_dict, target_col, alpha=alpha)
            else:
                comp_res = run_oneway_anova(groups_dict, target_col, alpha=alpha)

            stats_dict = comp_res
            status_str = comp_res.get("status", "COMPLETED")
            if "missing_report" in comp_res:
                missing_report = MissingDataReport(**comp_res["missing_report"])

            p_values_dict["primary"] = comp_res.get("p_value")

            # Assumptions: Homogeneity of variance & Sample size
            assumptions.append(check_homogeneity_of_variance(groups_dict, target_col, alpha=alpha))
            assumptions.append(check_sample_size_adequacy({k: len(v) for k, v in groups_dict.items()}, "multigroup_comparison"))

            for eff in comp_res.get("effect_sizes", []):
                effect_sizes.append(EffectSize(**eff))

            chart_specs = build_group_comparison_chart_specs(
                comp_res, request.dataset_id, request.dataset_version_id, target_col, group_col
            )

        # ── 6. Correlation (Pearson, Spearman, Kendall, Matrix) ──
        elif method in ("pearson", "spearman", "kendall"):
            x_name = request.target_columns[0]
            y_name = request.target_columns[1]
            x_vals = df[x_name].to_numpy()
            y_vals = df[y_name].to_numpy()

            corr_res = compute_bivariate_correlation(
                x_vals, y_vals, x_name, y_name, method=method, confidence_level=conf_level, alpha=alpha
            )
            stats_dict = corr_res
            status_str = corr_res.get("status", "COMPLETED")
            if "missing_report" in corr_res:
                missing_report = MissingDataReport(**corr_res["missing_report"])

            p_values_dict["primary"] = corr_res.get("p_value")
            if corr_res.get("effect_size"):
                effect_sizes.append(EffectSize(**corr_res["effect_size"]))
            if corr_res.get("confidence_interval"):
                confidence_intervals.append(ConfidenceInterval(**corr_res["confidence_interval"]))

            # Assumptions: Normality of both variables
            assumptions.append(check_normality(x_vals, x_name, alpha=alpha))
            assumptions.append(check_normality(y_vals, y_name, alpha=alpha))

        elif method == "correlation_matrix":
            cols_dict = {col: df[col].to_numpy() for col in request.target_columns if col in df.columns}
            corr_mat_res = compute_correlation_matrix(
                cols_dict, method=params.get("correlation_method", "pearson"), alpha=alpha
            )
            stats_dict = corr_mat_res
            chart_specs = build_correlation_chart_specs(
                corr_mat_res, request.dataset_id, request.dataset_version_id
            )

        elif method == "covariance_matrix":
            cols_dict = {col: df[col].to_numpy() for col in request.target_columns if col in df.columns}
            cov_res = compute_covariance_matrix(cols_dict)
            stats_dict = cov_res

        # ── 7. Categorical Association (Chi-Square / Fisher Exact) ──
        elif method in ("chi_square", "fisher_exact"):
            col1 = request.target_columns[0]
            col2 = request.target_columns[1] if len(request.target_columns) > 1 else request.group_columns[0]

            v1_list = df[col1].to_list()
            v2_list = df[col2].to_list()

            cat_res = run_categorical_association(
                v1_list, v2_list, col1, col2, alpha=alpha, prefer_fisher=(method == "fisher_exact")
            )
            stats_dict = cat_res
            status_str = cat_res.get("status", "COMPLETED")
            if "missing_report" in cat_res:
                missing_report = MissingDataReport(**cat_res["missing_report"])

            p_values_dict["primary"] = cat_res.get("p_value")
            for eff in cat_res.get("effect_sizes", []):
                effect_sizes.append(EffectSize(**eff))

            # Assumption: Sparsity
            sparsity = cat_res.get("sparsity_check", {})
            if not sparsity.get("assumption_satisfied", True):
                assumptions.append(
                    AssumptionCheck(
                        check_id="chi_square_sparsity",
                        assumption="Expected Frequency Adequacy",
                        status=AssumptionStatus.WARNING,
                        severity=FindingSeverity.MEDIUM,
                        method="Cochran's Criterion Check",
                        statistic=sparsity.get("percentage_under_5"),
                        p_value=None,
                        evidence=f"{sparsity.get('percentage_under_5')}% of contingency cells have expected counts < 5.",
                        description="Chi-Square test may underestimate true p-values when expected cell counts are sparse.",
                        recommendation="Consider combining categories or using Fisher's exact test.",
                    )
                )

            chart_specs = build_contingency_chart_specs(
                cat_res, request.dataset_id, request.dataset_version_id, col1, col2
            )

        # ── 8. Inferential OLS Regression ──
        elif method == "ols_regression":
            y_name = request.target_columns[0]
            x_names = request.group_columns or [c for c in request.target_columns[1:] if c in df.columns]

            y_arr = df[y_name].to_numpy()
            X_arr = df.select(x_names).to_numpy()

            reg_res = run_ols_regression(
                y_arr, X_arr, y_name, x_names, confidence_level=conf_level, alpha=alpha
            )
            stats_dict = reg_res
            status_str = reg_res.get("status", "COMPLETED")
            if "missing_report" in reg_res:
                missing_report = MissingDataReport(**reg_res["missing_report"])

            p_values_dict["primary"] = reg_res.get("f_p_value")
            diagnostics_dict = reg_res.get("diagnostics", {})

            # Convert regression coefficients to CIs
            for coeff in reg_res.get("coefficients", []):
                p_values_dict[coeff["parameter"]] = coeff["p_value"]
                ci_range = coeff.get("confidence_interval")
                if ci_range:
                    confidence_intervals.append(
                        ConfidenceInterval(
                            level=conf_level,
                            lower=ci_range[0],
                            upper=ci_range[1],
                            metric_name=f"beta_{coeff['parameter']}",
                            standard_error=coeff["standard_error"],
                        )
                    )

            # Assumptions from diagnostics
            bp = diagnostics_dict.get("breusch_pagan", {})
            assumptions.append(
                AssumptionCheck(
                    check_id="homoscedasticity_breusch_pagan",
                    assumption="Constant Variance (Homoscedasticity)",
                    status=AssumptionStatus.WARNING if bp.get("heteroscedasticity_concern") else AssumptionStatus.PASS,
                    severity=FindingSeverity.MEDIUM if bp.get("heteroscedasticity_concern") else FindingSeverity.INFO,
                    method="Breusch-Pagan Test",
                    statistic=bp.get("statistic"),
                    p_value=bp.get("p_value"),
                    evidence="Potential heteroscedasticity detected" if bp.get("heteroscedasticity_concern") else "Residual variance is consistent across fitted values.",
                    description="Assesses whether error variances are constant across levels of predictors.",
                    recommendation="Use robust standard errors (HC3) if severe." if bp.get("heteroscedasticity_concern") else None,
                )
            )

            dw = diagnostics_dict.get("durbin_watson", {})
            assumptions.append(
                AssumptionCheck(
                    check_id="independence_durbin_watson",
                    assumption="Independence of Errors",
                    status=AssumptionStatus.WARNING if dw.get("autocorrelation_concern") else AssumptionStatus.PASS,
                    severity=FindingSeverity.LOW if dw.get("autocorrelation_concern") else FindingSeverity.INFO,
                    method="Durbin-Watson Test",
                    statistic=dw.get("statistic"),
                    p_value=None,
                    evidence=f"DW statistic={dw.get('statistic')}",
                    description="Assesses autocorrelation in residual errors.",
                    recommendation="Check observation ordering if sequential." if dw.get("autocorrelation_concern") else None,
                )
            )

            res_norm = diagnostics_dict.get("residual_normality", {})
            assumptions.append(
                AssumptionCheck(
                    check_id="normality_residuals",
                    assumption="Normality of Residuals",
                    status=AssumptionStatus.PASS if res_norm.get("normal_residuals") else AssumptionStatus.WARNING,
                    severity=FindingSeverity.LOW if not res_norm.get("normal_residuals") else FindingSeverity.INFO,
                    method=res_norm.get("test", "Shapiro-Wilk"),
                    statistic=res_norm.get("statistic"),
                    p_value=res_norm.get("p_value"),
                    evidence=f"Residual normality p={res_norm.get('p_value')}",
                    description="OLS assumes normally distributed error terms for exact small-sample inference.",
                    recommendation="Inspect Q-Q residual plot." if not res_norm.get("normal_residuals") else None,
                )
            )

            chart_specs = build_regression_chart_specs(
                reg_res, request.dataset_id, request.dataset_version_id, y_name, x_names[0]
            )

        # ── Deterministic Findings & Explanations ──
        findings = generate_statistical_findings(
            analysis_type=analysis_type,
            method=method,
            target_columns=request.target_columns,
            statistics=stats_dict,
            p_values=p_values_dict,
            effect_sizes=[e.model_dump() for e in effect_sizes],
            assumptions=assumptions,
            missing_data=missing_report.model_dump(),
            alpha=alpha,
        )

        interpretation = generate_structured_interpretation(
            analysis_type=analysis_type,
            method=method,
            method_name=method_name,
            target_columns=request.target_columns,
            group_columns=request.group_columns,
            statistics=stats_dict,
            p_values=p_values_dict,
            effect_sizes=[e.model_dump() for e in effect_sizes],
            assumptions_summary=[a.model_dump() for a in assumptions],
            missing_data=missing_report.model_dump(),
            alpha=alpha,
        )

        if "primary" in p_values_dict and "p_value" not in p_values_dict:
            p_values_dict["p_value"] = p_values_dict["primary"]

        provenance_dict = {
            "statistics_engine_version": self.ENGINE_VERSION,
            "engine_version": self.ENGINE_VERSION,
            "dataset_id": request.dataset_id,
            "dataset_version_id": request.dataset_version_id,
            "analysis_type": analysis_type,
            "method": method,
            "target_columns": request.target_columns,
            "group_columns": request.group_columns,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "deterministic_libraries": ["scipy", "statsmodels", "numpy", "polars"],
            "software_versions": {
                "scipy": "1.15.0",
                "statsmodels": "0.15.0",
                "numpy": "2.2.0",
                "polars": "1.24.0",
            },
        }

        # Warnings and limitations
        if "warnings" in stats_dict:
            warnings_list.extend(stats_dict["warnings"])
        limitations_list.extend(interpretation.get("limitations", []))

        return StatisticalResult(
            result_id=f"res_{request.analysis_id}",
            dataset_id=request.dataset_id,
            dataset_version_id=request.dataset_version_id,
            analysis_type=analysis_type,
            method=method,
            status=status_str,
            inputs={
                "target_columns": request.target_columns,
                "group_columns": request.group_columns,
            },
            parameters=params,
            missing_data_report=missing_report,
            statistics=stats_dict,
            p_values=p_values_dict,
            effect_sizes=effect_sizes,
            confidence_intervals=confidence_intervals,
            assumptions=assumptions,
            diagnostics=diagnostics_dict,
            interpretation=interpretation,
            findings=findings,
            warnings=warnings_list,
            limitations=limitations_list,
            provenance=provenance_dict,
            chart_specs=chart_specs,
            created_at=datetime.now(timezone.utc).isoformat(),
        )


statistics_engine = StatisticsEngine()
