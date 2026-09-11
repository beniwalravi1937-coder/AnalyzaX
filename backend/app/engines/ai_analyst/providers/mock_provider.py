"""
AI Analyst Engine — Mock LLM Provider (Phase 13)
Deterministic offline provider enabling 100% test pass rate and predictable local operation.
"""

import re
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

from backend.app.engines.ai_analyst.models import (
    AnalystIntent,
    AnalysisPlan,
    AnalysisStep,
    ToolCall,
)
from backend.app.engines.ai_analyst.providers.base import LLMCapabilities, LLMProvider

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(LLMProvider):
    """Deterministic local provider for offline testing and development."""

    def __init__(self, model_id: str = "mock-analyst-v1"):
        super().__init__(
            provider_id="mock",
            model_id=model_id,
            capabilities=LLMCapabilities(
                supports_tool_calling=True,
                supports_structured_output=True,
                supports_streaming=True,
                max_context_tokens=32000,
                supports_json_mode=True,
            ),
        )

    async def health_check(self) -> bool:
        return True

    def _detect_intent(self, text: str) -> AnalystIntent:
        t = text.lower()
        if "api key" in t or "ignore all" in t or "secret" in t:
            return AnalystIntent.UNSUPPORTED_REQUEST
        if "remove duplicate" in t or "drop missing" in t or "clean data" in t or "fill missing" in t:
            return AnalystIntent.DATA_CLEANING_REQUEST
        if "forecast" in t or "predict next" in t or "future" in t or "time series" in t:
            return AnalystIntent.FORECASTING
        if "train" in t or "machine learning" in t or "predict" in t or "build a model" in t or "classification" in t or "regression" in t:
            return AnalystIntent.MACHINE_LEARNING
        if "significant" in t or "difference" in t or "correlation" in t or "hypothesis" in t or "p-value" in t or "t-test" in t or "anova" in t:
            return AnalystIntent.STATISTICAL_TEST
        if "clean" in t or "quality" in t or "missing" in t or "outlier" in t or "unusual" in t:
            return AnalystIntent.DATA_QUALITY
        if "chart" in t or "plot" in t or "visualize" in t or "show monthly" in t or "graph" in t:
            return AnalystIntent.VISUALIZATION
        if "column" in t or "schema" in t or "what is this dataset" in t or "overview" in t:
            return AnalystIntent.DATASET_OVERVIEW
        if "stock price" in t or "crypto" in t or "buy" in t:
            return AnalystIntent.UNSUPPORTED_REQUEST
        if "average" in t or "sum" in t or "total" in t or "top" in t or "count" in t or "revenue" in t:
            return AnalystIntent.SQL_ANALYSIS
        return AnalystIntent.DESCRIPTIVE_ANALYSIS

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        stop_sequences: Optional[List[str]] = None,
    ) -> str:
        intent = self._detect_intent(prompt)
        if intent == AnalystIntent.UNSUPPORTED_REQUEST:
            if "api key" in prompt.lower() or "secret" in prompt.lower():
                return "I cannot provide system secrets, API keys, or privileged configuration information."
            return "This request exceeds supported platform analytical capabilities."

        return f"Deterministic analytical response for intent: {intent.value}."

    async def structured_generate(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        intent = self._detect_intent(prompt)
        
        # If the requested model is AnalysisPlan
        if response_model == AnalysisPlan:
            steps = []
            if intent == AnalystIntent.DATASET_OVERVIEW:
                steps.append(AnalysisStep(description="Inspect dataset profile", tool_id="get_profile"))
            elif intent == AnalystIntent.DATA_QUALITY:
                steps.append(AnalysisStep(description="Inspect data quality issues", tool_id="get_quality_report"))
            elif intent == AnalystIntent.SQL_ANALYSIS:
                steps.append(AnalysisStep(description="Execute analytical SQL query", tool_id="execute_sql"))
            elif intent == AnalystIntent.STATISTICAL_TEST:
                steps.append(AnalysisStep(description="Run statistical hypothesis test", tool_id="run_statistical_analysis"))
            elif intent == AnalystIntent.MACHINE_LEARNING:
                steps.append(AnalysisStep(description="Run machine learning experiment", tool_id="run_ml_experiment"))
            elif intent == AnalystIntent.FORECASTING:
                steps.append(AnalysisStep(description="Run time-series forecast", tool_id="run_forecast"))
            elif intent == AnalystIntent.VISUALIZATION:
                steps.append(AnalysisStep(description="Execute SQL aggregation", tool_id="execute_sql"))
                steps.append(AnalysisStep(description="Create visualization", tool_id="create_visualization", depends_on=[steps[0].step_id]))
            elif intent == AnalystIntent.DATA_CLEANING_REQUEST:
                steps.append(AnalysisStep(description="Formulate cleaning proposal", tool_id="propose_cleaning"))
            else:
                steps.append(AnalysisStep(description="Explore dataset", tool_id="get_profile"))

            plan = AnalysisPlan(
                user_question=prompt[:100],
                intent=intent,
                steps=steps,
                required_tools=[s.tool_id for s in steps],
                assumptions=["Using active dataset and version."],
                expected_outputs=["Structured analytical evidence"],
            )
            return plan  # type: ignore

        # Fallback empty model validation
        return response_model.model_validate({})
