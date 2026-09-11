"""
Orchestrator and Planning Tests (Phase 13)
Verifies intent classification, multi-step planning, and orchestration workflow.
"""

import pytest
from backend.app.engines.ai_analyst.models import AnalystIntent, DatasetContextSummary
from backend.app.engines.ai_analyst.orchestrator import orchestrator
from backend.app.engines.ai_analyst.planner import IntentClassifier


def test_intent_classification():
    assert IntentClassifier.classify("What columns and schema exist in this dataset?") == AnalystIntent.DATASET_OVERVIEW
    assert IntentClassifier.classify("Is my data clean and are there any missing values?") == AnalystIntent.DATA_QUALITY
    assert IntentClassifier.classify("What is the average revenue by region?") == AnalystIntent.SQL_ANALYSIS
    assert IntentClassifier.classify("Is revenue significantly different between branches?") == AnalystIntent.STATISTICAL_TEST
    assert IntentClassifier.classify("Train a machine learning model to predict churn") == AnalystIntent.MACHINE_LEARNING
    assert IntentClassifier.classify("Forecast revenue for the next 6 months") == AnalystIntent.FORECASTING
    assert IntentClassifier.classify("Create a chart showing sales by category") == AnalystIntent.VISUALIZATION
    assert IntentClassifier.classify("Remove duplicate records from this table") == AnalystIntent.DATA_CLEANING_REQUEST


def test_analysis_planner_generates_steps():
    context = DatasetContextSummary(
        dataset_id="ds_sales",
        dataset_version_id="v1",
        row_count=1000,
        column_count=4,
        column_names=["region", "revenue", "units", "order_date"],
        numeric_columns=["revenue", "units"],
        categorical_columns=["region"],
        datetime_columns=["order_date"],
    )

    plan = orchestrator.planner.plan(
        question="What is the average revenue by region?",
        intent=AnalystIntent.SQL_ANALYSIS,
        context=context,
    )
    assert len(plan.steps) >= 1
    assert plan.steps[0].tool_id == "execute_sql"
    assert "revenue" in plan.steps[0].parameters.get("sql", "").lower()


@pytest.mark.asyncio
async def test_orchestrator_inquiry_flow():
    resp = await orchestrator.execute_inquiry(
        message="Summarize data quality and violations in this dataset",
    )
    assert resp.status == "completed"
    assert resp.intent == AnalystIntent.DATA_QUALITY
    assert len(resp.follow_up_questions) > 0
    assert len(resp.limitations) > 0
