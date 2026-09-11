"""
AnalyzaX — Phase 25: Context Assembly & Token Budgeting Engine.
Structured context assembly with relevance filtering, bounded row samples,
metadata-first retrieval, and token budgeting.
"""

from typing import Any, Dict, List, Optional
from backend.app.core.logging import logger
from backend.app.engines.ai_copilot.models import CopilotContext


MAX_CONTEXT_TOKENS = 4000
CHARS_PER_TOKEN = 4


class ContextEngine:
    """Assembles and optimizes analytical context for the AI Copilot."""

    @classmethod
    def assemble_context(
        cls,
        context: CopilotContext,
        dataset_meta: Optional[Dict[str, Any]] = None,
        profile_summary: Optional[Dict[str, Any]] = None,
        quality_summary: Optional[Dict[str, Any]] = None,
        recent_results: Optional[List[Dict[str, Any]]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        token_budget: int = MAX_CONTEXT_TOKENS,
        profile_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Builds a compact, prioritized context payload that strictly respects the token budget.
        """
        profile_summary = profile_summary or profile_data
        budget_chars = token_budget * CHARS_PER_TOKEN
        assembled: Dict[str, Any] = {
            "workspace_id": context.workspace_id,
            "project_id": context.project_id,
            "dataset_id": context.dataset_id,
            "version_id": context.dataset_version_id,
            "columns": [],
        }
        if profile_summary and "columns" in profile_summary:
            cols = profile_summary["columns"]
            assembled["columns"] = list(cols.keys())[:20] if isinstance(cols, dict) else cols[:20]
        current_chars = len(str(assembled))

        # 1. Dataset Schema & Metadata (High Priority)
        if dataset_meta:
            cols = dataset_meta.get("columns", [])
            schema_summary = [{"name": c.get("name"), "type": c.get("type")} for c in cols[:50]]
            meta_block = {
                "row_count": dataset_meta.get("row_count"),
                "column_count": len(cols),
                "columns": schema_summary,
            }
            meta_str = str(meta_block)
            if current_chars + len(meta_str) < budget_chars:
                assembled["dataset_schema"] = meta_block
                current_chars += len(meta_str)

        # 2. Quality Score & Major Warnings (High Priority)
        if quality_summary:
            q_block = {
                "quality_score": quality_summary.get("score") or quality_summary.get("quality_score"),
                "critical_violations": quality_summary.get("violations", [])[:3],
            }
            q_str = str(q_block)
            if current_chars + len(q_str) < budget_chars:
                assembled["quality_overview"] = q_block
                current_chars += len(q_str)

        # 3. Profile Summary (Medium Priority - Compacted)
        if profile_summary:
            cols = profile_summary.get("columns", {})
            if isinstance(cols, dict):
                compact_profile = {}
                for col_name, cinfo in list(cols.items())[:15]:
                    compact_profile[col_name] = {
                        "missing_pct": cinfo.get("missing_percentage", 0),
                        "unique_count": cinfo.get("unique_count"),
                        "mean": cinfo.get("mean"),
                    }
                p_str = str(compact_profile)
                if current_chars + len(p_str) < budget_chars:
                    assembled["profile_overview"] = compact_profile
                    current_chars += len(p_str)

        # 4. User Selected Context (High Priority)
        if context.selected_columns:
            assembled["selected_columns"] = context.selected_columns[:10]
        if context.selected_metrics:
            assembled["selected_metrics"] = context.selected_metrics[:10]

        # 5. Recent Analytical Results (Truncated)
        if recent_results:
            truncated_results = []
            for res in recent_results[:3]:
                truncated_results.append({
                    "type": res.get("type"),
                    "summary": str(res.get("summary", ""))[:200],
                    "key_metrics": res.get("metrics", {}),
                })
            r_str = str(truncated_results)
            if current_chars + len(r_str) < budget_chars:
                assembled["recent_results"] = truncated_results
                current_chars += len(r_str)

        # 6. Conversation History (Recent Turns Only)
        if conversation_history:
            recent_turns = conversation_history[-4:]
            turns_str = str(recent_turns)
            if current_chars + len(turns_str) < budget_chars:
                assembled["recent_conversation"] = recent_turns

        return assembled

    build_context = assemble_context
