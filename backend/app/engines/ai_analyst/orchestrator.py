"""
AI Analyst Engine — Main Orchestrator (Phase 13)
Coordinates Intent -> Planning -> Tool Execution Loop -> Grounding -> Response Generation.
Never performs LLM calculations; strictly delegates to registered deterministic engines.
"""

import time
from typing import Any, Dict, List, Optional
from uuid import uuid4

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.ai_analyst.exceptions import AIAnalystException, AIErrorCode
from backend.app.engines.ai_analyst.grounding import (
    AnswerValidator,
    CausalityGuard,
    PromptInjectionGuard,
    SecretFilter,
)
from backend.app.engines.ai_analyst.models import (
    AnalystChatResponse,
    AnalystIntent,
    AnalystMessage,
    AnalystMessageRole,
    AnalysisPlan,
    AnalysisReference,
    CleaningProposal,
    ToolCall,
    ToolResult,
)
from backend.app.engines.ai_analyst.planner import AnalysisPlanner, IntentClassifier
from backend.app.engines.ai_analyst.prompts.templates import (
    build_context_prompt,
    build_system_prompt,
    build_user_message_prompt,
)
from backend.app.engines.ai_analyst.providers.factory import get_llm_provider
from backend.app.engines.ai_analyst.sessions import context_manager, session_manager
from backend.app.engines.ai_analyst.tools.registry import tool_registry


class AIAnalystOrchestrator:
    """The central analytical coordinator for AnalyzaX AI Analyst."""

    def __init__(self) -> None:
        self.provider = get_llm_provider()
        self.planner = AnalysisPlanner(self.provider)

    async def execute_inquiry(
        self,
        message: str,
        session_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        dataset_version_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AnalystChatResponse:
        start_time = time.perf_counter()
        options = options or {}

        # 1. Resolve session
        if session_id:
            session = session_manager.get_session(session_id)
            if not dataset_id:
                dataset_id = session.dataset_id
            if not dataset_version_id:
                dataset_version_id = session.dataset_version_id
        else:
            session = session_manager.create_session(
                title=message[:30] + ("..." if len(message) > 30 else ""),
                dataset_id=dataset_id,
                dataset_version_id=dataset_version_id,
            )
            session_id = session.session_id

        # Update session with active dataset
        if dataset_id and session.dataset_id != dataset_id:
            session.dataset_id = dataset_id
            session.dataset_version_id = dataset_version_id
            session_manager.save_session(session)

        # 2. Append User Message
        user_msg = AnalystMessage(
            role=AnalystMessageRole.USER,
            content=message,
        )
        session_manager.append_message(session_id, user_msg)

        # 3. Security Checks: Prompt Injection & Secret Extraction
        if "api key" in message.lower() or "secret" in message.lower() or "password" in message.lower():
            refusal = "I cannot provide system secrets, API keys, credentials, or privileged internal parameters."
            resp = AnalystChatResponse(
                session_id=session_id,
                status="rejected",
                message=refusal,
                intent=AnalystIntent.UNSUPPORTED_REQUEST,
                warnings=["Security policy: secret extraction request blocked."],
            )
            session_manager.append_message(
                session_id,
                AnalystMessage(role=AnalystMessageRole.ASSISTANT, content=refusal, intent=AnalystIntent.UNSUPPORTED_REQUEST),
            )
            return resp

        if PromptInjectionGuard.is_adversarial(message):
            refusal = "Adversarial command pattern detected. Please submit valid analytical inquiries regarding your dataset."
            resp = AnalystChatResponse(
                session_id=session_id,
                status="rejected",
                message=refusal,
                intent=AnalystIntent.UNSUPPORTED_REQUEST,
                warnings=["Adversarial pattern blocked."],
            )
            session_manager.append_message(
                session_id,
                AnalystMessage(role=AnalystMessageRole.ASSISTANT, content=refusal, intent=AnalystIntent.UNSUPPORTED_REQUEST),
            )
            return resp

        # 4. Context Resolution
        ds_context = None
        if dataset_id:
            try:
                ds_context = context_manager.get_dataset_context(dataset_id, dataset_version_id)
            except Exception as e:
                logger.warning(f"Could not load dataset context: {e}")

        # 5. Intent Classification
        intent = IntentClassifier.classify(message)

        # Check for unsupported domain queries
        if intent == AnalystIntent.UNSUPPORTED_REQUEST:
            unsupported_msg = (
                "This request exceeds supported platform capabilities. "
                "AnalyzaX provides descriptive statistics, SQL queries, EDA, hypothesis testing, "
                "machine learning benchmarking, time-series forecasting, and interactive visualizations."
            )
            resp = AnalystChatResponse(
                session_id=session_id,
                status="rejected",
                message=unsupported_msg,
                intent=intent,
            )
            session_manager.append_message(
                session_id,
                AnalystMessage(role=AnalystMessageRole.ASSISTANT, content=unsupported_msg, intent=intent),
            )
            return resp

        # 6. Analysis Planning
        plan = self.planner.plan(message, intent, ds_context)

        # 7. Tool Execution Loop
        tool_calls: List[ToolCall] = []
        tool_results: List[ToolResult] = []
        visualizations: List[Dict[str, Any]] = []
        cleaning_proposal: Optional[CleaningProposal] = None
        warnings: List[str] = []

        context_dict = {
            "dataset_id": dataset_id,
            "dataset_version_id": dataset_version_id,
            "session_id": session_id,
        }

        call_count = 0
        for step in plan.steps:
            if call_count >= settings.AI_MAX_TOOL_CALLS:
                warnings.append(f"Reached maximum allowed tool executions ({settings.AI_MAX_TOOL_CALLS}).")
                break

            t_call = ToolCall(
                tool_id=step.tool_id,
                arguments=step.parameters,
                reasoning_summary=step.description,
            )
            tool_calls.append(t_call)
            call_count += 1

            try:
                res = await tool_registry.execute(t_call, context_dict)
                tool_results.append(res)
                step.status = "completed" if res.status == "completed" else "failed"

                # Extract visualization spec if present
                if res.status == "completed" and res.result:
                    if "chart_spec" in res.result:
                        visualizations.append(res.result["chart_spec"])
                    if "cleaning_proposal" in res.result:
                        cleaning_proposal = CleaningProposal(**res.result["cleaning_proposal"])

            except AIAnalystException as aie:
                step.status = "failed"
                tool_results.append(
                    ToolResult(
                        call_id=t_call.call_id,
                        tool_id=t_call.tool_id,
                        status="failed",
                        errors=[aie.message],
                    )
                )
                warnings.append(f"Tool {step.tool_id} error: {aie.message}")
            except Exception as ex:
                step.status = "failed"
                tool_results.append(
                    ToolResult(
                        call_id=t_call.call_id,
                        tool_id=t_call.tool_id,
                        status="failed",
                        errors=[str(ex)],
                    )
                )
                warnings.append(f"Tool {step.tool_id} unexpected error: {str(ex)}")

        # 8. Result Synthesis & Grounding
        validation_info = AnswerValidator.validate_grounding(
            message="",
            tool_results=tool_results,
            valid_columns=ds_context.column_names if ds_context else [],
        )
        citations = validation_info["citations"]
        warnings.extend(validation_info["warnings"])

        # Formulate grounded synthesis text
        response_text = self._synthesize_answer(
            intent=intent,
            tool_results=tool_results,
            ds_context=ds_context,
            cleaning_proposal=cleaning_proposal,
        )

        # Apply safety filters
        response_text = SecretFilter.filter_secrets(response_text)
        response_text = CausalityGuard.sanitize_causal_language(response_text)

        # 9. Follow-up Intelligence
        follow_ups = self._generate_follow_up_questions(intent, ds_context)

        # 10. Construct Final Response
        final_resp = AnalystChatResponse(
            session_id=session_id,
            status="completed",
            message=response_text,
            intent=intent,
            plan=plan,
            tool_calls=tool_calls,
            tool_results=tool_results,
            visualizations=visualizations,
            citations=citations,
            cleaning_proposal=cleaning_proposal,
            warnings=warnings,
            limitations=[
                "Analyses are computed deterministically based on available dataset observations.",
                "Correlation or association does not imply causality.",
            ],
            follow_up_questions=follow_ups,
            provenance={
                "dataset_id": dataset_id,
                "dataset_version_id": dataset_version_id,
                "execution_time_ms": (time.perf_counter() - start_time) * 1000,
                "provider": self.provider.provider_id,
                "model": self.provider.model_id,
            },
        )

        # 11. Append Assistant Message to Session
        assistant_msg = AnalystMessage(
            role=AnalystMessageRole.ASSISTANT,
            content=response_text,
            intent=intent,
            plan=plan,
            tool_calls=tool_calls,
            tool_results=tool_results,
            visualizations=visualizations,
            citations=citations,
            cleaning_proposal=cleaning_proposal,
            warnings=warnings,
            limitations=final_resp.limitations,
            follow_up_questions=follow_ups,
            provenance=final_resp.provenance,
        )
        session_manager.append_message(session_id, assistant_msg)

        return final_resp

    def _synthesize_answer(
        self,
        intent: AnalystIntent,
        tool_results: List[ToolResult],
        ds_context: Optional[Any],
        cleaning_proposal: Optional[CleaningProposal],
    ) -> str:
        """Grounded synthesis of tool findings."""
        if cleaning_proposal:
            return (
                f"### Data Cleaning Proposal\n\n"
                f"I have prepared a proposal for **{cleaning_proposal.operation_type}**.\n\n"
                f"- **Rationale:** {cleaning_proposal.rationale}\n"
                f"- **Expected Impact:** {cleaning_proposal.impact_summary}\n\n"
                f"> **Confirmation Required:** AnalyzaX enforces data immutability. Please review the proposal card below and click 'Confirm & Apply' to generate an auditable new version of your dataset."
            )

        completed = [tr for tr in tool_results if tr.status == "completed"]
        if not completed:
            failed_errs = [", ".join(tr.errors) for tr in tool_results if tr.errors]
            return f"Unable to complete analytical execution: {'; '.join(failed_errs) if failed_errs else 'unknown error'}."

        parts = []

        # Check for profile
        prof_res = next((tr.result for tr in completed if tr.tool_id == "get_profile"), None)
        if prof_res:
            parts.append(
                f"### Dataset Profile Summary\n\n"
                f"The dataset contains **{prof_res.get('row_count', 0):,} rows** and **{prof_res.get('column_count', 0)} columns**.\n"
                f"Columns profiled: {', '.join(list(prof_res.get('columns', {}).keys())[:10])}."
            )

        # Check for quality
        qual_res = next((tr.result for tr in completed if tr.tool_id == "get_quality_report"), None)
        if qual_res:
            score = qual_res.get("overall_score", 0)
            violations = qual_res.get("total_violations", 0)
            parts.append(
                f"### Data Quality Assessment\n\n"
                f"- **Overall Quality Score:** **{score:.1f} / 100**\n"
                f"- **Total Rule Violations:** {violations}\n"
                f"- **Critical Issues:** {qual_res.get('critical_violations', 0)}"
            )

        # Check for SQL
        sql_res = next((tr.result for tr in completed if tr.tool_id == "execute_sql"), None)
        if sql_res:
            row_count = sql_res.get("row_count", 0)
            rows = sql_res.get("rows", [])
            cols = sql_res.get("columns", [])
            parts.append(
                f"### Analytical Query Results\n\n"
                f"Executed deterministic DuckDB aggregation yielding **{row_count} rows** across {len(cols)} columns."
            )
            if rows:
                first_row = rows[0]
                sample_metrics = [f"**{k}:** {v}" for k, v in list(first_row.items())[:4]]
                parts.append(f"Top observation: {', '.join(sample_metrics)}")

        # Check for Statistics
        stat_res = next((tr.result for tr in completed if tr.tool_id == "run_statistical_analysis"), None)
        if stat_res:
            p_val = stat_res.get("p_value")
            stat_val = stat_res.get("statistic_value")
            is_sig = stat_res.get("is_significant", False)
            method = stat_res.get("method", "Hypothesis test")
            parts.append(
                f"### Statistical Evaluation ({method})\n\n"
                f"- **Test Statistic:** {stat_val:.4f if isinstance(stat_val, (int, float)) else stat_val}\n"
                f"- **p-value:** {f'{p_val:.4e}' if isinstance(p_val, float) else p_val}\n"
                f"- **Statistical Significance:** {'Statistically significant at alpha=0.05' if is_sig else 'Not statistically significant at alpha=0.05'}\n"
                f"- **Interpretation:** {stat_res.get('interpretation', 'Results show observed variation.')}"
            )

        # Check for ML
        ml_res = next((tr.result for tr in completed if tr.tool_id == "run_ml_experiment"), None)
        if ml_res:
            best_model = ml_res.get("best_model_id", "Model")
            best_metric = ml_res.get("best_metric_value", 0.0)
            parts.append(
                f"### Machine Learning Evaluation\n\n"
                f"- **Top Performing Algorithm:** `{best_model}`\n"
                f"- **Primary Metric Score:** **{best_metric:.4f}**\n"
                f"- **Evaluated Candidates:** {ml_res.get('models_trained', 0)} algorithms."
            )

        # Check for Forecasting
        fc_res = next((tr.result for tr in completed if tr.tool_id == "run_forecast"), None)
        if fc_res:
            best_m = fc_res.get("best_model_id", "Forecaster")
            horizon = fc_res.get("horizon", 6)
            pts = fc_res.get("forecast_points", [])
            parts.append(
                f"### Time-Series Forecast\n\n"
                f"- **Best Model:** `{best_m}`\n"
                f"- **Projection Horizon:** {horizon} steps\n"
                f"- Projected {len(pts)} future periods with confidence intervals."
            )

        # Check for Visualization
        viz_res = next((tr.result for tr in completed if tr.tool_id == "create_visualization"), None)
        if viz_res:
            parts.append(
                f"### Visualization Generated\n\n"
                f"An interactive chart has been created from aggregated data."
            )

        if not parts:
            return "Analysis completed successfully with verified analytical engines."

        return "\n\n".join(parts)

    def _generate_follow_up_questions(
        self,
        intent: AnalystIntent,
        ds_context: Optional[Any],
    ) -> List[str]:
        """Generates 2-3 logical analytical follow-up inquiries based on context."""
        follow_ups = []
        if intent in (AnalystIntent.SQL_ANALYSIS, AnalystIntent.DESCRIPTIVE_ANALYSIS):
            follow_ups.append("Would you like to visualize this trend as a chart?")
            follow_ups.append("Should we test whether group differences are statistically significant?")
            follow_ups.append("Would you like to forecast future values based on this metric?")
        elif intent == AnalystIntent.STATISTICAL_TEST:
            follow_ups.append("Would you like to train an ML model predicting this target?")
            follow_ups.append("Would you like to visualize the distribution comparison?")
        elif intent == AnalystIntent.DATASET_OVERVIEW:
            follow_ups.append("Run a comprehensive data quality check on this dataset?")
            follow_ups.append("Show top categories and value distributions?")
        elif intent == AnalystIntent.FORECASTING:
            follow_ups.append("Compare forecasting model accuracy against a baseline?")
            follow_ups.append("Plot the forecast with 95% confidence intervals?")
        else:
            follow_ups.append("Show summary profile for this dataset?")
            follow_ups.append("Check for unusual values or outliers?")
        return follow_ups[:3]


orchestrator = AIAnalystOrchestrator()
