"""
AnalyzaX — Phase 12: Forecasting Domain Models and Contracts.
Strongly-typed Pydantic v2 schemas representing time-series semantics, validation,
backtesting, metrics, prediction intervals, diagnostics, and ChartSpec visualizations.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ForecastFrequency(str, Enum):
    MINUTELY = "MINUTELY"
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    BUSINESS_DAY = "BUSINESS_DAY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"
    CUSTOM = "CUSTOM"


class RegularityStatus(str, Enum):
    REGULAR = "REGULAR"
    MOSTLY_REGULAR = "MOSTLY_REGULAR"
    IRREGULAR = "IRREGULAR"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class QualitySeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ForecastQualityIssue(BaseModel):
    issue_id: str
    issue_type: str
    severity: QualitySeverity
    description: str
    affected_rows: int = 0
    time_range: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None
    recommendation: Optional[str] = None


class TemporalValidationReport(BaseModel):
    is_valid: bool
    time_column: str
    target_column: str
    inferred_frequency: ForecastFrequency
    pandas_frequency_str: str = "D"
    regularity: RegularityStatus
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    observation_count: int
    expected_observation_count: int
    missing_timestamp_count: int = 0
    duplicate_timestamp_count: int = 0
    min_timestamp: str
    max_timestamp: str
    target_missing_count: int = 0
    target_zero_count: int = 0
    target_mean: float
    target_variance: float
    issues: List[ForecastQualityIssue] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class TrendDirection(str, Enum):
    UPWARD = "UPWARD"
    DOWNWARD = "DOWNWARD"
    FLAT = "FLAT"


class TrendFinding(BaseModel):
    detected: bool
    direction: TrendDirection
    slope: float
    p_value: float
    r_squared: float
    description: str


class SeasonalityFinding(BaseModel):
    detected: bool
    candidate_period: Optional[int] = None
    frequency_label: Optional[str] = None
    seasonal_strength: float = 0.0
    confidence: float = 0.0
    evidence: Optional[Dict[str, Any]] = None
    description: str


class ACFResult(BaseModel):
    lags: List[int]
    acf_values: List[float]
    pacf_values: List[float]
    confidence_bound: float  # typically 1.96 / sqrt(N)


class DecompositionResult(BaseModel):
    method: str = "classical"  # classical or stl
    period: int
    timestamps: List[str]
    observed: List[float]
    trend: List[Optional[float]]
    seasonal: List[Optional[float]]
    residual: List[Optional[float]]


class TemporalAnalysisSummary(BaseModel):
    trend: TrendFinding
    seasonality: SeasonalityFinding
    acf: Optional[ACFResult] = None
    decomposition: Optional[DecompositionResult] = None
    anomalies_detected: int = 0


class ForecastPoint(BaseModel):
    timestamp: str
    value: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    horizon_step: int


class ForecastMetrics(BaseModel):
    mae: float
    mse: float
    rmse: float
    mase: Optional[float] = None
    smape: float
    wape: float
    mape: Optional[float] = None  # None if zero-actuals prevent valid percentage


class BacktestFoldResult(BaseModel):
    fold_index: int
    train_end: str
    test_start: str
    test_end: str
    actuals: List[float]
    predictions: List[float]
    metrics: ForecastMetrics


class BacktestResult(BaseModel):
    folds: List[BacktestFoldResult]
    mean_metrics: ForecastMetrics
    std_metrics: Optional[Dict[str, float]] = None


class ResidualDiagnostics(BaseModel):
    mean: float
    std: float
    ljung_box_stat: Optional[float] = None
    ljung_box_pvalue: Optional[float] = None
    normality_stat: Optional[float] = None
    normality_pvalue: Optional[float] = None
    autocorrelation_detected: bool = False
    residuals: List[float] = Field(default_factory=list)
    residual_timestamps: List[str] = Field(default_factory=list)


class ForecastModelDefinition(BaseModel):
    model_id: str
    display_name: str
    description: str
    supports_seasonality: bool
    supports_trend: bool
    supports_prediction_intervals: bool
    default_parameters: Dict[str, Any] = Field(default_factory=dict)
    parameter_schema: Dict[str, Any] = Field(default_factory=dict)
    recommendation_priority: int = 1


class ForecastJobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


class ForecastModelRun(BaseModel):
    run_id: str
    model_id: str
    model_name: str
    parameters: Dict[str, Any]
    training_status: str
    training_duration_ms: float
    sample_count: int
    backtest_result: BacktestResult
    future_forecasts: List[ForecastPoint] = Field(default_factory=list)
    residual_diagnostics: Optional[ResidualDiagnostics] = None
    artifact_reference: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class FindingCategory(str, Enum):
    DATA_QUALITY = "DATA_QUALITY"
    TREND = "TREND"
    SEASONALITY = "SEASONALITY"
    AUTOCORRELATION = "AUTOCORRELATION"
    MODEL_PERFORMANCE = "MODEL_PERFORMANCE"
    MODEL_DIAGNOSTICS = "MODEL_DIAGNOSTICS"
    FORECAST_UNCERTAINTY = "FORECAST_UNCERTAINTY"
    ANOMALY = "ANOMALY"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    RESOURCE = "RESOURCE"
    MODEL_WARNING = "MODEL_WARNING"


class ForecastFinding(BaseModel):
    finding_id: str
    category: FindingCategory
    severity: QualitySeverity
    title: str
    description: str
    evidence: Optional[Dict[str, Any]] = None
    related_columns: List[str] = Field(default_factory=list)
    methodology: Optional[str] = None
    limitations: Optional[str] = None


class ForecastExperimentRequest(BaseModel):
    dataset_id: str
    workspace_id: Optional[str] = None
    dataset_version_id: str
    time_column: str
    target_column: str
    group_columns: Optional[List[str]] = None
    frequency: Optional[ForecastFrequency] = None
    forecast_horizon: int = Field(default=14, ge=1, le=365)
    training_window_type: str = Field(default="expanding", description="expanding or rolling")
    training_window_size: Optional[int] = None
    validation_folds: int = Field(default=3, ge=1, le=10)
    models: List[str] = Field(
        default_factory=lambda: ["naive", "drift", "simple_exp_smoothing", "holt", "holt_winters", "arima"]
    )
    primary_metric: str = Field(default="rmse")
    confidence_level: float = Field(default=0.95, ge=0.5, le=0.999)
    model_parameters: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    options: Dict[str, Any] = Field(default_factory=dict)


class ForecastExperiment(BaseModel):
    experiment_id: str
    dataset_id: str
    dataset_version_id: str
    time_column: str
    target_column: str
    frequency: ForecastFrequency
    forecast_horizon: int
    validation_folds: int
    models: List[str]
    primary_metric: str
    confidence_level: float
    status: ForecastJobStatus
    progress_stage: Optional[str] = None
    progress_percent: int = 0
    created_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


class ForecastResult(BaseModel):
    result_id: str
    experiment_id: str
    dataset_id: str
    dataset_version_id: str
    time_column: str
    target_column: str
    frequency: ForecastFrequency
    pandas_frequency_str: str
    forecast_horizon: int
    primary_metric: str
    confidence_level: float
    historical_timestamps: List[str]
    historical_values: List[float]
    models: List[ForecastModelRun]
    best_model_id: str
    validation_report: TemporalValidationReport
    temporal_analysis: TemporalAnalysisSummary
    findings: List[ForecastFinding]
    visualizations: List[Dict[str, Any]] = Field(default_factory=list)  # Phase 9 ChartSpecs
    warnings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any]
    created_at: str


class FuturePredictRequest(BaseModel):
    run_id: Optional[str] = None
    periods: int = Field(default=14, ge=1, le=365)
    confidence_level: Optional[float] = None


class FuturePredictResult(BaseModel):
    prediction_id: str
    run_id: str
    model_id: str
    model_name: str
    forecast_points: List[ForecastPoint]
    confidence_level: float
    created_at: str
