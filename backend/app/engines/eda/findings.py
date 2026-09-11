"""
AnalyzaX — Phase 7: Automated EDA Findings Engine
Rule-based, deterministic analytical findings generator.
Extracts grounded, non-causal statistical insights across 8 categories without any LLM dependency.
"""

import uuid
from typing import Any, Dict, List, Optional

from backend.app.engines.eda.models import (
    CardinalityAnalysis,
    CorrelationMatrix,
    DatetimeAnalysis,
    EDAOverview,
    EDAFinding,
    FindingCategory,
    FindingConfidence,
    FindingSeverity,
    MissingnessAnalysis,
    NumericNumericRelationship,
    OutlierAnalysis,
    UnivariateCategorical,
    UnivariateNumeric,
)


class EDAFindingsEngine:
    @staticmethod
    def generate_findings(
        overview: EDAOverview,
        numeric_analyses: List[UnivariateNumeric],
        categorical_analyses: List[UnivariateCategorical],
        datetime_analyses: List[DatetimeAnalysis],
        correlation: Optional[CorrelationMatrix],
        numeric_relationships: List[NumericNumericRelationship],
        missingness: Optional[MissingnessAnalysis],
        outliers: Optional[OutlierAnalysis],
        cardinality: Optional[CardinalityAnalysis],
    ) -> List[EDAFinding]:
        findings: List[EDAFinding] = []

        # 1. DATA_HEALTH Findings
        if overview.duplicate_rows > 0:
            sev = FindingSeverity.HIGH if overview.duplicate_percentage > 10.0 else FindingSeverity.MEDIUM
            findings.append(
                EDAFinding(
                    finding_id=f"find_dup_{uuid.uuid4().hex[:8]}",
                    category=FindingCategory.DATA_HEALTH,
                    severity=sev,
                    title="Duplicate Rows Detected",
                    description=f"Dataset contains {overview.duplicate_rows} duplicate rows ({overview.duplicate_percentage}% of total). Duplicate rows can distort aggregations and model evaluations.",
                    evidence=f"Identified {overview.duplicate_rows} exact row matches across {overview.row_count} total records.",
                    columns=[],
                    statistics={
                        "duplicate_rows": overview.duplicate_rows,
                        "duplicate_percentage": overview.duplicate_percentage,
                    },
                    confidence=FindingConfidence.HIGH,
                    methodology="Exact tuple matching across all columns.",
                )
            )

        if overview.quality_score is not None and overview.quality_score < 70.0:
            findings.append(
                EDAFinding(
                    finding_id=f"find_qual_{uuid.uuid4().hex[:8]}",
                    category=FindingCategory.DATA_HEALTH,
                    severity=FindingSeverity.HIGH if overview.quality_score < 50.0 else FindingSeverity.MEDIUM,
                    title="Sub-optimal Data Quality Score",
                    description=f"Dataset overall quality score is {overview.quality_score:.1f}/100. Issues with missing values, format validity, or duplicates should be reviewed in the Cleaning module.",
                    evidence=f"Composite quality score calculated at {overview.quality_score:.1f}/100.",
                    columns=[],
                    statistics={"quality_score": overview.quality_score},
                    confidence=FindingConfidence.HIGH,
                    methodology="Composite weighted scoring across completeness, validity, uniqueness, and consistency.",
                )
            )

        # 2. MISSINGNESS Findings
        if missingness:
            if missingness.overall_missing_percentage > 15.0:
                findings.append(
                    EDAFinding(
                        finding_id=f"find_miss_{uuid.uuid4().hex[:8]}",
                        category=FindingCategory.MISSINGNESS,
                        severity=FindingSeverity.HIGH if missingness.overall_missing_percentage > 30.0 else FindingSeverity.MEDIUM,
                        title="Significant Missing Data Observed",
                        description=f"Overall dataset missingness is {missingness.overall_missing_percentage}%, totaling {missingness.total_missing_cells} empty cells. Only {missingness.complete_rows_count} records are fully complete.",
                        evidence=f"{missingness.total_missing_cells} null cells across {missingness.total_cells} total cells.",
                        columns=[],
                        statistics={
                            "overall_missing_percentage": missingness.overall_missing_percentage,
                            "complete_rows_count": missingness.complete_rows_count,
                            "incomplete_rows_count": missingness.incomplete_rows_count,
                        },
                        confidence=FindingConfidence.HIGH,
                        methodology="Null cell aggregation and row-level completeness computation.",
                    )
                )

            for col_m in missingness.column_missingness:
                if col_m.missing_percentage > 25.0:
                    findings.append(
                        EDAFinding(
                            finding_id=f"find_col_miss_{uuid.uuid4().hex[:8]}",
                            category=FindingCategory.MISSINGNESS,
                            severity=FindingSeverity.HIGH if col_m.missing_percentage > 50.0 else FindingSeverity.MEDIUM,
                            title=f"High Missingness in '{col_m.column}'",
                            description=f"Column '{col_m.column}' is missing {col_m.missing_percentage}% of its values ({col_m.missing_count} rows). Consider imputation or dropping if uninformative.",
                            evidence=f"Column has {col_m.missing_count} nulls out of {overview.row_count} rows ({col_m.missing_percentage}%).",
                            columns=[col_m.column],
                            statistics={"missing_count": col_m.missing_count, "missing_percentage": col_m.missing_percentage},
                            confidence=FindingConfidence.HIGH,
                            methodology="Univariate null check.",
                        )
                    )

            for co in missingness.cooccurrences[:3]:
                if co.both_missing_count > 5 and co.cooccurrence_ratio > 0.6:
                    findings.append(
                        EDAFinding(
                            finding_id=f"find_co_miss_{uuid.uuid4().hex[:8]}",
                            category=FindingCategory.MISSINGNESS,
                            severity=FindingSeverity.LOW,
                            title=f"Missingness Co-occurrence: '{co.column_a}' & '{co.column_b}'",
                            description=f"Columns '{co.column_a}' and '{co.column_b}' tend to be missing together ({co.both_missing_count} rows co-missing, {co.cooccurrence_ratio * 100:.1f}% alignment). This may indicate systematic non-response or structural missingness.",
                            evidence=f"{co.both_missing_count} records have null values in both columns simultaneously.",
                            columns=[co.column_a, co.column_b],
                            statistics={"both_missing_count": co.both_missing_count, "cooccurrence_ratio": co.cooccurrence_ratio},
                            confidence=FindingConfidence.MEDIUM,
                            methodology="Bivariate pairwise null intersection.",
                        )
                    )

        # 3. DISTRIBUTION Findings
        for num in numeric_analyses:
            # Skewness
            if num.skewness is not None:
                if abs(num.skewness) > 1.5:
                    direction = "right-skewed (positive tail)" if num.skewness > 0 else "left-skewed (negative tail)"
                    findings.append(
                        EDAFinding(
                            finding_id=f"find_skew_{uuid.uuid4().hex[:8]}",
                            category=FindingCategory.DISTRIBUTION,
                            severity=FindingSeverity.LOW,
                            title=f"Substantial Skewness in '{num.column}'",
                            description=f"Column '{num.column}' exhibits a skewness coefficient of {num.skewness:.2f}, indicating a highly {direction} distribution. Median ({num.median}) may be a more representative central metric than mean ({num.mean}).",
                            evidence=f"Fisher-Pearson skewness = {num.skewness:.4f}; Mean = {num.mean}, Median = {num.median}.",
                            columns=[num.column],
                            statistics={"skewness": num.skewness, "mean": num.mean, "median": num.median},
                            chart_reference=f"hist_{num.column}",
                            confidence=FindingConfidence.HIGH,
                            methodology="Fisher-Pearson sample-adjusted skewness.",
                        )
                    )

            # High zero proportion
            if num.count > 0 and (num.zero_count / num.count) > 0.3:
                zero_pct = round((num.zero_count / num.count) * 100.0, 1)
                findings.append(
                    EDAFinding(
                        finding_id=f"find_zero_{uuid.uuid4().hex[:8]}",
                        category=FindingCategory.DISTRIBUTION,
                        severity=FindingSeverity.LOW,
                        title=f"Zero-Inflation in '{num.column}'",
                        description=f"Column '{num.column}' contains {num.zero_count} zeros ({zero_pct}% of non-null entries). Zero-inflated distributions often represent inactive states or sparsity.",
                        evidence=f"{num.zero_count} zero values out of {num.count} valid rows.",
                        columns=[num.column],
                        statistics={"zero_count": num.zero_count, "zero_percentage": zero_pct},
                        chart_reference=f"hist_{num.column}",
                        confidence=FindingConfidence.HIGH,
                        methodology="Zero-value frequency threshold.",
                    )
                )

        # 4. RELATIONSHIP Findings
        if correlation and correlation.ranked_pairs:
            for pair in correlation.ranked_pairs:
                if pair.abs_correlation >= 0.7:
                    sign = "positive" if pair.correlation > 0 else "negative"
                    findings.append(
                        EDAFinding(
                            finding_id=f"find_corr_{uuid.uuid4().hex[:8]}",
                            category=FindingCategory.RELATIONSHIP,
                            severity=FindingSeverity.INFO,
                            title=f"Strong {sign.capitalize()} Correlation: '{pair.column_x}' & '{pair.column_y}'",
                            description=f"A {pair.strength} linear relationship exists between '{pair.column_x}' and '{pair.column_y}' (r = {pair.correlation:+.2f}). Changes in one feature strongly track the other.",
                            evidence=f"Pearson correlation coefficient r = {pair.correlation:.4f}.",
                            columns=[pair.column_x, pair.column_y],
                            statistics={"correlation": pair.correlation, "strength": pair.strength},
                            chart_reference=f"scatter_{pair.column_x}_{pair.column_y}",
                            confidence=FindingConfidence.HIGH,
                            methodology="Pairwise Pearson / Spearman correlation.",
                        )
                    )

        # Regression fits with high R^2
        for rel in numeric_relationships:
            if rel.regression and rel.regression.r_squared >= 0.6:
                findings.append(
                    EDAFinding(
                        finding_id=f"find_regr_{uuid.uuid4().hex[:8]}",
                        category=FindingCategory.RELATIONSHIP,
                        severity=FindingSeverity.INFO,
                        title=f"Strong Linear Fit: '{rel.column_x}' vs '{rel.column_y}'",
                        description=f"Linear regression demonstrates that '{rel.column_x}' accounts for {rel.regression.r_squared * 100:.1f}% of variance in '{rel.column_y}' (R² = {rel.regression.r_squared:.2f}, slope = {rel.regression.slope:.2f}).",
                        evidence=f"OLS regression R² = {rel.regression.r_squared:.4f}, slope = {rel.regression.slope:.4f}, intercept = {rel.regression.intercept:.4f}.",
                        columns=[rel.column_x, rel.column_y],
                        statistics={
                            "r_squared": rel.regression.r_squared,
                            "slope": rel.regression.slope,
                            "intercept": rel.regression.intercept,
                        },
                        chart_reference=f"scatter_{rel.column_x}_{rel.column_y}",
                        confidence=FindingConfidence.HIGH,
                        methodology="Ordinary Least Squares (OLS) linear model.",
                    )
                )

        # 5. ANOMALY / OUTLIER Findings
        if outliers:
            for out_col in outliers.columns_with_outliers:
                if out_col.outlier_percentage > 5.0:
                    findings.append(
                        EDAFinding(
                            finding_id=f"find_outlier_{uuid.uuid4().hex[:8]}",
                            category=FindingCategory.ANOMALY,
                            severity=FindingSeverity.MEDIUM if out_col.outlier_percentage > 10.0 else FindingSeverity.LOW,
                            title=f"Frequent Outliers in '{out_col.column}'",
                            description=f"Column '{out_col.column}' contains {out_col.outlier_count} statistical outliers ({out_col.outlier_percentage}% of records) falling outside the IQR fence [{out_col.lower_bound:.2f}, {out_col.upper_bound:.2f}].",
                            evidence=f"{out_col.outlier_count} values outside Tukey's bounds [{out_col.lower_bound}, {out_col.upper_bound}]. Sample extremes: {out_col.sample_extreme_values[:3]}.",
                            columns=[out_col.column],
                            statistics={
                                "outlier_count": out_col.outlier_count,
                                "outlier_percentage": out_col.outlier_percentage,
                                "lower_bound": out_col.lower_bound,
                                "upper_bound": out_col.upper_bound,
                            },
                            chart_reference=f"box_{out_col.column}",
                            confidence=FindingConfidence.HIGH,
                            methodology="Tukey's IQR outlier fences (1.5x IQR).",
                        )
                    )

        # 6. CATEGORY Findings
        for cat in categorical_analyses:
            if cat.dominant_category_percentage >= 80.0:
                top_cat_name = cat.top_categories[0].category if cat.top_categories else "Unknown"
                findings.append(
                    EDAFinding(
                        finding_id=f"find_cat_dom_{uuid.uuid4().hex[:8]}",
                        category=FindingCategory.CATEGORY,
                        severity=FindingSeverity.LOW,
                        title=f"Class Imbalance in '{cat.column}'",
                        description=f"The category '{top_cat_name}' dominates '{cat.column}' with {cat.dominant_category_percentage}% of non-null occurrences. High class imbalance can cause bias in analytical stratification.",
                        evidence=f"Top category accounts for {cat.dominant_category_percentage}% of {cat.count} valid rows.",
                        columns=[cat.column],
                        statistics={
                            "dominant_category": top_cat_name,
                            "dominant_percentage": cat.dominant_category_percentage,
                        },
                        chart_reference=f"bar_{cat.column}",
                        confidence=FindingConfidence.HIGH,
                        methodology="Categorical frequency dominance threshold (>= 80%).",
                    )
                )

        # 7. CARDINALITY Findings
        if cardinality:
            for const_col in cardinality.constant_columns:
                findings.append(
                    EDAFinding(
                        finding_id=f"find_const_{uuid.uuid4().hex[:8]}",
                        category=FindingCategory.CARDINALITY,
                        severity=FindingSeverity.MEDIUM,
                        title=f"Constant Column '{const_col}'",
                        description=f"Column '{const_col}' contains only a single unique value across all records. It contains zero predictive variance and may be discarded during data prep.",
                        evidence="n_unique = 1 across all records.",
                        columns=[const_col],
                        statistics={"unique_count": 1},
                        confidence=FindingConfidence.HIGH,
                        methodology="Unique count cardinality analysis.",
                    )
                )

            for id_col in cardinality.identifier_candidates:
                findings.append(
                    EDAFinding(
                        finding_id=f"find_id_{uuid.uuid4().hex[:8]}",
                        category=FindingCategory.CARDINALITY,
                        severity=FindingSeverity.INFO,
                        title=f"Candidate Identifier Detected: '{id_col}'",
                        description=f"Column '{id_col}' has very high uniqueness relative to total row count, making it a primary key or identifier candidate rather than a general analytic dimension.",
                        evidence=f"Identified as candidate based on high unique ratio and naming patterns.",
                        columns=[id_col],
                        statistics={"is_identifier_candidate": True},
                        confidence=FindingConfidence.HIGH,
                        methodology="Cardinality ratio and identifier heuristic evaluation.",
                    )
                )

        # 8. TIME Findings
        for dt in datetime_analyses:
            if dt.span_days is not None and dt.span_days > 0:
                findings.append(
                    EDAFinding(
                        finding_id=f"find_time_{uuid.uuid4().hex[:8]}",
                        category=FindingCategory.TIME,
                        severity=FindingSeverity.INFO,
                        title=f"Temporal Coverage in '{dt.column}'",
                        description=f"Date records in '{dt.column}' span approximately {dt.span_days:.0f} days ({dt.min_timestamp} to {dt.max_timestamp}) with inferred frequency '{dt.inferred_frequency}'.",
                        evidence=f"Min date = {dt.min_timestamp}, Max date = {dt.max_timestamp}, Span = {dt.span_days} days.",
                        columns=[dt.column],
                        statistics={
                            "min_timestamp": dt.min_timestamp,
                            "max_timestamp": dt.max_timestamp,
                            "span_days": dt.span_days,
                            "inferred_frequency": dt.inferred_frequency,
                        },
                        chart_reference=f"line_{dt.column}",
                        confidence=FindingConfidence.HIGH,
                        methodology="Timestamp range extraction and interval delta inference.",
                    )
                )

        return findings
