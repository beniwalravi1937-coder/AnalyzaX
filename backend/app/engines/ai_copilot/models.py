"""
AnalyzaX — Phase 25: AI Copilot, Agentic Workflows & Multi-Step Intelligence Models.
Defines contracts for contextual copilot sessions, agent workflows, approval gates,
dashboard plans, analytical stories, and next-step recommendations.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.engines.insights.models import Insight, InsightEvidence


class WorkflowStatus(str, Enum):
    PLANNED = "PLANNED"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RiskLevel(str, Enum):
    READ_ONLY = "READ_ONLY"
    ANALYTICAL = "ANALYTICAL"
    REVERSIBLE_MUTATION = "REVERSIBLE_MUTATION"
    CONSEQUENTIAL_MUTATION = "CONSEQUENTIAL_MUTATION"
    SECURITY_SENSITIVE = "SECURITY_SENSITIVE"
    EXTERNAL_SIDE_EFFECT = "EXTERNAL_SIDE_EFFECT"


class CopilotContext(BaseModel):
    """User and analytical context provided to the Copilot."""
    workspace_id: str
    project_id: Optional[str] = None
    dataset_id: Optional[str] = None
    dataset_version_id: Optional[str] = None
    active_dashboard_id: Optional[str] = None
    active_query: Optional[str] = None
    selected_columns: List[str] = Field(default_factory=list)
    selected_metrics: List[str] = Field(default_factory=list)
    user_id: Optional[str] = None


class AIAction(BaseModel):
    """A proposed or executed action within the system."""
    action_id: str
    action_type: str  # 'create_dashboard', 'apply_cleaning', 'delete_project', 'export_report'
    resource_type: str
    resource_id: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = True
    risk_level: RiskLevel = RiskLevel.CONSEQUENTIAL_MUTATION
    preview: Optional[Dict[str, Any]] = None


class AIWorkflowStep(BaseModel):
    """A single step in a multi-step agentic analytical workflow."""
    step_id: str
    title: str
    tool_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.PLANNED
    risk_level: RiskLevel = RiskLevel.ANALYTICAL
    requires_confirmation: bool = False
    result_reference: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class AIWorkflow(BaseModel):
    """A multi-step analytical workflow executed with human approval boundaries."""
    workflow_id: str
    user_id: str
    workspace_id: str
    project_id: Optional[str] = None
    goal: str
    status: WorkflowStatus = WorkflowStatus.PLANNED
    steps: List[AIWorkflowStep] = Field(default_factory=list)
    current_step_index: int = 0
    created_at: str
    updated_at: str
    approved_at: Optional[str] = None
    provenance: Dict[str, Any] = Field(default_factory=dict)


class NextAnalysisRecommendation(BaseModel):
    """Proactive recommendation for the next best analytical step."""
    recommendation_id: str
    type: str  # 'segment_comparison', 'statistical_significance', 'forecast_projection', 'outlier_investigation'
    title: str
    reason: str
    expected_value: str
    required_inputs: List[str] = Field(default_factory=list)
    tool_plan: List[str] = Field(default_factory=list)
    risk: RiskLevel = RiskLevel.ANALYTICAL
    estimated_cost: float = 0.0


class DashboardPlanComponent(BaseModel):
    """Component specification in an AI-generated dashboard plan."""
    component_type: str  # 'chart', 'kpi', 'table', 'narrative'
    title: str
    chart_spec: Optional[Dict[str, Any]] = None
    metric_name: Optional[str] = None
    dimensions: List[str] = Field(default_factory=list)
    layout: Dict[str, Any] = Field(default_factory=dict)  # x, y, w, h


class DashboardPlan(BaseModel):
    """Structured plan for constructing an intelligent dashboard."""
    plan_id: str
    title: str
    description: str
    dataset_id: str
    version_id: str
    components: List[DashboardPlanComponent] = Field(default_factory=list)
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    requires_approval: bool = True
    created_at: str


class AnalyticalStory(BaseModel):
    """Narrative analytical story connecting evidence, findings, and conclusions."""
    story_id: str
    title: str
    question: str
    context: Dict[str, Any] = Field(default_factory=dict)
    observations: List[str] = Field(default_factory=list)
    evidence: List[InsightEvidence] = Field(default_factory=list)
    findings: List[str] = Field(default_factory=list)
    explanations: str
    limitations: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    charts: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str


class CopilotResponse(BaseModel):
    """Complete structured response from the AI Copilot."""
    response_id: str
    session_id: str
    message: str
    intent: str
    insights: List[Insight] = Field(default_factory=list)
    visualizations: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[NextAnalysisRecommendation] = Field(default_factory=list)
    actions: List[AIAction] = Field(default_factory=list)
    evidence: List[InsightEvidence] = Field(default_factory=list)
    workflow: Optional[AIWorkflow] = None
    dashboard_plan: Optional[DashboardPlan] = None
    analytical_story: Optional[AnalyticalStory] = None
    provenance: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
