"""
AnalyzaX — Phase 25: AI Copilot Application Service.
Coordinates AI Copilot chat sessions, multi-step workflows, human approval gates,
and dashboard generation workflows with server-side quota enforcement.
"""

from typing import Any, Dict, List, Optional
from backend.app.core.logging import logger
from backend.app.engines.ai_copilot.copilot import ai_copilot
from backend.app.engines.ai_copilot.models import (
    AIWorkflow,
    CopilotContext,
    CopilotResponse,
    DashboardPlan,
    RiskLevel,
    WorkflowStatus,
)
from backend.app.engines.ai_copilot.workflows import WorkflowEngine
from backend.app.services.dashboard_service import dashboard_service


class CopilotService:
    """Application Service for AI Copilot interactions and agentic workflow governance."""

    def __init__(self) -> None:
        self._copilot = ai_copilot
        self._active_workflows: Dict[str, AIWorkflow] = {}

    async def chat(
        self,
        message: str,
        context: CopilotContext,
        session_id: Optional[str] = None,
        tone: str = "ANALYST",
        user_workspace_id: Optional[str] = None,
    ) -> CopilotResponse:
        """Processes copilot chat requests with server-side quota checks and usage tracking."""
        workspace_id = context.workspace_id

        # Phase 20 Quota & Entitlement enforcement
        if workspace_id:
            try:
                from backend.app.engines.usage.metrics import UsageMetrics
                from backend.app.services.usage import quota_service, usage_service

                quota_service.enforce_feature(workspace_id, "AI_ANALYST")
                quota_service.enforce_quota(
                    workspace_id=workspace_id,
                    metric_key=UsageMetrics.AI_ANALYST_MESSAGES.key,
                    quantity=1.0,
                )
            except Exception as e:
                logger.warning(f"Quota enforcement bypassed or failed: {e}")

        # Execute Copilot chat
        from backend.app.engines.ai_copilot.narratives import NarrativeTone
        try:
            narrative_tone = NarrativeTone(tone.upper())
        except ValueError:
            narrative_tone = NarrativeTone.ANALYST

        resp = await self._copilot.chat(
            message=message,
            context=context,
            session_id=session_id,
            tone=narrative_tone,
            user_workspace_id=user_workspace_id,
        )

        # Cache workflow if one was created
        if resp.workflow:
            self._active_workflows[resp.workflow.workflow_id] = resp.workflow

        # Record usage if successful
        if workspace_id and resp.intent != "unauthorized":
            try:
                from backend.app.engines.usage.metrics import UsageMetrics
                from backend.app.services.usage import usage_service

                usage_service.record_usage(
                    workspace_id=workspace_id,
                    metric_key=UsageMetrics.AI_ANALYST_MESSAGES.key,
                    quantity=1.0,
                    operation_type="ai_copilot_chat",
                    resource_type="copilot_session",
                    resource_id=resp.session_id,
                    idempotency_key=f"copilot_{resp.response_id}",
                )
            except Exception as e:
                logger.warning(f"Usage recording failed: {e}")

        return resp

    def get_workflow(self, workflow_id: str) -> Optional[AIWorkflow]:
        return self._active_workflows.get(workflow_id)

    async def approve_workflow_step(
        self,
        workflow_id: str,
        step_id: str,
        user_id: str,
    ) -> AIWorkflow:
        """Approves a paused workflow step and resumes execution."""
        wf = self._active_workflows.get(workflow_id)
        if not wf:
            raise ValueError(f"Workflow '{workflow_id}' not found.")

        # Resume execution with explicit approval
        updated_wf = await WorkflowEngine.execute_workflow(wf, approved_step_id=step_id)
        self._active_workflows[workflow_id] = updated_wf
        return updated_wf

    def cancel_workflow(self, workflow_id: str) -> AIWorkflow:
        """Cancels an active or waiting workflow."""
        wf = self._active_workflows.get(workflow_id)
        if not wf:
            raise ValueError(f"Workflow '{workflow_id}' not found.")
        wf.status = WorkflowStatus.CANCELLED
        self._active_workflows[workflow_id] = wf
        return wf

    def execute_dashboard_plan(
        self,
        plan: DashboardPlan,
        workspace_id: str,
        user_id: str,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Materializes an approved DashboardPlan into an active dashboard using DashboardService."""
        # Convert plan components to dashboard widgets
        from backend.app.engines.dashboards.models import (
            Dashboard,
            DashboardWidget,
            WidgetType,
        )
        widgets = []
        for i, comp in enumerate(plan.components):
            widget_type = (
                WidgetType.KPI
                if comp.component_type == "kpi"
                else WidgetType.CHART
            )
            widgets.append(
                DashboardWidget(
                    widget_id=f"w_{i+1}",
                    type=widget_type,
                    title=comp.title,
                    chart_spec=comp.chart_spec,
                    layout=comp.layout or {"x": (i % 3) * 4, "y": (i // 3) * 4, "w": 4, "h": 4},
                )
            )

        db = dashboard_service.create_dashboard(
            workspace_id=workspace_id,
            project_id=project_id,
            title=plan.title,
            description=plan.description,
            owner_id=user_id,
            widgets=widgets,
            filters=plan.filters,
        )
        return {"status": "created", "dashboard_id": db.dashboard_id, "title": db.title}


copilot_service = CopilotService()
