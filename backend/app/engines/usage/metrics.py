"""
Centralized Usage Metric Registry for Phase 20.
Defines canonical system metrics, aggregation semantics, and reliable measurement sources.
Every metered metric has an auditable measurement source (zero fake accounting).
"""

from typing import Dict, List, Optional
from pydantic import BaseModel
from backend.app.engines.usage.models import MetricUnit, QuotaPeriod


class MetricDefinition(BaseModel):
    """Specification of an auditable usage metric."""
    metric_key: str
    display_name: str
    description: str
    category: str
    unit: MetricUnit
    default_period: QuotaPeriod
    is_point_in_time: bool = False  # If True, represents current state (e.g. current storage bytes) rather than monthly sum
    measurement_source: str


class MetricKey(str):
    @property
    def key(self) -> str:
        return str(self)


class UsageMetrics:
    # ─────────────────────────────────────────────────────────
    # Canonical Metric Keys
    # ─────────────────────────────────────────────────────────

    # Storage & Datasets
    DATASET_UPLOADS = MetricKey("dataset_uploads")
    DATASET_STORAGE_BYTES = MetricKey("dataset_storage_bytes")
    DATASET_ROWS_PROCESSED = MetricKey("dataset_rows_processed")

    # Workspaces & Projects
    PROJECT_COUNT = MetricKey("project_count")
    WORKSPACE_MEMBER_COUNT = MetricKey("workspace_member_count")

    # AI Analyst
    AI_ANALYST_MESSAGES = MetricKey("ai_analyst_messages")
    AI_MODEL_TOKENS_INPUT = MetricKey("ai_model_tokens_input")
    AI_MODEL_TOKENS_OUTPUT = MetricKey("ai_model_tokens_output")

    # SQL Analytics
    SQL_QUERY_EXECUTIONS = MetricKey("sql_query_executions")

    # Machine Learning & Forecasting
    ML_EXPERIMENTS = MetricKey("ml_experiments")
    FORECAST_RUNS = MetricKey("forecast_runs")

    # Statistical Analyses
    STATISTICAL_ANALYSES = MetricKey("statistical_analyses")

    # Exports & Reports
    EXPORTS_GENERATED = MetricKey("exports_generated")
    EXPORT_BYTES = MetricKey("export_bytes")


# Registry of all official metrics
METRIC_REGISTRY: Dict[str, MetricDefinition] = {
    UsageMetrics.DATASET_UPLOADS: MetricDefinition(
        metric_key=UsageMetrics.DATASET_UPLOADS,
        display_name="Dataset Uploads",
        description="Number of dataset files ingested into the workspace during the billing period.",
        category="Storage",
        unit=MetricUnit.COUNT,
        default_period=QuotaPeriod.MONTHLY,
        is_point_in_time=False,
        measurement_source="IngestionService.ingest_file successful completions",
    ),
    UsageMetrics.DATASET_STORAGE_BYTES: MetricDefinition(
        metric_key=UsageMetrics.DATASET_STORAGE_BYTES,
        display_name="Dataset Storage",
        description="Current physical disk space occupied by raw files, Parquet tables, and versioned assets.",
        category="Storage",
        unit=MetricUnit.BYTES,
        default_period=QuotaPeriod.CURRENT,
        is_point_in_time=True,
        measurement_source="Physical disk byte sum of data/uploads/ and dataset parquet files",
    ),
    UsageMetrics.DATASET_ROWS_PROCESSED: MetricDefinition(
        metric_key=UsageMetrics.DATASET_ROWS_PROCESSED,
        display_name="Dataset Rows Processed",
        description="Total row count ingested across all datasets in the billing period.",
        category="Storage",
        unit=MetricUnit.ROWS,
        default_period=QuotaPeriod.MONTHLY,
        is_point_in_time=False,
        measurement_source="DuckDB row count probe upon dataset ingestion",
    ),
    UsageMetrics.PROJECT_COUNT: MetricDefinition(
        metric_key=UsageMetrics.PROJECT_COUNT,
        display_name="Active Projects",
        description="Number of active, non-archived projects in the workspace.",
        category="Workspace",
        unit=MetricUnit.COUNT,
        default_period=QuotaPeriod.CURRENT,
        is_point_in_time=True,
        measurement_source="WorkspaceRepository active project count",
    ),
    UsageMetrics.WORKSPACE_MEMBER_COUNT: MetricDefinition(
        metric_key=UsageMetrics.WORKSPACE_MEMBER_COUNT,
        display_name="Team Members",
        description="Number of active members collaborating in the workspace.",
        category="Workspace",
        unit=MetricUnit.COUNT,
        default_period=QuotaPeriod.CURRENT,
        is_point_in_time=True,
        measurement_source="AuthRepository active workspace members count",
    ),
    UsageMetrics.AI_ANALYST_MESSAGES: MetricDefinition(
        metric_key=UsageMetrics.AI_ANALYST_MESSAGES,
        display_name="AI Analyst Messages",
        description="Natural language queries and assistant responses executed by the AI Analyst.",
        category="AI",
        unit=MetricUnit.COUNT,
        default_period=QuotaPeriod.MONTHLY,
        is_point_in_time=False,
        measurement_source="ai_analyst_service.chat chat execution turns",
    ),
    UsageMetrics.AI_MODEL_TOKENS_INPUT: MetricDefinition(
        metric_key=UsageMetrics.AI_MODEL_TOKENS_INPUT,
        display_name="AI Input Tokens",
        description="Prompt tokens sent to AI language models.",
        category="AI",
        unit=MetricUnit.TOKENS,
        default_period=QuotaPeriod.MONTHLY,
        is_point_in_time=False,
        measurement_source="LLM provider usage metadata (when returned by provider)",
    ),
    UsageMetrics.AI_MODEL_TOKENS_OUTPUT: MetricDefinition(
        metric_key=UsageMetrics.AI_MODEL_TOKENS_OUTPUT,
        display_name="AI Output Tokens",
        description="Completion tokens generated by AI language models.",
        category="AI",
        unit=MetricUnit.TOKENS,
        default_period=QuotaPeriod.MONTHLY,
        is_point_in_time=False,
        measurement_source="LLM provider usage metadata (when returned by provider)",
    ),
    UsageMetrics.SQL_QUERY_EXECUTIONS: MetricDefinition(
        metric_key=UsageMetrics.SQL_QUERY_EXECUTIONS,
        display_name="SQL Query Executions",
        description="Vectorized DuckDB SQL analytical queries executed.",
        category="Analytics",
        unit=MetricUnit.COUNT,
        default_period=QuotaPeriod.MONTHLY,
        is_point_in_time=False,
        measurement_source="SqlQueryService.execute_query runs",
    ),
    UsageMetrics.ML_EXPERIMENTS: MetricDefinition(
        metric_key=UsageMetrics.ML_EXPERIMENTS,
        display_name="ML Experiments",
        description="Automated model training, hyperparameter evaluations, and benchmark runs.",
        category="Analytics",
        unit=MetricUnit.COUNT,
        default_period=QuotaPeriod.MONTHLY,
        is_point_in_time=False,
        measurement_source="ml_service.train_model completed experiments",
    ),
    UsageMetrics.FORECAST_RUNS: MetricDefinition(
        metric_key=UsageMetrics.FORECAST_RUNS,
        display_name="Forecast Runs",
        description="Time-series forecasting models executed.",
        category="Analytics",
        unit=MetricUnit.COUNT,
        default_period=QuotaPeriod.MONTHLY,
        is_point_in_time=False,
        measurement_source="forecasting_service.train_and_forecast runs",
    ),
    UsageMetrics.STATISTICAL_ANALYSES: MetricDefinition(
        metric_key=UsageMetrics.STATISTICAL_ANALYSES,
        display_name="Statistical Analyses",
        description="Hypothesis tests, parametric correlations, and distribution evaluations executed.",
        category="Analytics",
        unit=MetricUnit.COUNT,
        default_period=QuotaPeriod.MONTHLY,
        is_point_in_time=False,
        measurement_source="statistics_service test executions",
    ),
    UsageMetrics.EXPORTS_GENERATED: MetricDefinition(
        metric_key=UsageMetrics.EXPORTS_GENERATED,
        display_name="Exports Generated",
        description="Dataset Parquet/CSV exports and compiled executive report artifacts.",
        category="Exports",
        unit=MetricUnit.COUNT,
        default_period=QuotaPeriod.MONTHLY,
        is_point_in_time=False,
        measurement_source="export_service.export_dataset and report exports",
    ),
    UsageMetrics.EXPORT_BYTES: MetricDefinition(
        metric_key=UsageMetrics.EXPORT_BYTES,
        display_name="Exported Bytes",
        description="Total physical bytes in exported files downloaded by users.",
        category="Exports",
        unit=MetricUnit.BYTES,
        default_period=QuotaPeriod.MONTHLY,
        is_point_in_time=False,
        measurement_source="Export job artifact file size bytes",
    ),
}


def get_metric_definition(metric_key: str) -> Optional[MetricDefinition]:
    """Retrieves definition for a given metric key."""
    return METRIC_REGISTRY.get(metric_key)


def list_metric_definitions() -> List[MetricDefinition]:
    """Returns all registered metrics."""
    return list(METRIC_REGISTRY.values())
