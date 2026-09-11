"""
AnalyzaX — Phase 10: Statistical Models & Schema Contracts
Strictly typed Pydantic models for statistical analysis requests, results,
findings, assumption checks, confidence intervals, effect sizes, and diagnostics.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import uuid
from pydantic import BaseModel, Field


class AnalysisType(str, Enum):
    DESCRIPTIVE = "descriptive"
    DISTRIBUTION = "distribution"
    NORMALITY = "normality"
    CONFIDENCE_INTERVAL = "confidence_interval"
    HYPOTHESIS_TEST = "hypothesis_test"
    CORRELATION = "correlation"
    COVARIANCE = "covariance"
    CATEGORICAL_ASSOCIATION = "categorical_association"
    GROUP_COMPARISON = "group_comparison"
    REGRESSION = "regression"
    DIAGNOSTICS = "diagnostics"


class StatisticalMethod(str, Enum):
    # Descriptive & Distribution
    DESCRIPTIVE_SUMMARY = "descriptive_summary"
    DISTRIBUTION_ANALYSIS = "distribution_analysis"
    NORMALITY_TEST = "normality_test"

    # Confidence Intervals
    CONFIDENCE_INTERVAL_MEAN = "ci_mean"
    CONFIDENCE_INTERVAL_PROPORTION = "ci_proportion"
    CONFIDENCE_INTERVAL_DIFF_MEANS = "ci_diff_means"
    CONFIDENCE_INTERVAL_DIFF_PROPORTIONS = "ci_diff_proportions"

    # Two-group comparisons
    T_TEST_IND = "t_test_ind"          # Student's independent t-test (equal_var=True)
    T_TEST_WELCH = "t_test_welch"      # Welch's independent t-test (equal_var=False)
    T_TEST_PAIRED = "t_test_paired"    # Paired t-test
    MANN_WHITNEY_U = "mann_whitney_u"  # Mann-Whitney U non-parametric
    WILCOXON_SIGNED_RANK = "wilcoxon"  # Wilcoxon signed-rank paired

    # Multi-group comparisons
    ANOVA_ONEWAY = "anova_oneway"      # One-way ANOVA with Tukey HSD post-hoc
    KRUSKAL_WALLIS = "kruskal_wallis"  # Kruskal-Wallis non-parametric

    # Correlation & Covariance
    PEARSON_CORRELATION = "pearson"
    SPEARMAN_CORRELATION = "spearman"
    KENDALL_CORRELATION = "kendall"
    CORRELATION_MATRIX = "correlation_matrix"
    COVARIANCE_MATRIX = "covariance_matrix"

    # Categorical association
    CHI_SQUARE_INDEPENDENCE = "chi_square"
    FISHER_EXACT = "fisher_exact"

    # Regression
    OLS_REGRESSION = "ols_regression"


class AssumptionStatus(str, Enum):
    NOT_CHECKED = "NOT_CHECKED"
    PASS = "PASS"
    WARNING = "WARNING"
    VIOLATION = "VIOLATION"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class FindingCategory(str, Enum):
    SIGNIFICANT_DIFFERENCE = "SIGNIFICANT_DIFFERENCE"
    STRONG_ASSOCIATION = "STRONG_ASSOCIATION"
    WEAK_ASSOCIATION = "WEAK_ASSOCIATION"
    POTENTIAL_EFFECT = "POTENTIAL_EFFECT"
    DISTRIBUTION_CONCERN = "DISTRIBUTION_CONCERN"
    ASSUMPTION_WARNING = "ASSUMPTION_WARNING"
    OUTLIER_CONCERN = "OUTLIER_CONCERN"
    MULTICOLLINEARITY = "MULTICOLLINEARITY"
    HETEROSCEDASTICITY = "HETEROSCEDASTICITY"
    INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"
    MISSING_DATA_CONCERN = "MISSING_DATA_CONCERN"


class FindingSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MultipleTestingMethod(str, Enum):
    NONE = "none"
    BONFERRONI = "bonferroni"
    HOLM = "holm"
    BENJAMINI_HOCHBERG = "fdr_bh"


class AnalysisStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    WARNING = "WARNING"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NUMERICAL_FAILURE = "NUMERICAL_FAILURE"


class MissingDataPolicy(str, Enum):
    LISTWISE = "LISTWISE"
    PAIRWISE = "PAIRWISE"
    METHOD_DEFAULT = "METHOD_DEFAULT"


class AlternativeHypothesis(str, Enum):
    TWO_SIDED = "two_sided"
    GREATER = "greater"
    LESS = "less"


class StatisticValue(BaseModel):
    name: str
    value: float
    unit: Optional[str] = None
    description: Optional[str] = None


class PValue(BaseModel):
    value: float
    formatted: str
    comparison: str = "equal"
    adjusted: bool = False
    adjustment_method: Optional[str] = None


class Diagnostic(BaseModel):
    diagnostic_type: str
    status: str
    metric: str
    value: float
    threshold: Optional[float] = None
    evidence: str
    description: str


class StatisticalWarning(BaseModel):
    code: str
    severity: str
    message: str


class StatisticalLimitation(BaseModel):
    code: str
    message: str


class MissingDataReport(BaseModel):
    original_observations: int
    used_observations: int
    excluded_observations: int
    missing_policy: str = "listwise_deletion"
    exclusion_reason: Optional[str] = None


class ConfidenceInterval(BaseModel):
    level: float = Field(0.95, description="Confidence level e.g. 0.90, 0.95, 0.99")
    lower: float
    upper: float
    metric_name: str
    standard_error: Optional[float] = None
    margin_of_error: Optional[float] = None
    estimate: Optional[float] = None
    parameter: Optional[str] = None
    method: Optional[str] = None


class EffectSize(BaseModel):
    metric_name: str = Field(..., description="e.g. cohen_d, hedges_g, eta_squared, cramer_v, r")
    value: float
    interpretation: str = Field(..., description="negligible, small, medium, large")
    confidence_interval: Optional[ConfidenceInterval] = None


class AssumptionCheck(BaseModel):
    check_id: str
    assumption: str
    status: AssumptionStatus
    severity: FindingSeverity
    method: str
    statistic: Optional[float] = None
    p_value: Optional[float] = None
    evidence: str
    description: str
    recommendation: Optional[str] = None


class StatisticalFinding(BaseModel):
    finding_id: str
    category: FindingCategory
    severity: FindingSeverity
    title: str
    description: str
    columns: List[str]
    method: str
    statistics: Dict[str, Any] = Field(default_factory=dict)
    effect_size: Optional[Dict[str, Any]] = None
    confidence_interval: Optional[Dict[str, Any]] = None
    p_value: Optional[float] = None
    adjusted_p_value: Optional[float] = None
    evidence: str
    confidence: float = 1.0
    limitations: List[str] = Field(default_factory=list)


class StatisticalAnalysisRequest(BaseModel):
    analysis_id: str = Field(default_factory=lambda: f"stat_{uuid.uuid4().hex[:10]}")
    workspace_id: Optional[str] = None
    dataset_id: str
    dataset_version_id: str
    analysis_type: Union[AnalysisType, str]
    method: Union[StatisticalMethod, str]
    target_columns: List[str] = Field(default_factory=list)
    group_columns: List[str] = Field(default_factory=list)
    inputs: Optional[Dict[str, Any]] = None
    parameters: Dict[str, Any] = Field(
        default_factory=lambda: {
            "alpha": 0.05,
            "confidence_level": 0.95,
            "alternative": "two_sided",
            "multiple_testing": "none",
            "missing_data_policy": "listwise_deletion",
        }
    )
    missing_data_policy: Optional[Union[MissingDataPolicy, str]] = None
    multiple_testing: Optional[Dict[str, Any]] = None
    options: Optional[Dict[str, Any]] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def model_post_init(self, __context: Any) -> None:
        if self.inputs:
            if "outcome_columns" in self.inputs and not self.target_columns:
                self.target_columns = list(self.inputs["outcome_columns"])
            elif "target_columns" in self.inputs and not self.target_columns:
                self.target_columns = list(self.inputs["target_columns"])
            if "group_column" in self.inputs and not self.group_columns:
                val = self.inputs["group_column"]
                self.group_columns = [val] if isinstance(val, str) else list(val)
            elif "group_columns" in self.inputs and not self.group_columns:
                self.group_columns = list(self.inputs["group_columns"])


class StatisticalResult(BaseModel):
    schema_version: str = "statistics_result_v1"
    result_id: str
    analysis_id: Optional[str] = None
    dataset_id: str
    dataset_version_id: str
    analysis_type: str
    method: str
    status: Union[AnalysisStatus, str] = AnalysisStatus.COMPLETED.value
    inputs: Dict[str, Any]
    parameters: Dict[str, Any]
    missing_data_report: MissingDataReport
    sample: Optional[Dict[str, Any]] = None
    statistics: Dict[str, Any] = Field(default_factory=dict)
    p_values: Dict[str, Optional[float]] = Field(default_factory=dict)
    effect_sizes: List[EffectSize] = Field(default_factory=list)
    confidence_intervals: List[ConfidenceInterval] = Field(default_factory=list)
    assumptions: List[AssumptionCheck] = Field(default_factory=list)
    diagnostics: Dict[str, Any] = Field(default_factory=dict)
    interpretation: Dict[str, Any] = Field(default_factory=dict)
    findings: List[StatisticalFinding] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    chart_specs: List[Dict[str, Any]] = Field(default_factory=list)
    visualizations: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def model_post_init(self, __context: Any) -> None:
        if not self.analysis_id:
            self.analysis_id = self.result_id
        if self.missing_data_report and not self.sample:
            self.sample = {
                "available_rows": self.missing_data_report.original_observations,
                "analyzed_rows": self.missing_data_report.used_observations,
                "excluded_rows": self.missing_data_report.excluded_observations,
                "missing_rows": self.missing_data_report.excluded_observations,
            }
        if self.chart_specs and not self.visualizations:
            self.visualizations = [
                {
                    "visualization_id": f"viz_{self.result_id}_{idx}",
                    "chart_spec": spec
                }
                for idx, spec in enumerate(self.chart_specs)
            ]


class MethodCatalogItem(BaseModel):
    method: str
    name: str
    category: str
    description: str
    required_inputs: Dict[str, str]
    supported_data_types: List[str]
    assumptions: List[str]
    supports_effect_size: bool
    supports_confidence_interval: bool
    supports_visualization: bool


class MethodRecommendationRequest(BaseModel):
    dataset_id: str
    dataset_version_id: str
    target_columns: List[str]
    group_columns: Optional[List[str]] = Field(default_factory=list)
    intent: Optional[str] = None  # "compare_two", "compare_multi", "association", "relationship", "regression"


class MethodRecommendation(BaseModel):
    recommended_method: str
    recommended_name: str
    alternative_methods: List[str]
    rationale: List[str]
    required_assumptions: List[str]
    warnings: List[str] = Field(default_factory=list)


class ValidationResponse(BaseModel):
    is_valid: bool
    issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    missing_data_report: Optional[MissingDataReport] = None
