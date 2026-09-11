"""
AnalyzaX — Phase 25: Controlled Multi-Step Agentic Workflow Engine.
State machine executing analytical step plans with strict human approval boundaries
for consequential mutations.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from backend.app.core.logging import logger
from backend.app.engines.ai_analyst.tools.registry import tool_registry
from backend.app.engines.ai_copilot.models import (
    AIWorkflow,
    AIWorkflowStep,
    RiskLevel,
    WorkflowStatus,
)


MUTATING_TOOL_IDS = {
    "propose_cleaning",
    "apply_cleaning",
    "create_dashboard",
    "delete_dataset",
    "delete_project",
    "share_resource",
    "modify_metric",
}


class WorkflowEngine:
    """Manages execution and human confirmation gates for multi-step AI workflows."""

    def __init__(self) -> None:
        self._workflows: Dict[str, AIWorkflow] = {}

    @classmethod
    def plan_workflow(
        cls,
        goal: str,
        user_id: str,
        workspace_id: str,
        project_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        version_id: Optional[str] = None,
    ) -> AIWorkflow:
        steps = [
            AIWorkflowStep(
                step_id=f"step_{uuid4().hex[:6]}",
                title="Inspect Dataset Profile",
                tool_id="get_profile",
                parameters={"dataset_id": dataset_id or "default"},
                risk_level=RiskLevel.READ_ONLY,
            ),
            AIWorkflowStep(
                step_id=f"step_{uuid4().hex[:6]}",
                title="Detect Anomalies and Correlations",
                tool_id="get_eda_report",
                parameters={"dataset_id": dataset_id or "default", "dataset_version_id": version_id or "v1"},
                risk_level=RiskLevel.ANALYTICAL,
            ),
            AIWorkflowStep(
                step_id=f"step_{uuid4().hex[:6]}",
                title="Propose Cleaning Plan for Inconsistencies",
                tool_id="propose_cleaning",
                parameters={"dataset_id": dataset_id or "default"},
                risk_level=RiskLevel.REVERSIBLE_MUTATION,
                requires_confirmation=True,
            ),
        ]
        return workflow_engine.create_workflow(
            user_id=user_id,
            workspace_id=workspace_id,
            project_id=project_id,
            goal=goal,
            steps=steps,
        )

    @classmethod
    async def execute_workflow(
        cls,
        workflow: AIWorkflow,
        approved_step_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AIWorkflow:
        if approved_step_id:
            workflow_engine.approve_workflow(workflow.workflow_id)
        ctx = context or {"dataset_id": "default", "dataset_version_id": "v1"}
        return await workflow_engine.advance_workflow(workflow.workflow_id, ctx)

    def create_workflow(
        self,
        user_id: str,
        workspace_id: str,
        goal: str,
        steps: List[AIWorkflowStep],
        project_id: Optional[str] = None,
    ) -> AIWorkflow:
        now_iso = datetime.now(timezone.utc).isoformat()
        wf_id = f"wf_{uuid4().hex[:8]}"

        # Mark risk level and confirmation requirements for each step
        for step in steps:
            if step.tool_id in MUTATING_TOOL_IDS:
                step.risk_level = RiskLevel.CONSEQUENTIAL_MUTATION
                step.requires_confirmation = True
            else:
                step.risk_level = RiskLevel.ANALYTICAL
                step.requires_confirmation = False

        workflow = AIWorkflow(
            workflow_id=wf_id,
            user_id=user_id,
            workspace_id=workspace_id,
            project_id=project_id,
            goal=goal,
            status=WorkflowStatus.PLANNED,
            steps=steps,
            current_step_index=0,
            created_at=now_iso,
            updated_at=now_iso,
        )
        self._workflows[wf_id] = workflow
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[AIWorkflow]:
        return self._workflows.get(workflow_id)

    async def advance_workflow(
        self,
        workflow_id: str,
        context: Dict[str, Any],
    ) -> AIWorkflow:
        """
        Executes pending workflow steps sequentially.
        Pauses and transitions to WAITING_FOR_APPROVAL if a step requires human confirmation.
        """
        wf = self.get_workflow(workflow_id)
        if not wf:
            raise ValueError(f"Workflow '{workflow_id}' not found.")

        if wf.status in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED):
            return wf

        wf.status = WorkflowStatus.RUNNING
        now_iso = datetime.now(timezone.utc).isoformat()
        wf.updated_at = now_iso

        while wf.current_step_index < len(wf.steps):
            step = wf.steps[wf.current_step_index]

            # Check human approval boundary
            if step.requires_confirmation and wf.status != WorkflowStatus.WAITING_FOR_APPROVAL:
                # Check if this step was explicitly approved
                if not wf.approved_at:
                    wf.status = WorkflowStatus.WAITING_FOR_APPROVAL
                    step.status = WorkflowStatus.WAITING_FOR_APPROVAL
                    wf.updated_at = datetime.now(timezone.utc).isoformat()
                    logger.info(f"Workflow {wf.workflow_id} paused at step {step.step_id} for user approval.")
                    return wf

            # Execute step via ToolRegistry
            step.status = WorkflowStatus.RUNNING
            step.started_at = datetime.now(timezone.utc).isoformat()

            try:
                from backend.app.engines.ai_analyst.models import ToolCall
                tool_call = ToolCall(
                    call_id=f"call_{uuid4().hex[:6]}",
                    tool_id=step.tool_id,
                    arguments=step.parameters,
                )
                tool_result = await tool_registry.execute(tool_call, context)

                step.status = WorkflowStatus.COMPLETED
                step.completed_at = datetime.now(timezone.utc).isoformat()
                step.result_reference = {
                    "tool_id": step.tool_id,
                    "status": getattr(tool_result, "status", "completed"),
                    "result": getattr(tool_result, "result", None),
                    "errors": getattr(tool_result, "errors", []),
                }
                wf.current_step_index += 1
                # Reset single-step approval
                wf.approved_at = None

            except Exception as e:
                logger.error(f"Step {step.step_id} failed in workflow {wf.workflow_id}: {e}")
                step.status = WorkflowStatus.FAILED
                step.error = str(e)
                step.completed_at = datetime.now(timezone.utc).isoformat()
                wf.status = WorkflowStatus.FAILED
                wf.updated_at = datetime.now(timezone.utc).isoformat()
                return wf

        wf.status = WorkflowStatus.COMPLETED
        wf.updated_at = datetime.now(timezone.utc).isoformat()
        return wf

    def approve_workflow(self, workflow_id: str) -> AIWorkflow:
        wf = self.get_workflow(workflow_id)
        if not wf:
            raise ValueError(f"Workflow '{workflow_id}' not found.")
        wf.approved_at = datetime.now(timezone.utc).isoformat()
        wf.status = WorkflowStatus.RUNNING
        return wf

    def cancel_workflow(self, workflow_id: str) -> AIWorkflow:
        wf = self.get_workflow(workflow_id)
        if not wf:
            raise ValueError(f"Workflow '{workflow_id}' not found.")
        wf.status = WorkflowStatus.CANCELLED
        wf.updated_at = datetime.now(timezone.utc).isoformat()
        return wf


workflow_engine = WorkflowEngine()
