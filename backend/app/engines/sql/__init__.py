"""
AnalyzaX — Phase 8: SQL Analytics Engine Package
"""

from backend.app.engines.sql.chart_advisor import SQLChartAdvisor
from backend.app.engines.sql.executor import SQLExecutor, query_registry
from backend.app.engines.sql.hasher import SQLHasher
from backend.app.engines.sql.history import query_history_repo
from backend.app.engines.sql.introspection import SchemaIntrospector
from backend.app.engines.sql.models import (
    QueryHistoryEntry,
    QueryStatus,
    SavedQuery,
    SavedQueryCreateRequest,
    SavedQueryUpdateRequest,
    SchemaColumnInfo,
    SchemaTableInfo,
    SQLColumnDescriptor,
    SQLExplainResult,
    SQLQueryRequest,
    SQLQueryResponse,
    SQLStatementType,
    SQLTemplate,
    SQLValidationError,
    SQLValidationResult,
    SQLValidationWarning,
    VisualizationRequest,
)
from backend.app.engines.sql.parser import SQLParsedAst, SQLParser
from backend.app.engines.sql.saved_queries import saved_queries_repo
from backend.app.engines.sql.templates import SQLTemplateGenerator
from backend.app.engines.sql.validator import SQLValidator

__all__ = [
    "SQLChartAdvisor",
    "SQLExecutor",
    "query_registry",
    "SQLHasher",
    "query_history_repo",
    "SchemaIntrospector",
    "QueryHistoryEntry",
    "QueryStatus",
    "SavedQuery",
    "SavedQueryCreateRequest",
    "SavedQueryUpdateRequest",
    "SchemaColumnInfo",
    "SchemaTableInfo",
    "SQLColumnDescriptor",
    "SQLExplainResult",
    "SQLQueryRequest",
    "SQLQueryResponse",
    "SQLStatementType",
    "SQLTemplate",
    "SQLValidationError",
    "SQLValidationResult",
    "SQLValidationWarning",
    "VisualizationRequest",
    "SQLParsedAst",
    "SQLParser",
    "saved_queries_repo",
    "SQLTemplateGenerator",
    "SQLValidator",
]
