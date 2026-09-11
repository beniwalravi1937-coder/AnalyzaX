"""
AnalyzaX — Phase 11: Machine Learning Domain Contracts & Data Models.
Deterministic, version-aware, strictly typed Pydantic models for ML.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class MLTaskType(str, Enum):
    REGRESSION = "regression"
    BINARY_CLASSIFICATION = "binary_classification"
    MULTICLASS_CLASSIFICATION = "multiclass_classification"
    CLUSTERING = "clustering"


class MLJobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


class SuitabilitySeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SuitabilityIssue(BaseModel):
    code: str
    severity: SuitabilitySeverity
    column: Optional[str] = None
    title: str
    message: str
    action_recommendation: Optional[str] = None


class SuitabilityReport(BaseModel):
    is_suitable: bool
    summary: str
    issues: List[SuitabilityIssue] = Field(default_factory=list)
    dataset_row_count: int
    dataset_col_count: int
    recommended_task: Optional[MLTaskType] = None
    recommended_target: Optional[str] = None
    recommended_features: List[str] = Field(default_factory=list)
    excluded_features: Dict[str, str] = Field(default_factory=dict)
    class_distribution: Optional[Dict[str, int]] = None
    imbalance_ratio: Optional[float] = None


# Preprocessing configurations
class NumericImputeStrategy(str, Enum):
    MEDIAN = "median"
    MEAN = "mean"
    CONSTANT = "constant"


class NumericScaleStrategy(str, Enum):
    STANDARD = "standard"
    MINMAX = "minmax"
    ROBUST = "robust"
    PASSTHROUGH = "passthrough"


class CategoricalImputeStrategy(str, Enum):
    MOST_FREQUENT = "most_frequent"
    CONSTANT = "constant"


class CategoricalEncodeStrategy(str, Enum):
    ONE_HOT = "one_hot"
    ORDINAL = "ordinal"


class PreprocessingConfig(BaseModel):
    numeric_impute: NumericImputeStrategy = NumericImputeStrategy.MEDIAN
    numeric_impute_value: Optional[float] = None
    numeric_scale: NumericScaleStrategy = NumericScaleStrategy.STANDARD
    categorical_impute: CategoricalImputeStrategy = CategoricalImputeStrategy.MOST_FREQUENT
    categorical_impute_value: Optional[str] = "missing"
    categorical_encode: CategoricalEncodeStrategy = CategoricalEncodeStrategy.ONE_HOT
    extract_date_features: bool = False
    date_features: List[str] = Field(default_factory=lambda: ["year", "month", "day", "day_of_week"])


class PreprocessingStep(BaseModel):
    step_id: str
    operation: str
    input_columns: List[str]
    output_columns: List[str]
    parameters: Dict[str, Any] = Field(default_factory=dict)
    fitted: bool = False
    ordering: int = 0


# Splitting and Cross Validation
class SplitConfig(BaseModel):
    train_size: float = 0.70
    val_size: float = 0.15
    test_size: float = 0.15
    random_seed: int = 42
    stratify: bool = True


class SplitSummary(BaseModel):
    train_rows: int
    val_rows: int
    test_rows: int
    total_rows: int
    stratified: bool = False


class CrossValidationConfig(BaseModel):
    enabled: bool = True
    n_splits: int = 5
    shuffle: bool = True
    random_seed: int = 42
    stratified: bool = True


class HyperparameterDefinition(BaseModel):
    name: str
    display_name: str
    param_type: str  # "int", "float", "string", "bool", "choice"
    default: Any
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    description: str


class MLModelDefinition(BaseModel):
    model_id: str
    display_name: str
    description: str
    task_types: List[MLTaskType]
    default_parameters: Dict[str, Any] = Field(default_factory=dict)
    parameter_schema: List[HyperparameterDefinition] = Field(default_factory=list)
    supports_probability: bool = False
    supports_feature_importance: bool = False
    supports_coefficients: bool = False
    resource_class: str = "light"  # "light", "medium", "heavy"
    recommendation_priority: int = 100


class HyperparameterSearchConfig(BaseModel):
    enabled: bool = False
    search_method: str = "grid"  # "grid" or "random"
    param_grid: Dict[str, List[Any]] = Field(default_factory=dict)
    n_iter: int = 10
    scoring: Optional[str] = None


# Evaluation Metrics
class RegressionMetrics(BaseModel):
    mae: float
    mse: float
    rmse: float
    r2: float
    adjusted_r2: Optional[float] = None
    mape: Optional[float] = None
    median_absolute_error: float


class ClassificationMetrics(BaseModel):
    accuracy: float
    balanced_accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    precision_weighted: float
    recall_weighted: float
    f1_weighted: float
    roc_auc: Optional[float] = None
    pr_auc: Optional[float] = None
    log_loss: Optional[float] = None


class ClusteringMetrics(BaseModel):
    inertia: float
    silhouette_score: Optional[float] = None
    calinski_harabasz_score: Optional[float] = None
    davies_bouldin_score: Optional[float] = None


class ConfusionMatrixData(BaseModel):
    labels: List[str]
    matrix: List[List[int]]
    normalized_matrix: List[List[float]]
    per_class_metrics: Dict[str, Dict[str, float]] = Field(default_factory=dict)


class ResidualDiagnostics(BaseModel):
    actual_vs_predicted: List[Dict[str, float]] = Field(default_factory=list)
    residuals: List[float] = Field(default_factory=list)
    mean_residual: float = 0.0
    std_residual: float = 0.0
    residual_skew: float = 0.0
    largest_errors: List[Dict[str, Any]] = Field(default_factory=list)


class ROCCurvePoint(BaseModel):
    fpr: float
    tpr: float
    threshold: float


class PRCurvePoint(BaseModel):
    precision: float
    recall: float
    threshold: float


class CurveData(BaseModel):
    class_label: str
    auc: Optional[float] = None
    points: List[Dict[str, float]] = Field(default_factory=list)


class ClusterSummaryItem(BaseModel):
    cluster_id: int
    size: int
    percentage: float
    center: Dict[str, float] = Field(default_factory=dict)


class FeatureImportanceItem(BaseModel):
    feature: str
    source_column: str
    importance: float
    coefficient: Optional[float] = None


class MLFinding(BaseModel):
    finding_id: str
    experiment_id: str
    category: str
    severity: str
    title: str
    description: str
    evidence: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    related_columns: List[str] = Field(default_factory=list)
    related_model: Optional[str] = None
    confidence: float = 0.95
    methodology: str = "Deterministic evaluation"
    limitations: List[str] = Field(default_factory=list)


class MLModelRun(BaseModel):
    model_run_id: str
    model_id: str
    model_name: str
    task_type: MLTaskType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: MLJobStatus = MLJobStatus.COMPLETED
    duration_ms: int = 0
    sample_counts: Dict[str, int] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    cv_metrics: Optional[Dict[str, Any]] = None
    test_metrics: Optional[Dict[str, Any]] = None
    baseline_comparison: Optional[Dict[str, Any]] = None
    feature_importance: List[FeatureImportanceItem] = Field(default_factory=list)
    confusion_matrix: Optional[ConfusionMatrixData] = None
    residual_diagnostics: Optional[ResidualDiagnostics] = None
    roc_curves: Optional[List[CurveData]] = None
    pr_curves: Optional[List[CurveData]] = None
    cluster_summaries: Optional[List[ClusterSummaryItem]] = None
    artifact_reference: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class MLExperimentRequest(BaseModel):
    dataset_id: str
    workspace_id: Optional[str] = None
    dataset_version_id: str
    task_type: MLTaskType
    target_column: Optional[str] = None
    feature_columns: List[str]
    preprocessing: PreprocessingConfig = Field(default_factory=PreprocessingConfig)
    split: SplitConfig = Field(default_factory=SplitConfig)
    cross_validation: CrossValidationConfig = Field(default_factory=CrossValidationConfig)
    models: List[str] = Field(default_factory=list)
    model_parameters: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    hyperparameter_search: HyperparameterSearchConfig = Field(default_factory=HyperparameterSearchConfig)
    primary_metric: Optional[str] = None
    random_seed: int = 42
    mode: str = "beginner"  # "beginner" or "advanced"


class MLExperiment(BaseModel):
    experiment_id: str
    dataset_id: str
    dataset_version_id: str
    task_type: MLTaskType
    target_column: Optional[str] = None
    feature_columns: List[str]
    preprocessing: PreprocessingConfig
    split: SplitConfig
    cross_validation: CrossValidationConfig
    models: List[str]
    primary_metric: str
    random_seed: int
    status: MLJobStatus = MLJobStatus.QUEUED
    created_at: str
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    config_hash: str
    error_message: Optional[str] = None


class MLResult(BaseModel):
    result_id: str
    experiment_id: str
    dataset_id: str
    dataset_version_id: str
    task_type: MLTaskType
    status: MLJobStatus
    target: Optional[str] = None
    features: List[str]
    sample_summary: SplitSummary
    preprocessing_steps: List[PreprocessingStep] = Field(default_factory=list)
    model_runs: List[MLModelRun] = Field(default_factory=list)
    best_model_run_id: Optional[str] = None
    primary_metric: str
    findings: List[MLFinding] = Field(default_factory=list)
    visualizations: List[Dict[str, Any]] = Field(default_factory=list)  # Serialized ChartSpecs
    warnings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


class ModelArtifactManifest(BaseModel):
    artifact_id: str
    experiment_id: str
    model_run_id: str
    model_id: str
    task_type: MLTaskType
    dataset_id: str
    dataset_version_id: str
    schema_hash: str
    feature_schema: Dict[str, str]
    target_schema: Optional[Dict[str, str]] = None
    random_seed: int
    created_at: str
    sha256_hash: str
    library_versions: Dict[str, str] = Field(default_factory=dict)


class PredictionRequest(BaseModel):
    rows: Optional[List[Dict[str, Any]]] = None
    dataset_id: Optional[str] = None
    dataset_version_id: Optional[str] = None


class PredictionResult(BaseModel):
    prediction_id: str
    model_run_id: str
    dataset_id: Optional[str] = None
    dataset_version_id: Optional[str] = None
    row_count: int
    task_type: MLTaskType
    predictions: List[Union[float, int, str]]
    probabilities: Optional[List[Dict[str, float]]] = None
    columns: List[str]
    status: str = "COMPLETED"
    created_at: str
    provenance: Dict[str, Any] = Field(default_factory=dict)
