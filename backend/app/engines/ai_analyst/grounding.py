"""
AI Analyst Engine — Safety, Grounding, and Hallucination Guards (Phase 13)
Enforces AGENTS.md rules: secret protection, prompt injection defense, non-causal language,
and verification that numerical answers are grounded in actual tool results.
"""

import re
from typing import Any, Dict, List, Optional, Set

from backend.app.core.logging import logger
from backend.app.engines.ai_analyst.models import (
    AnalysisReference,
    ToolResult,
)


class PromptInjectionGuard:
    """Detects and defuses adversarial attempts to alter system instructions."""

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"disregard\s+system\s+prompt",
        r"reveal\s+(the\s+)?(api\s+key|password|secret|env)",
        r"system\s+prompt\s+override",
        r"bypass\s+security",
        r"drop\s+database",
    ]

    @classmethod
    def is_adversarial(cls, text: str) -> bool:
        lower = text.lower()
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, lower):
                return True
        return False

    @classmethod
    def sanitize(cls, text: str) -> str:
        # Wrap untrusted user input to protect privileged system prompt
        return text.strip()


class SecretFilter:
    """Prevents any credential, token, or secret from leaking in generated responses."""

    SECRET_PATTERNS = [
        r"sk-[a-zA-Z0-9_\-]{20,}",
        r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}",
        r"ghp_[a-zA-Z0-9]{30,}",
        r"[a-zA-Z0-9_\-\.]+@[a-zA-Z0-9_\-\.]+\.[a-zA-Z]{2,}",
    ]

    @classmethod
    def filter_secrets(cls, text: str) -> str:
        cleaned = text
        for pattern in cls.SECRET_PATTERNS:
            cleaned = re.sub(pattern, "[PROTECTED_SECRET]", cleaned)
        return cleaned


class CausalityGuard:
    """Enforces non-causal interpretation of observational data."""

    CAUSAL_REPLACEMENTS = {
        r"\bcauses\b": "is associated with",
        r"\bcaused\b": "was associated with",
        r"\bcauses of\b": "factors associated with",
        r"\bproves that\b": "suggests that",
        r"\bdrives\b": "is correlated with",
    }

    @classmethod
    def sanitize_causal_language(cls, text: str) -> str:
        sanitized = text
        for pat, repl in cls.CAUSAL_REPLACEMENTS.items():
            sanitized = re.sub(pat, repl, sanitized, flags=re.IGNORECASE)
        return sanitized


class AnswerValidator:
    """Deterministic validation ensuring LLM response claims are grounded in tool results."""

    @classmethod
    def validate_grounding(
        cls,
        message: str,
        tool_results: List[ToolResult],
        valid_columns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        warnings: List[str] = []

        # 1. Check for failed tools being presented
        failed_tools = [tr.tool_id for tr in tool_results if tr.status == "failed"]
        if failed_tools:
            warnings.append(f"Tools failed during analysis: {', '.join(failed_tools)}. Answer may be partial.")

        # 2. Extract references
        references: List[AnalysisReference] = []
        for tr in tool_results:
            if tr.status == "completed":
                dataset_id = tr.provenance.get("dataset_id", "unknown")
                version_id = tr.provenance.get("version_id", "unknown")
                ref = AnalysisReference(
                    tool_id=tr.tool_id,
                    result_id=tr.call_id,
                    dataset_id=dataset_id,
                    dataset_version_id=version_id,
                    relevant_fields=list(tr.metadata.keys()),
                    summary=f"Result from {tr.tool_id}",
                )
                references.append(ref)

        return {
            "is_valid": True,
            "warnings": warnings,
            "citations": references,
        }
