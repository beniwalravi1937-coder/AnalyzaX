"""
Grounding, Hallucination Prevention, and Causality Tests (Phase 13)
Verifies non-causal language enforcement and result validation.
"""

from backend.app.engines.ai_analyst.grounding import AnswerValidator, CausalityGuard
from backend.app.engines.ai_analyst.models import ToolResult


def test_causality_guard_sanitization():
    raw_statement = "Increasing price causes lower sales and proves that marketing drives demand."
    sanitized = CausalityGuard.sanitize_causal_language(raw_statement)
    assert "causes" not in sanitized
    assert "is associated with" in sanitized
    assert "proves that" not in sanitized
    assert "suggests that" in sanitized


def test_answer_validator_grounding():
    results = [
        ToolResult(
            call_id="call_001",
            tool_id="execute_sql",
            status="completed",
            metadata={"row_count": 10},
            provenance={"dataset_id": "ds_1", "version_id": "v1"},
        ),
        ToolResult(
            call_id="call_002",
            tool_id="run_statistical_analysis",
            status="completed",
            metadata={"p_value": 0.002},
            provenance={"dataset_id": "ds_1", "version_id": "v1"},
        ),
    ]

    val = AnswerValidator.validate_grounding(
        message="Sales grew significantly.",
        tool_results=results,
    )
    assert val["is_valid"] is True
    assert len(val["citations"]) == 2
    assert val["citations"][0].tool_id == "execute_sql"
    assert val["citations"][1].tool_id == "run_statistical_analysis"


def test_answer_validator_warns_on_failed_tool():
    results = [
        ToolResult(
            call_id="call_fail",
            tool_id="run_ml_experiment",
            status="failed",
            errors=["Insufficient rows for cross-validation."],
        )
    ]
    val = AnswerValidator.validate_grounding(
        message="Model trained.",
        tool_results=results,
    )
    assert len(val["warnings"]) > 0
    assert "run_ml_experiment" in val["warnings"][0]
