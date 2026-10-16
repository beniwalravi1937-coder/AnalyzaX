"""
AnalyzaX — Phase 25: AI Copilot Coordinator.
The central intelligence orchestrator connecting Context Engine, Governed Metrics,
Proactive Insights, Multi-Step Agentic Workflows, Dashboard Planning, and Memory.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.core.logging import logger
from backend.app.engines.ai_analyst.providers.factory import get_llm_provider
from backend.app.engines.ai_copilot.context import ContextEngine
from backend.app.engines.ai_copilot.dashboard_builder import DashboardBuilderEngine
from backend.app.engines.ai_copilot.evaluation import (
    AnswerValidator,
    PromptInjectionDetector,
    TenantIsolationValidator,
)
from backend.app.engines.ai_copilot.memory import AnalyticalMemoryEngine
from backend.app.engines.ai_copilot.models import (
    AIAction,
    AnalyticalStory,
    CopilotContext,
    CopilotResponse,
    DashboardPlan,
    NextAnalysisRecommendation,
    RiskLevel,
)
from backend.app.engines.ai_copilot.narratives import NarrativeGenerator, NarrativeTone
from backend.app.engines.ai_copilot.provenance import ProvenanceEngine
from backend.app.engines.ai_copilot.recommendations import RecommendationEngine
from backend.app.engines.ai_copilot.routing import ModelRouter
from backend.app.engines.ai_copilot.workflows import WorkflowEngine
from backend.app.engines.insights.detector import ProactiveInsightDetector
from backend.app.engines.insights.models import Insight, InsightEvidence
from backend.app.engines.insights.ranker import InsightRanker
from backend.app.engines.insights.repository import insight_repository
from backend.app.engines.semantic.engine import SemanticEngine
from backend.app.engines.semantic.models import MetricStatus
from backend.app.engines.semantic.repository import semantic_repo



class AICopilot:
    """Unified AI Copilot orchestrator for interactive analytics, proactive discovery, and workflows."""

    def __init__(self) -> None:
        self.router = ModelRouter()
        self.memory = AnalyticalMemoryEngine()

    async def chat(
        self,
        message: str,
        context: CopilotContext,
        session_id: Optional[str] = None,
        tone: NarrativeTone = NarrativeTone.ANALYST,
        user_workspace_id: Optional[str] = None,
    ) -> CopilotResponse:
        """Processes a conversational prompt with safety, semantic resolution, and deterministic grounding."""
        session_id = session_id or f"session_{uuid.uuid4().hex[:12]}"
        response_id = f"resp_{uuid.uuid4().hex[:12]}"
        now_str = datetime.now(timezone.utc).isoformat()

        # 1. Tenant isolation gate
        if user_workspace_id and not TenantIsolationValidator.verify_tenant_access(
            user_workspace_id, context.workspace_id
        ):
            return CopilotResponse(
                response_id=response_id,
                session_id=session_id,
                message="Access denied: Cannot query across workspace isolation boundaries.",
                intent="unauthorized",
                provenance=ProvenanceEngine.create_provenance(
                    provider="system", model="security_gate"
                ).model_dump(),
                created_at=now_str,
            )

        # 2. Prompt-injection gate
        if PromptInjectionDetector.check_text(message):
            return CopilotResponse(
                response_id=response_id,
                session_id=session_id,
                message="I detected an adversarial instruction or request for system credentials. I treat all inputs strictly as analytical data.",
                intent="injection_rejected",
                provenance=ProvenanceEngine.create_provenance(
                    provider="system", model="safety_gate"
                ).model_dump(),
                created_at=now_str,
            )

        # 3. Model routing policy check
        model_policy = self.router.select_model(message)
        route_decision = self.router.route(message, context.workspace_id)

        # 4. Scoped analytical memory retrieval
        recent_memory = self.memory.get_recent_context(
            scope="SESSION",
            scope_id=session_id,
            limit=5,
        )

        # 5. Semantic intelligence resolution
        active_metrics = semantic_repo.list_metrics(
            workspace_id=context.workspace_id,
            project_id=context.project_id,
            status=MetricStatus.ACTIVE,
        )
        resolved_metric = None
        for word in message.split():
            clean_word = word.strip("?,.!").lower()
            if len(clean_word) > 2:
                matched = SemanticEngine.resolve_term(clean_word, active_metrics)
                if matched:
                    resolved_metric = matched
                    break

        # Check for ambiguity in metric requests
        ambiguous = SemanticEngine.detect_ambiguity(message, active_metrics)
        if ambiguous:
            return CopilotResponse(
                response_id=response_id,
                session_id=session_id,
                message=f"I found multiple metrics matching your request: {', '.join([m.name for m in ambiguous])}. Could you please clarify which one you mean?",
                intent="semantic_clarification",
                provenance=ProvenanceEngine.create_provenance(
                    provider=route_decision.provider,
                    model=route_decision.model,
                ).model_dump(),
                created_at=now_str,
            )

        # 6. Assemble context with real dataset metadata and profile summary
        dataset_meta = None
        profile_summary = None
        if context.dataset_id:
            try:
                from backend.app.services.dataset_service import dataset_service
                from backend.app.services.profiling_service import profiling_service

                ds_obj = dataset_service.get_dataset(context.dataset_id)
                if ds_obj:
                    dataset_meta = ds_obj
                prof_obj = profiling_service.get_cached_profile(context.dataset_id)
                if prof_obj:
                    profile_summary = prof_obj.model_dump() if hasattr(prof_obj, "model_dump") else prof_obj
            except Exception as e:
                logger.debug(f"AI Copilot context fetch note: {e}")

        assembled_context = ContextEngine.build_context(
            context=context,
            dataset_meta=dataset_meta,
            profile_summary=profile_summary,
            conversation_history=recent_memory,
        )

        # 7. Intent Dispatch
        lower_msg = message.lower()
        insights: List[Insight] = []
        visualizations: List[Dict[str, Any]] = []
        recommendations: List[NextAnalysisRecommendation] = []
        actions: List[AIAction] = []
        evidence_list: List[InsightEvidence] = []
        dashboard_plan: Optional[DashboardPlan] = None
        analytical_story: Optional[AnalyticalStory] = None
        workflow = None

        # Intent A: Dashboard Planning
        if "dashboard" in lower_msg or "build dashboard" in lower_msg:
            intent = "build_dashboard"
            dashboard_plan = DashboardBuilderEngine.plan_dashboard(
                title=f"Dashboard: {message[:40]}",
                description="AI-assisted dashboard plan based on governed metrics and schema.",
                dataset_id=context.dataset_id or "default_dataset",
                version_id=context.dataset_version_id or "v1",
                governed_metrics=active_metrics,
                selected_dimensions=context.selected_columns or [],
            )

            actions.append(
                AIAction(
                    action_id=f"act_{uuid.uuid4().hex[:8]}",
                    action_type="create_dashboard",
                    resource_type="dashboard",
                    parameters={"plan_id": dashboard_plan.plan_id},
                    requires_confirmation=True,
                    risk_level=RiskLevel.CONSEQUENTIAL_MUTATION,
                    preview={"components_count": len(dashboard_plan.components)},
                )
            )
            response_text = (
                f"I have constructed a structured dashboard plan with {len(dashboard_plan.components)} "
                "components (KPIs and visual breakdowns). Please review and approve the preview before creation."
            )

        # Intent B: Story / Narrative / Executive Briefing
        elif any(k in lower_msg for k in ["story", "narrative", "executive summary", "explain this"]):
            intent = "analytical_story"
            # Discover insights for story
            insights = insight_repository.list_insights(
                workspace_id=context.workspace_id,
                dataset_id=context.dataset_id,
            )
            analytical_story = NarrativeGenerator.generate_story(
                question=message,
                insights=insights,
                tone=tone,
            )
            response_text = analytical_story.explanations

        # Intent C: Multi-step Investigation / Workflow
        elif any(k in lower_msg for k in ["why", "investigate", "drop", "decline", "unusual", "pattern"]):
            intent = "multi_step_investigation"
            workflow = WorkflowEngine.plan_workflow(
                goal=message,
                user_id=context.user_id or "user_default",
                workspace_id=context.workspace_id,
                project_id=context.project_id,
                dataset_id=context.dataset_id or "dataset_default",
                version_id=context.dataset_version_id or "v1",
            )
            # Execute workflow steps safely
            workflow = await WorkflowEngine.execute_workflow(workflow)

            # Proactively detect insights on dataset if available
            insights = insight_repository.list_insights(
                workspace_id=context.workspace_id,
                dataset_id=context.dataset_id,
            )
            response_text = (
                f"I initiated an analytical investigation: '{workflow.goal}'. "
                f"Completed {len(workflow.steps)} diagnostic steps across schema, profiling, and distribution variance."
            )
            if workflow.status == "WAITING_FOR_APPROVAL":
                response_text += " A consequential transformation step requires your explicit approval."

        # Intent D: General Question / Semantic Query / Conversational Intelligence
        else:
            intent = "general_query"
            if resolved_metric:
                base_text = (
                    f"Resolved term to governed metric '{resolved_metric.name}' "
                    f"({resolved_metric.expression}, unit: {resolved_metric.unit or 'units'}). "
                    "Deterministic calculation can be queried against the active dataset."
                )
            else:
                base_text = (
                    f"I analyzed your inquiry against dataset '{context.dataset_id or 'current'}'. "
                    "What specific segment, trend, or statistical test would you like to explore?"
                )

            # Invoke configured LLM provider (Google Gemini) if active
            provider = get_llm_provider()
            if provider and getattr(provider, "provider_id", "") != "mock":
                try:
                    system_prompt = (
                        "You are AnalyzaX AI Copilot, an elite data intelligence assistant powered by Google Gemini. "
                        "You assist data analysts, engineers, and executives with dataset exploration, exploratory data analysis (EDA), "
                        "SQL queries, statistical tests, predictive modeling, and data cleaning.\n\n"
                        "Mandatory Constitutional Rules:\n"
                        "1. Rely strictly on the dataset schema, column names, data types, and statistical profile provided in the context.\n"
                        "2. Never fabricate numbers or perform manual unverified arithmetic. All calculations in AnalyzaX are computed deterministically.\n"
                        "3. Do not make unsupported causal claims (e.g. avoid 'caused by', 'proves that'). Use observational terminology ('associated with', 'correlated with').\n"
                        "4. Format your output in clean, elegant Markdown with concise bullet points, bold key terms, and SQL or Python code snippets where helpful.\n"
                        f"5. Maintain an analytical tone suited for an {tone.value} audience."
                    )
                    prompt_parts = [
                        f"User Message: {message}",
                        f"Analytical Context: {json.dumps(assembled_context, default=str)}",
                    ]
                    if resolved_metric:
                        prompt_parts.append(
                            f"Governed Metric: {resolved_metric.name} ({resolved_metric.expression}, unit: {resolved_metric.unit or 'units'})"
                        )

                    llm_output = await provider.generate(
                        prompt="\n\n".join(prompt_parts),
                        system_prompt=system_prompt,
                        temperature=0.2,
                        max_tokens=2048,
                    )
                    if llm_output and len(llm_output.strip()) > 5:
                        if resolved_metric and resolved_metric.name.lower() not in llm_output.lower():
                            response_text = (
                                f"Resolved term to governed metric '{resolved_metric.name}' "
                                f"({resolved_metric.expression}, unit: {resolved_metric.unit or 'units'}).\n\n"
                                f"{llm_output.strip()}"
                            )
                        else:
                            response_text = llm_output.strip()
                    else:
                        response_text = base_text
                except Exception as exc:
                    logger.warning(f"AI Copilot LLM generation error: {exc}. Gracefully falling back to deterministic response.")
                    response_text = base_text
            else:
                response_text = base_text

        # 8. Generate Contextual Recommendations
        recommendations = RecommendationEngine.generate_recommendations(
            insights=insights,
            active_columns=context.selected_columns,
        )

        # 9. Grounding & Safety Validation
        validation = AnswerValidator.validate_grounding(
            response_text=response_text,
            valid_columns=set(context.selected_columns),
            tool_results=[s.result_reference for s in (workflow.steps if workflow else []) if s.result_reference],
        )
        if not validation.is_valid and validation.violations:
            response_text += f"\n[System Note: {'; '.join(validation.violations)}]"

        # 10. Record Provenance
        provider_name = route_decision.provider
        model_name = route_decision.model
        active_provider = get_llm_provider()
        if active_provider and getattr(active_provider, "provider_id", "") != "mock":
            provider_name = active_provider.provider_id
            model_name = active_provider.model_id

        provenance = ProvenanceEngine.create_provenance(
            provider=provider_name,
            model=model_name,
            dataset_id=context.dataset_id,
            dataset_version_id=context.dataset_version_id,
            tool_references=[s.tool_id for s in (workflow.steps if workflow else [])],
        )

        # 11. Save interaction to analytical memory
        self.memory.record_memory(
            scope="SESSION",
            scope_id=session_id,
            key=f"query_{uuid.uuid4().hex[:6]}",
            content={"message": message, "response": response_text, "intent": intent},
        )

        return CopilotResponse(
            response_id=response_id,
            session_id=session_id,
            message=response_text,
            intent=intent,
            insights=insights,
            visualizations=visualizations,
            recommendations=recommendations,
            actions=actions,
            evidence=evidence_list,
            workflow=workflow,
            dashboard_plan=dashboard_plan,
            analytical_story=analytical_story,
            provenance=provenance.model_dump(),
            created_at=now_str,
        )


ai_copilot = AICopilot()
