"""
AI Analyst Engine — Tool Registry & Permission System (Phase 13)
Central registry defining schemas, permissions, timeouts, and resource constraints for all tools.
"""

from typing import Any, Callable, Coroutine, Dict, List, Optional
from backend.app.engines.ai_analyst.exceptions import AIAnalystException, AIErrorCode
from backend.app.engines.ai_analyst.models import (
    ToolCall,
    ToolDefinition,
    ToolPermission,
    ToolResult,
)


class ToolRegistry:
    """Central registry and policy enforcement engine for all analytical tools."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}
        self._handlers: Dict[str, Callable[[ToolCall, Dict[str, Any]], Coroutine[Any, Any, ToolResult]]] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        definitions = [
            ToolDefinition(
                tool_id="get_dataset_context",
                display_name="Get Dataset Context",
                description="Retrieves metadata, column names, data types, and row count for the active dataset.",
                purpose="Metadata inspection and schema understanding",
                permission=ToolPermission.READ_ONLY,
                required_context=["dataset_id"],
            ),
            ToolDefinition(
                tool_id="get_profile",
                display_name="Get Dataset Profile",
                description="Returns full column profiles, distributions, missing rates, and summary statistics.",
                purpose="Descriptive statistics and distribution checks",
                permission=ToolPermission.READ_ONLY,
                required_context=["dataset_id"],
            ),
            ToolDefinition(
                tool_id="get_quality_report",
                display_name="Get Quality Report",
                description="Returns data quality score, anomalies, outliers, duplicate checks, and violations.",
                purpose="Data hygiene and quality analysis",
                permission=ToolPermission.READ_ONLY,
                required_context=["dataset_id"],
            ),
            ToolDefinition(
                tool_id="get_eda_report",
                display_name="Get EDA Report",
                description="Returns exploratory data analysis report including findings, correlations, and interactions.",
                purpose="Exploratory data analysis and pattern detection",
                permission=ToolPermission.READ_ONLY,
                required_context=["dataset_id", "dataset_version_id"],
            ),
            ToolDefinition(
                tool_id="execute_sql",
                display_name="Execute Read-Only SQL",
                description="Runs a validated read-only SQL query against DuckDB on the dataset version.",
                purpose="Deterministic data aggregation, grouping, and filtering",
                permission=ToolPermission.READ_ONLY,
                required_context=["dataset_id"],
            ),
            ToolDefinition(
                tool_id="validate_sql",
                display_name="Validate SQL Query",
                description="Validates SQL query syntax, AST safety, and schema compatibility without executing.",
                purpose="Pre-flight SQL safety and typo validation",
                permission=ToolPermission.READ_ONLY,
                required_context=["dataset_id"],
            ),
            ToolDefinition(
                tool_id="get_statistics",
                display_name="Get Statistical Methods Catalog",
                description="Lists available hypothesis tests, correlation methods, and assumptions.",
                purpose="Statistical capability discovery",
                permission=ToolPermission.READ_ONLY,
            ),
            ToolDefinition(
                tool_id="run_statistical_analysis",
                display_name="Run Statistical Analysis",
                description="Executes a deterministic hypothesis test or correlation (Phase 10 Statistics Engine).",
                purpose="Hypothesis testing, p-values, confidence intervals, effect sizes",
                permission=ToolPermission.DERIVED_RESULT,
                required_context=["dataset_id"],
            ),
            ToolDefinition(
                tool_id="run_ml_experiment",
                display_name="Run ML Experiment",
                description="Trains benchmark machine learning models and returns metrics (Phase 11 ML Engine).",
                purpose="Classification, regression, and feature importance",
                permission=ToolPermission.DERIVED_RESULT,
                required_context=["dataset_id"],
            ),
            ToolDefinition(
                tool_id="get_ml_result",
                display_name="Get ML Experiment Result",
                description="Retrieves results, leaderboards, and diagnostics for a prior ML experiment.",
                purpose="ML evaluation and inspection",
                permission=ToolPermission.READ_ONLY,
            ),
            ToolDefinition(
                tool_id="run_forecast",
                display_name="Run Time-Series Forecast",
                description="Trains forecasting models and produces future predictions with intervals (Phase 12).",
                purpose="Time series projection, trends, and seasonality",
                permission=ToolPermission.DERIVED_RESULT,
                required_context=["dataset_id"],
            ),
            ToolDefinition(
                tool_id="get_forecast_result",
                display_name="Get Forecast Result",
                description="Retrieves results, horizon forecasts, and diagnostics for a forecast experiment.",
                purpose="Forecasting evaluation",
                permission=ToolPermission.READ_ONLY,
            ),
            ToolDefinition(
                tool_id="recommend_visualization",
                display_name="Recommend Visualizations",
                description="Recommends optimal chart types and encodings for given columns (Phase 9).",
                purpose="Visual chart recommendation",
                permission=ToolPermission.READ_ONLY,
                required_context=["dataset_id"],
            ),
            ToolDefinition(
                tool_id="create_visualization",
                display_name="Create Visualization Spec",
                description="Builds and validates an analytical ChartSpec using Phase 9 Visualization Engine.",
                purpose="Chart generation",
                permission=ToolPermission.DERIVED_RESULT,
                required_context=["dataset_id"],
            ),
            ToolDefinition(
                tool_id="get_visualization_data",
                display_name="Get Chart Data",
                description="Extracts data payload for a specific chart specification.",
                purpose="Visualization data preview",
                permission=ToolPermission.READ_ONLY,
                required_context=["dataset_id"],
            ),
            ToolDefinition(
                tool_id="propose_cleaning",
                display_name="Propose Data Cleaning Plan",
                description="Generates a structured cleaning proposal for explicit user review without mutating data.",
                purpose="Non-destructive cleaning recommendation",
                permission=ToolPermission.PROPOSAL_ONLY,
                required_context=["dataset_id"],
            ),
        ]
        for tool in definitions:
            self._tools[tool.tool_id] = tool

    def register_handler(
        self,
        tool_id: str,
        handler: Callable[[ToolCall, Dict[str, Any]], Coroutine[Any, Any, ToolResult]],
    ) -> None:
        if tool_id not in self._tools:
            raise AIAnalystException(
                AIErrorCode.AI_TOOL_NOT_FOUND,
                f"Cannot register handler for unknown tool '{tool_id}'.",
            )
        self._handlers[tool_id] = handler

    def get_tool(self, tool_id: str) -> ToolDefinition:
        if tool_id not in self._tools:
            raise AIAnalystException(
                AIErrorCode.AI_TOOL_NOT_FOUND,
                f"Tool '{tool_id}' is not a registered analytical tool.",
            )
        return self._tools[tool_id]

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def validate_permissions(self, tool_id: str, auto_confirm_proposals: bool = False) -> None:
        """Verifies tool permission policy. Mutating actions require explicit user approval."""
        tool = self.get_tool(tool_id)
        if tool.permission == ToolPermission.USER_CONFIRMATION_REQUIRED and not auto_confirm_proposals:
            raise AIAnalystException(
                AIErrorCode.AI_TOOL_PERMISSION_DENIED,
                f"Tool '{tool_id}' requires explicit user confirmation before execution.",
            )

    async def execute(
        self,
        tool_call: ToolCall,
        context: Dict[str, Any],
    ) -> ToolResult:
        tool_id = tool_call.tool_id
        tool = self.get_tool(tool_id)

        # Check required context fields
        for req in tool.required_context:
            if req not in context and req not in tool_call.arguments:
                raise AIAnalystException(
                    AIErrorCode.AI_TOOL_CALL_INVALID,
                    f"Tool '{tool_id}' requires '{req}' in context or arguments.",
                )

        # Check permissions
        self.validate_permissions(tool_id)

        if tool_id not in self._handlers:
            raise AIAnalystException(
                AIErrorCode.AI_TOOL_NOT_FOUND,
                f"No handler registered for tool '{tool_id}'.",
            )

        handler = self._handlers[tool_id]
        return await handler(tool_call, context)


tool_registry = ToolRegistry()
