"""
AI Analyst Application Service (Phase 13)
Orchestrates high-level conversational flows, plan generation, tool execution,
and user-confirmed data cleaning delegations to Phase 6.
"""

from typing import Any, Dict, List, Optional

from backend.app.core.logging import logger
from backend.app.engines.ai_analyst.exceptions import AIAnalystException, AIErrorCode
from backend.app.engines.ai_analyst.models import (
    AnalystChatRequest,
    AnalystChatResponse,
    AnalystMessage,
    AnalystSession,
    AnalysisPlan,
    ToolDefinition,
)
from backend.app.engines.ai_analyst.orchestrator import orchestrator
from backend.app.engines.ai_analyst.sessions import context_manager, session_manager
from backend.app.engines.ai_analyst.tools.registry import tool_registry
from backend.app.services.cleaning.plan_service import PlanService
from backend.app.services.cleaning.version_service import VersionService


class AIAnalystService:
    """Application Service for the AI Data Analyst."""

    def __init__(self) -> None:
        self._orchestrator = orchestrator
        self._session_manager = session_manager
        self._context_manager = context_manager
        self._tool_registry = tool_registry
        self._plan_service = PlanService()
        self._version_service = VersionService()

    async def chat(self, request: AnalystChatRequest) -> AnalystChatResponse:
        """Processes user natural language query end-to-end with quota enforcement."""
        workspace_id = request.workspace_id or request.options.get("workspace_id")
        if workspace_id:
            from backend.app.services.usage import quota_service, usage_service
            from backend.app.engines.usage.metrics import UsageMetrics

            # Check feature entitlement and quota
            quota_service.enforce_feature(workspace_id, "AI_ANALYST")
            quota_service.enforce_quota(
                workspace_id=workspace_id,
                metric_key=UsageMetrics.AI_ANALYST_MESSAGES.key,
                quantity=1.0,
            )

        resp = await self._orchestrator.execute_inquiry(
            message=request.message,
            session_id=request.session_id,
            dataset_id=request.dataset_id,
            dataset_version_id=request.dataset_version_id,
            options=request.options,
        )

        if workspace_id and resp.status != "rejected":
            from backend.app.services.usage import usage_service
            from backend.app.engines.usage.metrics import UsageMetrics
            usage_service.record_usage(
                workspace_id=workspace_id,
                metric_key=UsageMetrics.AI_ANALYST_MESSAGES.key,
                quantity=1.0,
                operation_type="ai_chat",
                resource_type="session",
                resource_id=resp.session_id,
                idempotency_key=f"ai_{resp.response_id}",
            )

        return resp

    def create_plan(
        self,
        dataset_id: str,
        question: str,
        version_id: Optional[str] = None,
    ) -> AnalysisPlan:
        """Generates an inspectable multi-step execution plan without executing tools."""
        from backend.app.engines.ai_analyst.planner import IntentClassifier
        ctx = self._context_manager.get_dataset_context(dataset_id, version_id)
        intent = IntentClassifier.classify(question)
        return self._orchestrator.planner.plan(question, intent, ctx)

    def list_sessions(self) -> List[AnalystSession]:
        return self._session_manager.list_sessions()

    def create_session(
        self,
        title: str = "New Analysis",
        dataset_id: Optional[str] = None,
        dataset_version_id: Optional[str] = None,
    ) -> AnalystSession:
        return self._session_manager.create_session(
            title=title,
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
        )

    def get_session(self, session_id: str) -> AnalystSession:
        return self._session_manager.get_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        return self._session_manager.delete_session(session_id)

    def get_messages(self, session_id: str) -> List[AnalystMessage]:
        session = self.get_session(session_id)
        return session.messages

    def list_tools(self) -> List[ToolDefinition]:
        return self._tool_registry.list_tools()

    def confirm_cleaning_proposal(
        self,
        session_id: str,
        proposal_id: str,
    ) -> Dict[str, Any]:
        """
        Executes a user-confirmed cleaning operation via Phase 6 Transformation Service,
        creating an auditable new immutable dataset version.
        """
        session = self.get_session(session_id)
        # Find proposal in session messages
        target_proposal = None
        for msg in reversed(session.messages):
            if msg.cleaning_proposal and msg.cleaning_proposal.proposal_id == proposal_id:
                target_proposal = msg.cleaning_proposal
                break

        if not target_proposal:
            raise AIAnalystException(
                AIErrorCode.AI_TOOL_CALL_INVALID,
                f"Cleaning proposal '{proposal_id}' not found in session '{session_id}'.",
            )

        # Delegate to Transformation Plan Engine
        dataset_id = target_proposal.dataset_id
        parent_version_id = target_proposal.dataset_version_id
        op_str = target_proposal.operation_type.upper()

        try:
            from uuid import uuid4
            from backend.app.engines.transformations.models import (
                TransformationPlan,
                TransformationStep,
                TransformationType,
            )
            # Match operation type or default to DROP_DUPLICATES
            try:
                op_type = TransformationType(op_str)
            except ValueError:
                op_type = TransformationType.DROP_DUPLICATES

            step = TransformationStep(
                step_id=f"step_{uuid4().hex[:8]}",
                type=op_type,
                parameters=target_proposal.parameters,
                description=target_proposal.rationale,
            )
            plan = TransformationPlan(
                plan_id=f"plan_{uuid4().hex[:8]}",
                dataset_id=dataset_id,
                source_version_id=parent_version_id,
                steps=[step],
            )
            new_version = self._plan_service.apply_plan(
                dataset_id=dataset_id,
                plan=plan,
                label=f"AI Analyst: {op_type.value}",
            )
            target_proposal.status = "applied"
            self._session_manager.save_session(session)

            return {
                "status": "success",
                "proposal_id": proposal_id,
                "dataset_id": dataset_id,
                "new_version_id": new_version.version_id,
                "row_count": new_version.row_count,
            }
        except Exception as exc:
            logger.error(f"Failed to apply confirmed cleaning proposal: {exc}")
            raise AIAnalystException(
                AIErrorCode.AI_ANALYSIS_FAILED,
                f"Failed to apply cleaning proposal: {str(exc)}",
            )


ai_analyst_service = AIAnalystService()
