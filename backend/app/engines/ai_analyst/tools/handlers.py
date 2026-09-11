"""
AI Analyst Engine — Tool Handlers (Phase 13)
Executes deterministic analytical capabilities via backend application services.
Ensures tool execution bounds, execution timing, and provenance generation.
"""

import time
from typing import Any, Dict, Optional
import polars as pl

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.ai_analyst.exceptions import AIAnalystException, AIErrorCode
from backend.app.engines.ai_analyst.models import (
    CleaningProposal,
    ToolCall,
    ToolResult,
)
from backend.app.engines.ai_analyst.tools.registry import tool_registry

# Import application services
from backend.app.services.cleaning.version_service import VersionService
from backend.app.services.dataset_service import dataset_service
from backend.app.services.eda_service import EDAService
from backend.app.services.forecasting_service import ForecastingService
from backend.app.services.ml_service import MLService
from backend.app.services.profiling_service import ProfilingService
from backend.app.services.quality_service import QualityService
from backend.app.services.sql.query_service import SQLQueryService
from backend.app.services.statistics_service import StatisticsService
from backend.app.services.visualization_service import VisualizationService

# Singleton service instances
_version_service = VersionService()
_profiling_service = ProfilingService()
_quality_service = QualityService()
_eda_service = EDAService()
_sql_service = SQLQueryService()
_statistics_service = StatisticsService()
_ml_service = MLService()
_forecasting_service = ForecastingService()
_visualization_service = VisualizationService()


def _resolve_ids(tool_call: ToolCall, context: Dict[str, Any]) -> tuple[str, str]:
    dataset_id = tool_call.arguments.get("dataset_id") or context.get("dataset_id")
    version_id = tool_call.arguments.get("dataset_version_id") or context.get("dataset_version_id")
    if not dataset_id:
        raise AIAnalystException(AIErrorCode.AI_DATASET_CONTEXT_INVALID, "Dataset ID is missing.")
    if not version_id:
        active_ver = _version_service.get_active_version(dataset_id)
        if active_ver:
            version_id = active_ver.version_id
        else:
            version_id = "v1"
    return dataset_id, version_id


# Handler 1: get_dataset_context
async def handle_get_dataset_context(tool_call: ToolCall, context: Dict[str, Any]) -> ToolResult:
    start_time = time.perf_counter()
    dataset_id, version_id = _resolve_ids(tool_call, context)
    try:
        ds = dataset_service.get_dataset(dataset_id)
        version = _version_service.get_version(dataset_id, version_id)
        file_path = version.storage_path if version else None

        row_count, col_count, cols, col_types = 0, 0, [], {}
        preview_rows = []
        if file_path:
            df = pl.read_parquet(file_path)
            row_count = df.height
            col_count = df.width
            cols = df.columns
            col_types = {col: str(df[col].dtype) for col in cols}
            preview_rows = df.head(5).to_dicts()

        payload = {
            "dataset_id": dataset_id,
            "dataset_version_id": version_id,
            "name": ds.name if ds else "Unknown",
            "row_count": row_count,
            "column_count": col_count,
            "columns": cols,
            "column_types": col_types,
            "preview_rows": preview_rows,
        }
        elapsed = (time.perf_counter() - start_time) * 1000
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="completed",
            result=payload,
            metadata={"row_count": row_count, "column_count": col_count},
            provenance={"dataset_id": dataset_id, "version_id": version_id},
            execution_time_ms=elapsed,
        )
    except Exception as exc:
        logger.error(f"Error in handle_get_dataset_context: {exc}")
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="failed",
            errors=[str(exc)],
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )


# Handler 2: get_profile
async def handle_get_profile(tool_call: ToolCall, context: Dict[str, Any]) -> ToolResult:
    start_time = time.perf_counter()
    dataset_id, version_id = _resolve_ids(tool_call, context)
    try:
        profile = _profiling_service.profile_dataset(dataset_id)
        # Extract compact column summary for token efficiency
        columns_summary = {}
        for col_prof in profile.columns:
            columns_summary[col_prof.name] = {
                "type": col_prof.physical_type,
                "semantic_type": col_prof.semantic_type,
                "missing_count": col_prof.null_count,
                "missing_pct": round(col_prof.null_percentage, 2),
                "unique_count": col_prof.unique_count,
                "mean": col_prof.numeric_metrics.mean if col_prof.numeric_metrics else None,
                "min": col_prof.numeric_metrics.min if col_prof.numeric_metrics else None,
                "max": col_prof.numeric_metrics.max if col_prof.numeric_metrics else None,
            }

        payload = {
            "dataset_id": dataset_id,
            "row_count": profile.row_count,
            "column_count": profile.column_count,
            "columns": columns_summary,
        }
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="completed",
            result=payload,
            metadata={"row_count": profile.row_count},
            provenance={"dataset_id": dataset_id, "version_id": version_id},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )
    except Exception as exc:
        logger.error(f"Error in handle_get_profile: {exc}")
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="failed",
            errors=[str(exc)],
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )


# Handler 3: get_quality_report
async def handle_get_quality_report(tool_call: ToolCall, context: Dict[str, Any]) -> ToolResult:
    start_time = time.perf_counter()
    dataset_id, version_id = _resolve_ids(tool_call, context)
    try:
        report = _quality_service.assess_dataset_quality(dataset_id)
        dim_scores = {}
        for dim, ds in report.dimension_scores.items():
            dim_key = dim.value if hasattr(dim, "value") else str(dim)
            dim_scores[dim_key] = ds.score if hasattr(ds, "score") else ds

        payload = {
            "overall_score": report.overall_score,
            "overall_grade": report.overall_grade,
            "dimension_scores": dim_scores,
            "total_violations": report.total_issues,
            "critical_violations": report.critical_issues,
            "high_violations": report.high_issues,
            "violations_sample": [
                {
                    "column": getattr(iss, "column", None) or getattr(iss, "column_name", "dataset"),
                    "severity": iss.severity.value if hasattr(iss.severity, "value") else str(iss.severity),
                    "message": getattr(iss, "message", getattr(iss, "rule_name", "Issue")),
                }
                for iss in report.issues[:10]
            ],
        }
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="completed",
            result=payload,
            metadata={"overall_score": report.overall_score},
            provenance={"dataset_id": dataset_id, "version_id": version_id},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )
    except Exception as exc:
        logger.error(f"Error in handle_get_quality_report: {exc}")
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="failed",
            errors=[str(exc)],
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )


# Handler 4: get_eda_report
async def handle_get_eda_report(tool_call: ToolCall, context: Dict[str, Any]) -> ToolResult:
    start_time = time.perf_counter()
    dataset_id, version_id = _resolve_ids(tool_call, context)
    try:
        report = _eda_service.get_eda_report(dataset_id, version_id)
        payload = {
            "dataset_id": dataset_id,
            "version_id": version_id,
            "findings_count": len(report.findings),
            "key_findings": [
                {
                    "category": f.category.value,
                    "severity": f.severity.value,
                    "title": f.title,
                    "description": f.description,
                }
                for f in report.findings[:8]
            ],
        }
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="completed",
            result=payload,
            metadata={"findings_count": len(report.findings)},
            provenance={"dataset_id": dataset_id, "version_id": version_id},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )
    except Exception as exc:
        logger.error(f"Error in handle_get_eda_report: {exc}")
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="failed",
            errors=[str(exc)],
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )


# Handler 5: execute_sql
async def handle_execute_sql(tool_call: ToolCall, context: Dict[str, Any]) -> ToolResult:
    start_time = time.perf_counter()
    dataset_id, version_id = _resolve_ids(tool_call, context)
    sql = tool_call.arguments.get("sql") or tool_call.arguments.get("query")
    if not sql:
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="failed",
            errors=["Missing 'sql' argument."],
            execution_time_ms=0.0,
        )

    try:
        from backend.app.engines.sql.models import SQLQueryRequest
        request = SQLQueryRequest(
            dataset_id=dataset_id,
            version_id=version_id,
            sql=sql,
            limit=settings.AI_MAX_RESULT_ROWS,
        )
        resp = _sql_service.execute_query(request)
        if resp.status.value != "success":
            return ToolResult(
                call_id=tool_call.call_id,
                tool_id=tool_call.tool_id,
                status="failed",
                errors=[resp.error.message if resp.error else "SQL execution failed."],
                metadata={"sql": sql},
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Bound rows
        rows = resp.data[:settings.AI_MAX_RESULT_ROWS] if resp.data else []
        payload = {
            "columns": resp.columns,
            "row_count": resp.row_count,
            "rows": rows,
            "sql": sql,
            "execution_time_ms": resp.execution_time_ms,
        }
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="completed",
            result=payload,
            metadata={"row_count": resp.row_count, "columns": resp.columns},
            provenance={"dataset_id": dataset_id, "version_id": version_id, "sql": sql},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )
    except Exception as exc:
        logger.error(f"Error in handle_execute_sql: {exc}")
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="failed",
            errors=[str(exc)],
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )


# Handler 6: validate_sql
async def handle_validate_sql(tool_call: ToolCall, context: Dict[str, Any]) -> ToolResult:
    start_time = time.perf_counter()
    dataset_id, version_id = _resolve_ids(tool_call, context)
    sql = tool_call.arguments.get("sql") or tool_call.arguments.get("query", "")
    try:
        val = _sql_service.validate_query(dataset_id, sql, version_id)
        payload = {
            "is_valid": val.is_valid,
            "error": val.error,
            "error_type": val.error_type,
            "ast": val.ast_summary,
        }
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="completed",
            result=payload,
            metadata={"is_valid": val.is_valid},
            provenance={"dataset_id": dataset_id, "version_id": version_id},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )
    except Exception as exc:
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="failed",
            errors=[str(exc)],
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )


# Handler 7: get_statistics
async def handle_get_statistics(tool_call: ToolCall, context: Dict[str, Any]) -> ToolResult:
    start_time = time.perf_counter()
    try:
        catalog = _statistics_service.get_methods_catalog()
        methods = [
            {
                "method_id": m.method if isinstance(m.method, str) else getattr(m.method, "value", str(m.method)),
                "display_name": getattr(m, "name", str(m.method)),
                "category": m.category if isinstance(m.category, str) else getattr(m.category, "value", str(m.category)),
            }
            for m in catalog
        ]
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="completed",
            result={"methods": methods},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )
    except Exception as exc:
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="failed",
            errors=[str(exc)],
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )


# Handler 8: run_statistical_analysis
async def handle_run_statistical_analysis(tool_call: ToolCall, context: Dict[str, Any]) -> ToolResult:
    start_time = time.perf_counter()
    dataset_id, version_id = _resolve_ids(tool_call, context)
    args = tool_call.arguments
    method = args.get("method") or args.get("method_id", "independent_t_test")
    variables = args.get("variables") or args.get("columns", [])
    group_col = args.get("group_column")

    try:
        from backend.app.engines.statistics.models import StatisticalAnalysisRequest, StatisticalMethod
        req = StatisticalAnalysisRequest(
            dataset_id=dataset_id,
            version_id=version_id,
            method=StatisticalMethod(method),
            variables=variables,
            group_column=group_col,
            parameters=args.get("parameters", {}),
        )
        res = _statistics_service.execute_analysis(req)
        payload = {
            "analysis_id": res.analysis_id,
            "method": res.method.value,
            "statistic_name": res.statistic_name,
            "statistic_value": res.statistic_value,
            "p_value": res.p_value,
            "is_significant": res.is_significant,
            "effect_size": res.effect_size,
            "effect_size_type": res.effect_size_type,
            "confidence_interval": res.confidence_interval,
            "interpretation": res.interpretation,
            "assumptions": res.assumptions,
            "limitations": res.limitations,
        }
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="completed",
            result=payload,
            metadata={"p_value": res.p_value, "statistic": res.statistic_value},
            provenance={"dataset_id": dataset_id, "version_id": version_id, "analysis_id": res.analysis_id},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )
    except Exception as exc:
        logger.error(f"Error in handle_run_statistical_analysis: {exc}")
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="failed",
            errors=[str(exc)],
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )


# Handler 9: run_ml_experiment
async def handle_run_ml_experiment(tool_call: ToolCall, context: Dict[str, Any]) -> ToolResult:
    start_time = time.perf_counter()
    dataset_id, version_id = _resolve_ids(tool_call, context)
    args = tool_call.arguments
    target_column = args.get("target_column")
    task_type = args.get("task_type", "regression")

    if not target_column:
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="failed",
            errors=["Missing 'target_column' argument for ML experiment."],
            execution_time_ms=0.0,
        )

    try:
        from backend.app.engines.ml.models import MLExperimentRequest, MLTaskType
        req = MLExperimentRequest(
            dataset_id=dataset_id,
            version_id=version_id,
            target_column=target_column,
            task_type=MLTaskType(task_type),
            feature_columns=args.get("feature_columns"),
            model_ids=args.get("model_ids"),
        )
        res = _ml_service.create_and_run_experiment(req)
        payload = {
            "experiment_id": res.experiment_id,
            "best_model_id": res.best_model_id,
            "best_metric_value": res.best_metric_value,
            "task_type": res.task_type.value,
            "models_trained": len(res.model_runs),
            "leaderboard": [
                {
                    "model_id": m.model_id,
                    "model_name": m.model_name,
                    "metrics": m.metrics,
                }
                for m in res.model_runs
            ],
            "feature_importance": res.feature_importance,
        }
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="completed",
            result=payload,
            metadata={"best_model_id": res.best_model_id, "best_metric": res.best_metric_value},
            provenance={"dataset_id": dataset_id, "version_id": version_id, "experiment_id": res.experiment_id},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )
    except Exception as exc:
        logger.error(f"Error in handle_run_ml_experiment: {exc}")
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="failed",
            errors=[str(exc)],
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )


# Handler 10: get_ml_result
async def handle_get_ml_result(tool_call: ToolCall, context: Dict[str, Any]) -> ToolResult:
    start_time = time.perf_counter()
    exp_id = tool_call.arguments.get("experiment_id")
    if not exp_id:
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="failed",
            errors=["Missing 'experiment_id'."],
            execution_time_ms=0.0,
        )
    try:
        res = _ml_service.get_experiment_result(exp_id)
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="completed",
            result={"best_model": res.best_model_id, "metric": res.best_metric_value},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )
    except Exception as exc:
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="failed",
            errors=[str(exc)],
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )


# Handler 11: run_forecast
async def handle_run_forecast(tool_call: ToolCall, context: Dict[str, Any]) -> ToolResult:
    start_time = time.perf_counter()
    dataset_id, version_id = _resolve_ids(tool_call, context)
    args = tool_call.arguments
    target_column = args.get("target_column")
    time_column = args.get("time_column")
    horizon = int(args.get("horizon", 6))

    if not target_column or not time_column:
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="failed",
            errors=["Missing 'target_column' or 'time_column' for forecasting."],
            execution_time_ms=0.0,
        )

    try:
        from backend.app.engines.forecasting.models import ForecastExperimentRequest
        req = ForecastExperimentRequest(
            dataset_id=dataset_id,
            version_id=version_id,
            time_column=time_column,
            target_column=target_column,
            horizon=horizon,
            model_ids=args.get("model_ids"),
        )
        exp = _forecasting_service.submit_experiment(req)
        # Wait or poll briefly for completion
        for _ in range(30):
            res = _forecasting_service.get_experiment_results(exp.experiment_id)
            if res and res.status == "completed":
                payload = {
                    "experiment_id": res.experiment_id,
                    "best_model_id": res.best_model_id,
                    "best_metric_value": res.best_metric_value,
                    "horizon": res.horizon,
                    "leaderboard": [
                        {"model_id": m.model_id, "model_name": m.model_name, "metrics": m.metrics}
                        for m in res.model_runs
                    ],
                    "forecast_points": res.forecast_points[:horizon],
                }
                return ToolResult(
                    call_id=tool_call.call_id,
                    tool_id=tool_call.tool_id,
                    status="completed",
                    result=payload,
                    metadata={"best_model_id": res.best_model_id, "horizon": horizon},
                    provenance={"dataset_id": dataset_id, "version_id": version_id, "experiment_id": res.experiment_id},
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                )
            time.sleep(0.5)

        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="completed",
            result={"experiment_id": exp.experiment_id, "status": "running"},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )
    except Exception as exc:
        logger.error(f"Error in handle_run_forecast: {exc}")
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="failed",
            errors=[str(exc)],
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )


# Handler 12: get_forecast_result
async def handle_get_forecast_result(tool_call: ToolCall, context: Dict[str, Any]) -> ToolResult:
    start_time = time.perf_counter()
    exp_id = tool_call.arguments.get("experiment_id")
    if not exp_id:
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="failed",
            errors=["Missing 'experiment_id'."],
            execution_time_ms=0.0,
        )
    try:
        res = _forecasting_service.get_experiment_results(exp_id)
        if not res:
            return ToolResult(
                call_id=tool_call.call_id,
                tool_id=tool_call.tool_id,
                status="failed",
                errors=["Forecast result not found."],
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="completed",
            result={"best_model": res.best_model_id, "metrics": res.best_metric_value},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )
    except Exception as exc:
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="failed",
            errors=[str(exc)],
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )


# Handler 13: recommend_visualization
async def handle_recommend_visualization(tool_call: ToolCall, context: Dict[str, Any]) -> ToolResult:
    start_time = time.perf_counter()
    dataset_id, version_id = _resolve_ids(tool_call, context)
    columns = tool_call.arguments.get("columns", [])
    try:
        recs = _visualization_service.recommend_visualizations(dataset_id, version_id, columns)
        payload = {
            "recommendations": [
                {
                    "chart_type": r.chart_type.value if hasattr(r.chart_type, "value") else str(r.chart_type),
                    "title": r.title,
                    "score": r.score,
                    "reasoning": r.reasoning,
                }
                for r in recs[:5]
            ]
        }
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="completed",
            result=payload,
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )
    except Exception as exc:
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="failed",
            errors=[str(exc)],
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )


# Handler 14: create_visualization
async def handle_create_visualization(tool_call: ToolCall, context: Dict[str, Any]) -> ToolResult:
    start_time = time.perf_counter()
    dataset_id, version_id = _resolve_ids(tool_call, context)
    args = tool_call.arguments

    try:
        from backend.app.engines.visualization.models import ChartSpec, ChartType, EncodingMapping
        chart_type = args.get("chart_type", "bar")
        x_field = args.get("x")
        y_field = args.get("y")
        title = args.get("title", f"{chart_type.title()} Chart")

        spec = ChartSpec(
            dataset_id=dataset_id,
            version_id=version_id,
            chart_type=ChartType(chart_type),
            title=title,
            encoding=EncodingMapping(x=x_field, y=y_field),
        )
        preview = _visualization_service.preview_chart(spec)
        payload = {
            "chart_spec": spec.model_dump(mode="json"),
            "data_point_count": len(preview.data) if preview.data else 0,
            "preview_data": preview.data[:settings.AI_MAX_RESULT_ROWS] if preview.data else [],
        }
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="completed",
            result=payload,
            metadata={"chart_type": chart_type, "points": len(preview.data) if preview.data else 0},
            provenance={"dataset_id": dataset_id, "version_id": version_id},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )
    except Exception as exc:
        logger.error(f"Error in handle_create_visualization: {exc}")
        return ToolResult(
            call_id=tool_call.call_id,
            tool_id=tool_call.tool_id,
            status="failed",
            errors=[str(exc)],
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )


# Handler 15: get_visualization_data
async def handle_get_visualization_data(tool_call: ToolCall, context: Dict[str, Any]) -> ToolResult:
    return await handle_create_visualization(tool_call, context)


# Handler 16: propose_cleaning (PROPOSAL_ONLY)
async def handle_propose_cleaning(tool_call: ToolCall, context: Dict[str, Any]) -> ToolResult:
    start_time = time.perf_counter()
    dataset_id, version_id = _resolve_ids(tool_call, context)
    args = tool_call.arguments
    op_type = args.get("operation_type", "drop_duplicates")
    params = args.get("parameters", {})
    rationale = args.get("rationale", "User requested data cleaning operation.")
    impact = args.get("impact_summary", "Will create a new dataset version after user confirmation.")

    proposal = CleaningProposal(
        dataset_id=dataset_id,
        dataset_version_id=version_id,
        operation_type=op_type,
        parameters=params,
        rationale=rationale,
        impact_summary=impact,
        requires_confirmation=True,
        status="proposed",
    )
    return ToolResult(
        call_id=tool_call.call_id,
        tool_id=tool_call.tool_id,
        status="completed",
        result={"cleaning_proposal": proposal.model_dump(mode="json")},
        metadata={"requires_confirmation": True, "operation_type": op_type},
        provenance={"dataset_id": dataset_id, "version_id": version_id},
        execution_time_ms=(time.perf_counter() - start_time) * 1000,
    )


# Register handlers in ToolRegistry
def register_all_handlers() -> None:
    tool_registry.register_handler("get_dataset_context", handle_get_dataset_context)
    tool_registry.register_handler("get_profile", handle_get_profile)
    tool_registry.register_handler("get_quality_report", handle_get_quality_report)
    tool_registry.register_handler("get_eda_report", handle_get_eda_report)
    tool_registry.register_handler("execute_sql", handle_execute_sql)
    tool_registry.register_handler("validate_sql", handle_validate_sql)
    tool_registry.register_handler("get_statistics", handle_get_statistics)
    tool_registry.register_handler("run_statistical_analysis", handle_run_statistical_analysis)
    tool_registry.register_handler("run_ml_experiment", handle_run_ml_experiment)
    tool_registry.register_handler("get_ml_result", handle_get_ml_result)
    tool_registry.register_handler("run_forecast", handle_run_forecast)
    tool_registry.register_handler("get_forecast_result", handle_get_forecast_result)
    tool_registry.register_handler("recommend_visualization", handle_recommend_visualization)
    tool_registry.register_handler("create_visualization", handle_create_visualization)
    tool_registry.register_handler("get_visualization_data", handle_get_visualization_data)
    tool_registry.register_handler("propose_cleaning", handle_propose_cleaning)


register_all_handlers()
