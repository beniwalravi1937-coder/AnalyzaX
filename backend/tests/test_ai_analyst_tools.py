"""
Tests for AI Analyst Tool Registry and Handlers (Phase 13)
Verifies tool definitions, permissions, schema validation, and tool execution.
"""

import pytest
from backend.app.engines.ai_analyst.exceptions import AIAnalystException, AIErrorCode
from backend.app.engines.ai_analyst.models import ToolCall, ToolPermission
from backend.app.engines.ai_analyst.tools.registry import ToolRegistry, tool_registry


def test_tool_registry_registration():
    tools = tool_registry.list_tools()
    assert len(tools) >= 16
    tool_ids = [t.tool_id for t in tools]
    assert "get_dataset_context" in tool_ids
    assert "get_profile" in tool_ids
    assert "get_quality_report" in tool_ids
    assert "get_eda_report" in tool_ids
    assert "execute_sql" in tool_ids
    assert "validate_sql" in tool_ids
    assert "run_statistical_analysis" in tool_ids
    assert "run_ml_experiment" in tool_ids
    assert "run_forecast" in tool_ids
    assert "create_visualization" in tool_ids
    assert "propose_cleaning" in tool_ids


def test_tool_registry_permissions():
    exec_sql = tool_registry.get_tool("execute_sql")
    assert exec_sql.permission == ToolPermission.READ_ONLY

    ml_tool = tool_registry.get_tool("run_ml_experiment")
    assert ml_tool.permission == ToolPermission.DERIVED_RESULT

    clean_tool = tool_registry.get_tool("propose_cleaning")
    assert clean_tool.permission == ToolPermission.PROPOSAL_ONLY


def test_tool_registry_unknown_tool():
    with pytest.raises(AIAnalystException) as exc:
        tool_registry.get_tool("non_existent_tool_123")
    assert exc.value.error_code == AIErrorCode.AI_TOOL_NOT_FOUND


@pytest.mark.asyncio
async def test_propose_cleaning_handler():
    call = ToolCall(
        tool_id="propose_cleaning",
        arguments={
            "dataset_id": "ds_test",
            "dataset_version_id": "v1",
            "operation_type": "drop_duplicates",
            "rationale": "Deduplicate sales table",
        },
    )
    result = await tool_registry.execute(call, {"dataset_id": "ds_test"})
    assert result.status == "completed"
    assert "cleaning_proposal" in result.result
    proposal = result.result["cleaning_proposal"]
    assert proposal["requires_confirmation"] is True
    assert proposal["operation_type"] == "drop_duplicates"


@pytest.mark.asyncio
async def test_get_statistics_catalog_handler():
    call = ToolCall(tool_id="get_statistics", arguments={})
    result = await tool_registry.execute(call, {})
    assert result.status == "completed"
    assert "methods" in result.result
    assert len(result.result["methods"]) > 0
