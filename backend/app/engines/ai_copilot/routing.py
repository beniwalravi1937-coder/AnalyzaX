"""
AnalyzaX — Phase 25: AI Model Router & Cost Controller.
Routes analytical tasks by complexity to optimal models and enforces request budgets.
"""

from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class TaskComplexity(str, Enum):
    SIMPLE_CLASSIFICATION = "SIMPLE_CLASSIFICATION"
    ROUTINE_ANALYSIS = "ROUTINE_ANALYSIS"
    COMPLEX_SYNTHESIS = "COMPLEX_SYNTHESIS"
    STORY_GENERATION = "STORY_GENERATION"


class AIModelPolicy(BaseModel):
    task_complexity: TaskComplexity
    target_model: str
    max_tokens: int = 2048
    temperature: float = 0.0
    provider: str = "openrouter"

    @property
    def model(self) -> str:
        return self.target_model


class AIRequestBudget(BaseModel):
    max_steps: int = 8
    max_tool_calls: int = 10
    max_context_tokens: int = 4000
    max_output_tokens: int = 2048
    max_execution_seconds: float = 60.0


class AIUsageRecord(BaseModel):
    record_id: str
    workspace_id: str
    user_id: str
    operation_type: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    estimated_cost: float
    created_at: str


class ModelRouter:
    """Policy-based model selector optimizing for accuracy, context capacity, and cost."""

    def __init__(self) -> None:
        self._policies: Dict[TaskComplexity, AIModelPolicy] = {
            TaskComplexity.SIMPLE_CLASSIFICATION: AIModelPolicy(
                task_complexity=TaskComplexity.SIMPLE_CLASSIFICATION,
                target_model="anthropic/claude-3-haiku",
                max_tokens=512,
                temperature=0.0,
            ),
            TaskComplexity.ROUTINE_ANALYSIS: AIModelPolicy(
                task_complexity=TaskComplexity.ROUTINE_ANALYSIS,
                target_model="anthropic/claude-3.5-sonnet",
                max_tokens=2048,
                temperature=0.0,
            ),
            TaskComplexity.COMPLEX_SYNTHESIS: AIModelPolicy(
                task_complexity=TaskComplexity.COMPLEX_SYNTHESIS,
                target_model="anthropic/claude-3.5-sonnet",
                max_tokens=4096,
                temperature=0.0,
            ),
            TaskComplexity.STORY_GENERATION: AIModelPolicy(
                task_complexity=TaskComplexity.STORY_GENERATION,
                target_model="anthropic/claude-3.5-sonnet",
                max_tokens=4096,
                temperature=0.2,
            ),
        }

    def select_model(self, query: str = "") -> AIModelPolicy:
        """Classifies task complexity from query and selects an appropriate model policy."""
        q = (query or "").lower()
        if any(w in q for w in ["story", "narrative", "executive summary", "report"]):
            return self.route(TaskComplexity.STORY_GENERATION)
        elif any(w in q for w in ["why", "synthesize", "investigate", "root cause", "explain"]):
            return self.route(TaskComplexity.COMPLEX_SYNTHESIS)
        elif any(w in q for w in ["what is", "list", "show", "get", "profile"]):
            return self.route(TaskComplexity.SIMPLE_CLASSIFICATION)
        return self.route(TaskComplexity.ROUTINE_ANALYSIS)

    def route(self, complexity_or_query: Any, workspace_id: Optional[str] = None) -> AIModelPolicy:
        if isinstance(complexity_or_query, TaskComplexity):
            return self._policies.get(complexity_or_query, self._policies[TaskComplexity.ROUTINE_ANALYSIS])
        if isinstance(complexity_or_query, str):
            return self.select_model(complexity_or_query)
        return self._policies[TaskComplexity.ROUTINE_ANALYSIS]

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimates cost in USD based on model pricing per million tokens."""
        # Baseline rough estimates (e.g. $3 / 1M input, $15 / 1M output for Claude 3.5 Sonnet)
        input_cost = (input_tokens / 1_000_000.0) * 3.00
        output_cost = (output_tokens / 1_000_000.0) * 15.00
        return round(input_cost + output_cost, 6)


model_router = ModelRouter()

