"""
AI Analyst Engine — Intent Classification and Analytical Planner (Phase 13)
Produces structured, inspectable execution plans before tool orchestration.
"""

import re
from typing import Any, Dict, List, Optional
from uuid import uuid4

from backend.app.engines.ai_analyst.models import (
    AnalystIntent,
    AnalysisPlan,
    AnalysisStep,
    DatasetContextSummary,
)
from backend.app.engines.ai_analyst.providers.base import LLMProvider


class IntentClassifier:
    """Classifies natural-language inquiries into AnalyzaX intent taxonomy."""

    @classmethod
    def classify(cls, query: str) -> AnalystIntent:
        q = query.lower()
        if "ignore all" in q or "reveal" in q or "api key" in q or "password" in q:
            return AnalystIntent.UNSUPPORTED_REQUEST
        if "stock price" in q or "crypto" in q or "should i buy" in q or "trading" in q or "stock" in q:
            return AnalystIntent.UNSUPPORTED_REQUEST
        if "remove duplicate" in q or "drop missing" in q or "clean data" in q or "fill missing" in q:
            return AnalystIntent.DATA_CLEANING_REQUEST
        if "forecast" in q or "predict next" in q or "future" in q or "time series" in q:
            return AnalystIntent.FORECASTING
        if "train" in q or "model" in q or "machine learning" in q or "classify" in q or "regression" in q:
            return AnalystIntent.MACHINE_LEARNING
        if "significant" in q or "difference" in q or "correlation" in q or "hypothesis" in q or "t-test" in q or "p-value" in q:
            return AnalystIntent.STATISTICAL_TEST
        if "clean" in q or "quality" in q or "anomal" in q or "missing" in q or "violation" in q:
            return AnalystIntent.DATA_QUALITY
        if "chart" in q or "plot" in q or "visualiz" in q or "graph" in q or "distribution" in q:
            return AnalystIntent.VISUALIZATION
        if "column" in q or "schema" in q or "overview" in q or "summary" in q or "dataset" in q and len(q.split()) <= 4:
            return AnalystIntent.DATASET_OVERVIEW
        if "average" in q or "sum" in q or "total" in q or "top" in q or "revenue" in q or "sales" in q or "by" in q:
            return AnalystIntent.SQL_ANALYSIS
        return AnalystIntent.DESCRIPTIVE_ANALYSIS


class AnalysisPlanner:
    """Plans multi-step deterministic tool execution based on intent and metadata."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def plan(
        self,
        question: str,
        intent: AnalystIntent,
        context: Optional[DatasetContextSummary] = None,
    ) -> AnalysisPlan:
        steps: List[AnalysisStep] = []
        assumptions: List[str] = ["Using active dataset version in isolated memory engine."]
        expected_outputs: List[str] = ["Structured analytical metrics"]

        dataset_id = context.dataset_id if context else "unknown"
        version_id = context.dataset_version_id if context else "v1"
        cols = context.column_names if context else []
        num_cols = context.numeric_columns if context else []
        cat_cols = context.categorical_columns if context else []
        dt_cols = context.datetime_columns if context else []

        if intent == AnalystIntent.DATASET_OVERVIEW:
            steps.append(
                AnalysisStep(
                    description="Inspect dataset profile and column distributions",
                    tool_id="get_profile",
                    parameters={"dataset_id": dataset_id, "dataset_version_id": version_id},
                )
            )
            expected_outputs.append("Full column schema and distribution profile")

        elif intent == AnalystIntent.DATA_QUALITY:
            steps.append(
                AnalysisStep(
                    description="Assess dataset quality score and rule violations",
                    tool_id="get_quality_report",
                    parameters={"dataset_id": dataset_id, "dataset_version_id": version_id},
                )
            )
            expected_outputs.append("Quality score and violation details")

        elif intent == AnalystIntent.SQL_ANALYSIS:
            # Generate deterministic SQL based on columns
            target_num = num_cols[0] if num_cols else (cols[0] if cols else "*")
            group_col = cat_cols[0] if cat_cols else None
            
            if group_col and target_num != "*":
                sql = f'SELECT "{group_col}", AVG("{target_num}") AS "avg_{target_num}", COUNT(*) AS "record_count" FROM dataset GROUP BY "{group_col}" ORDER BY "avg_{target_num}" DESC LIMIT 20'
            elif target_num != "*":
                sql = f'SELECT AVG("{target_num}") AS "average_{target_num}", MIN("{target_num}") AS "min_{target_num}", MAX("{target_num}") AS "max_{target_num}", COUNT(*) AS "total_count" FROM dataset'
            else:
                sql = "SELECT * FROM dataset LIMIT 20"

            steps.append(
                AnalysisStep(
                    description="Execute read-only SQL aggregation query",
                    tool_id="execute_sql",
                    parameters={"sql": sql, "dataset_id": dataset_id, "dataset_version_id": version_id},
                )
            )
            expected_outputs.append("Aggregated SQL query result")

        elif intent == AnalystIntent.STATISTICAL_TEST:
            method = "independent_t_test"
            var = num_cols[0] if num_cols else "value"
            grp = cat_cols[0] if cat_cols else "group"
            steps.append(
                AnalysisStep(
                    description="Execute hypothesis test for group differences",
                    tool_id="run_statistical_analysis",
                    parameters={
                        "dataset_id": dataset_id,
                        "dataset_version_id": version_id,
                        "method": method,
                        "variables": [var],
                        "group_column": grp,
                    },
                )
            )
            expected_outputs.append("Test statistic, p-value, and effect size")

        elif intent == AnalystIntent.MACHINE_LEARNING:
            target = num_cols[0] if num_cols else (cols[0] if cols else "target")
            steps.append(
                AnalysisStep(
                    description="Train benchmark ML models and compare performance",
                    tool_id="run_ml_experiment",
                    parameters={
                        "dataset_id": dataset_id,
                        "dataset_version_id": version_id,
                        "target_column": target,
                        "task_type": "regression",
                    },
                )
            )
            expected_outputs.append("ML leaderboard and evaluation metrics")

        elif intent == AnalystIntent.FORECASTING:
            target = num_cols[0] if num_cols else "value"
            time_col = dt_cols[0] if dt_cols else (cols[0] if cols else "date")
            steps.append(
                AnalysisStep(
                    description="Train time-series forecasting models and generate predictions",
                    tool_id="run_forecast",
                    parameters={
                        "dataset_id": dataset_id,
                        "dataset_version_id": version_id,
                        "target_column": target,
                        "time_column": time_col,
                        "horizon": 6,
                    },
                )
            )
            expected_outputs.append("Projected horizon points with prediction intervals")

        elif intent == AnalystIntent.VISUALIZATION:
            chart_type = "line" if dt_cols else ("bar" if cat_cols else "scatter")
            x = dt_cols[0] if dt_cols else (cat_cols[0] if cat_cols else cols[0] if cols else "x")
            y = num_cols[0] if num_cols else (cols[1] if len(cols) > 1 else "y")

            step1 = AnalysisStep(
                description="Aggregate data for visual plotting",
                tool_id="execute_sql",
                parameters={
                    "sql": f'SELECT "{x}", AVG("{y}") AS "{y}" FROM dataset GROUP BY "{x}" LIMIT 30',
                    "dataset_id": dataset_id,
                    "dataset_version_id": version_id,
                },
            )
            step2 = AnalysisStep(
                description="Generate validated ChartSpec",
                tool_id="create_visualization",
                parameters={
                    "dataset_id": dataset_id,
                    "dataset_version_id": version_id,
                    "chart_type": chart_type,
                    "x": x,
                    "y": y,
                    "title": f"{y} by {x}",
                },
                depends_on=[step1.step_id],
            )
            steps.extend([step1, step2])
            expected_outputs.append("Interactive ChartSpec")

        elif intent == AnalystIntent.DATA_CLEANING_REQUEST:
            steps.append(
                AnalysisStep(
                    description="Formulate non-destructive cleaning proposal for user confirmation",
                    tool_id="propose_cleaning",
                    parameters={
                        "dataset_id": dataset_id,
                        "dataset_version_id": version_id,
                        "operation_type": "drop_duplicates",
                        "rationale": "User requested deduplication.",
                    },
                )
            )
            expected_outputs.append("Cleaning proposal requiring user confirmation")

        else:
            steps.append(
                AnalysisStep(
                    description="Inspect dataset overview and summary profile",
                    tool_id="get_profile",
                    parameters={"dataset_id": dataset_id, "dataset_version_id": version_id},
                )
            )

        return AnalysisPlan(
            user_question=question,
            intent=intent,
            steps=steps,
            required_tools=[s.tool_id for s in steps],
            assumptions=assumptions,
            expected_outputs=expected_outputs,
            status="created",
        )
