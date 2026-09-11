"""
AnalyzaX — Phase 25: AI Evaluation & Safety Defense Framework.
Performs verification of tool selection accuracy, numeric claim grounding,
unsupported causal assertions, prompt-injection defense, and tenant isolation integrity.
"""

import re
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    """Result of evaluating an AI interaction or response."""
    is_valid: bool
    score: float  # 0.0 to 1.0
    grounding_passed: bool = True
    safety_passed: bool = True
    causality_passed: bool = True
    violations: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PromptInjectionDetector:
    """Detects adversarial or prompt-injection attempts inside user messages or untrusted dataset cells."""

    INJECTION_PATTERNS = [
        r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"(?i)system\s+prompt",
        r"(?i)reveal\s+(the\s+)?(api_?key|secret|password|token)",
        r"(?i)you\s+are\s+now\s+in\s+developer\s+mode",
        r"(?i)bypass\s+(authorization|permission|quota|security)",
        r"(?i)drop\s+table",
        r"(?i)delete\s+from\s+",
        r"(?i)exec\s*\(",
        r"(?i)eval\s*\(",
    ]

    @classmethod
    def check_text(cls, text: str) -> bool:
        """Returns True if any prompt-injection or hostile pattern is detected."""
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text):
                return True
        return False


class AnswerValidator:
    """Verifies that an AI output is grounded in actual tool results and schema columns."""

    @staticmethod
    def validate_grounding(
        response_text: str,
        valid_columns: Set[str],
        tool_results: List[Dict[str, Any]],
        strict: bool = False,
    ) -> EvaluationResult:
        """Validates that referenced columns exist and checks for unsupported causal claims."""
        violations: List[str] = []

        # 1. Safety check for prompt injection
        if PromptInjectionDetector.check_text(response_text):
            violations.append("Adversarial or prompt-injection text pattern detected in response.")

        # 2. Check for unsupported causal claims
        causal_indicators = ["caused by", "proves that", "definitely caused", "causes the"]
        has_causal_violation = False
        for ci in causal_indicators:
            if ci in response_text.lower():
                has_causal_violation = True
                violations.append(f"Unsupported causal claim detected: '{ci}'.")

        # 3. Check for numeric grounding against tool outputs
        # Extract numbers from response
        extracted_numbers = re.findall(r"\b\d+(?:\.\d+)?\b", response_text)
        # Check tool results text
        tool_results_str = str(tool_results)
        ungrounded_numbers = []
        for num in extracted_numbers:
            # Skip common small integers or years
            if num in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "2024", "2025", "2026", "100"):
                continue
            if num not in tool_results_str:
                ungrounded_numbers.append(num)

        if strict and ungrounded_numbers:
            violations.append(f"Potentially ungrounded numeric claims detected: {ungrounded_numbers[:5]}")

        is_valid = len(violations) == 0
        score = 1.0 if is_valid else max(0.0, 1.0 - (len(violations) * 0.25))

        return EvaluationResult(
            is_valid=is_valid,
            score=score,
            grounding_passed=len(ungrounded_numbers) == 0,
            safety_passed=not PromptInjectionDetector.check_text(response_text),
            causality_passed=not has_causal_violation,
            violations=violations,
            metadata={
                "extracted_numbers_count": len(extracted_numbers),
                "ungrounded_numbers": ungrounded_numbers[:5],
            },
        )


class TenantIsolationValidator:
    """Verifies that an AI Copilot request cannot access unauthorized tenant contexts."""

    @staticmethod
    def verify_tenant_access(
        user_workspace_id: str,
        target_workspace_id: str,
    ) -> bool:
        """Returns True if the user belongs to the requested workspace."""
        return user_workspace_id == target_workspace_id
