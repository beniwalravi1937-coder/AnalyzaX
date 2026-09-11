"""
AI Analyst Engine — Domain Models and Data Contracts (Phase 13)
Strictly validated Pydantic models for intent, planning, tool contracts, provenance, and conversational state.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class AnalystIntent(str, Enum):
    DATASET_OVERVIEW = "DATASET_OVERVIEW"
    DATA_QUALITY = "DATA_QUALITY"
    DESCRIPTIVE_ANALYSIS = "DESCRIPTIVE_ANALYSIS"
    DISTRIBUTION = "DISTRIBUTION"
    COMPARISON = "COMPARISON"
    RANKING = "RANKING"
    TREND = "TREND"
    CORRELATION = "CORRELATION"
    RELATIONSHIP = "RELATIONSHIP"
    GROUP_ANALYSIS = "GROUP_ANALYSIS"
    STATISTICAL_TEST = "STATISTICAL_TEST"
    REGRESSION = "REGRESSION"
    MACHINE_LEARNING = "MACHINE_LEARNING"
    FORECASTING = "FORECASTING"
    ANOMALY_EXPLORATION = "ANOMALY_EXPLORATION"
    VISUALIZATION = "VISUALIZATION"
    SQL_ANALYSIS = "SQL_ANALYSIS"
    EXPLANATION = "EXPLANATION"
    FOLLOW_UP = "FOLLOW_UP"
    MODEL_COMPARISON = "MODEL_COMPARISON"
    FORECAST_COMPARISON = "FORECAST_COMPARISON"
    DATA_CLEANING_REQUEST = "DATA_CLEANING_REQUEST"
    UNSUPPORTED_REQUEST = "UNSUPPORTED_REQUEST"


class ToolPermission(str, Enum):
    READ_ONLY = "READ_ONLY"
    DERIVED_RESULT = "DERIVED_RESULT"
    PROPOSAL_ONLY = "PROPOSAL_ONLY"
    USER_CONFIRMATION_REQUIRED = "USER_CONFIRMATION_REQUIRED"


class ToolDefinition(BaseModel):
    tool_id: str
    display_name: str
    description: str
    purpose: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    required_context: List[str] = Field(default_factory=list)
    permission: ToolPermission = ToolPermission.READ_ONLY
    timeout_seconds: int = 60
    supports_async: bool = False
    deterministic: bool = True
    side_effect_level: str = "none"


class AnalysisStep(BaseModel):
    step_id: str = Field(default_factory=lambda: f"step_{uuid4().hex[:8]}")
    description: str
    tool_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed, skipped


class AnalysisPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: f"plan_{uuid4().hex[:8]}")
    user_question: str
    intent: AnalystIntent
    steps: List[AnalysisStep] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    expected_outputs: List[str] = Field(default_factory=list)
    status: str = "created"  # created, in_progress, completed, partial_failure, failed


class ToolCall(BaseModel):
    call_id: str = Field(default_factory=lambda: f"call_{uuid4().hex[:8]}")
    tool_id: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    reasoning_summary: Optional[str] = None
    requested_by: str = "ai_analyst"
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ToolResult(BaseModel):
    call_id: str
    tool_id: str
    status: str  # completed, failed, rejected
    result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0


class AnalysisReference(BaseModel):
    reference_id: str = Field(default_factory=lambda: f"ref_{uuid4().hex[:8]}")
    tool_id: str
    result_id: Optional[str] = None
    dataset_id: str
    dataset_version_id: str
    relevant_fields: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class VisualizationIntent(BaseModel):
    chart_type: str = "bar"
    x: Optional[str] = None
    y: Optional[str] = None
    series: Optional[str] = None
    color: Optional[str] = None
    aggregation: Optional[str] = None
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    sorting: Optional[Dict[str, Any]] = None
    title: Optional[str] = None
    rationale: Optional[str] = None


class CleaningProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: f"prop_{uuid4().hex[:8]}")
    dataset_id: str
    dataset_version_id: str
    operation_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    rationale: str
    impact_summary: str
    requires_confirmation: bool = True
    status: str = "proposed"  # proposed, approved, rejected, applied


class AnalystMessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class AnalystMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: f"msg_{uuid4().hex[:8]}")
    role: AnalystMessageRole
    content: str
    intent: Optional[AnalystIntent] = None
    plan: Optional[AnalysisPlan] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)
    tool_results: List[ToolResult] = Field(default_factory=list)
    visualizations: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[AnalysisReference] = Field(default_factory=list)
    cleaning_proposal: Optional[CleaningProposal] = None
    warnings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class DatasetContextSummary(BaseModel):
    dataset_id: str
    dataset_version_id: str
    dataset_name: Optional[str] = None
    row_count: int = 0
    column_count: int = 0
    column_names: List[str] = Field(default_factory=list)
    column_types: Dict[str, str] = Field(default_factory=dict)
    numeric_columns: List[str] = Field(default_factory=list)
    categorical_columns: List[str] = Field(default_factory=list)
    datetime_columns: List[str] = Field(default_factory=list)
    missing_summary: Dict[str, float] = Field(default_factory=dict)
    sample_preview: List[Dict[str, Any]] = Field(default_factory=list)
    available_engines: List[str] = Field(default_factory=list)


class AnalystSession(BaseModel):
    session_id: str = Field(default_factory=lambda: f"sess_{uuid4().hex[:8]}")
    title: str = "New Analysis"
    dataset_id: Optional[str] = None
    dataset_version_id: Optional[str] = None
    messages: List[AnalystMessage] = Field(default_factory=list)
    active_columns: List[str] = Field(default_factory=list)
    recent_result_references: List[AnalysisReference] = Field(default_factory=list)
    context_summary: Optional[str] = None
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class AnalystChatRequest(BaseModel):
    session_id: Optional[str] = None
    workspace_id: Optional[str] = None
    dataset_id: Optional[str] = None
    dataset_version_id: Optional[str] = None
    message: str
    options: Dict[str, Any] = Field(default_factory=dict)


class AnalystChatResponse(BaseModel):
    response_id: str = Field(default_factory=lambda: f"resp_{uuid4().hex[:8]}")
    session_id: str
    status: str = "completed"  # completed, clarification_needed, failed, rejected
    message: str
    intent: AnalystIntent
    plan: Optional[AnalysisPlan] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)
    tool_results: List[ToolResult] = Field(default_factory=list)
    visualizations: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[AnalysisReference] = Field(default_factory=list)
    cleaning_proposal: Optional[CleaningProposal] = None
    warnings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class PlanRequest(BaseModel):
    dataset_id: str
    dataset_version_id: str
    question: str
    session_id: Optional[str] = None


class ExecutePlanRequest(BaseModel):
    session_id: str
    plan: AnalysisPlan
    dataset_id: str
    dataset_version_id: str
