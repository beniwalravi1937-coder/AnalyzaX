"""
AnalyzaX — Phase 8: SQL Domain Models
Defines all strongly-typed schemas for SQL query requests, execution results,
AST validation, schema introspection, history entries, and saved queries.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.engines.eda.models import ChartSpec


class QueryStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"


class SQLStatementType(str, Enum):
    SELECT = "SELECT"
    EXPLAIN = "EXPLAIN"
    WITH = "WITH"
    UNKNOWN = "UNKNOWN"


class SQLColumnDescriptor(BaseModel):
    name: str
    physical_type: str
    semantic_type: str = "unknown"
    nullable: bool = True


class SQLQueryRequest(BaseModel):
    dataset_id: str
    workspace_id: Optional[str] = None
    version_id: Optional[str] = None
    sql: str
    max_rows: int = Field(default=10000, ge=1, le=50000)
    timeout_seconds: float = Field(default=30.0, ge=1.0, le=120.0)
    use_cache: bool = True


class SQLQueryResponse(BaseModel):
    query_id: str
    dataset_id: str
    version_id: str
    status: QueryStatus
    columns: List[SQLColumnDescriptor] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    total_rows_estimate: Optional[int] = None
    scanned_rows: Optional[int] = None
    execution_time_ms: float = 0.0
    is_truncated: bool = False
    query_hash: str = ""
    cached: bool = False
    error_message: Optional[str] = None
    suggested_charts: List[ChartSpec] = Field(default_factory=list)


class SQLValidationError(BaseModel):
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    error_code: str = "SYNTAX_ERROR"


class SQLValidationWarning(BaseModel):
    message: str
    warning_code: str
    suggestion: Optional[str] = None


class SQLValidationResult(BaseModel):
    is_valid: bool
    statement_type: SQLStatementType = SQLStatementType.UNKNOWN
    tables: List[str] = Field(default_factory=list)
    columns: List[str] = Field(default_factory=list)
    errors: List[SQLValidationError] = Field(default_factory=list)
    warnings: List[SQLValidationWarning] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class SQLExplainResult(BaseModel):
    query_id: str
    dataset_id: str
    version_id: str
    plan_text: str
    plan_tree: Optional[Dict[str, Any]] = None
    estimated_cardinality: Optional[int] = None
    execution_time_ms: float = 0.0


class QueryHistoryEntry(BaseModel):
    query_id: str
    dataset_id: str
    version_id: str
    query_text: str
    query_hash: str
    status: QueryStatus
    execution_time_ms: float
    row_count: int
    error_message: Optional[str] = None
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class SavedQuery(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    dataset_id: str
    version_scope: str = "active"  # "active" or explicit version_id e.g. "v1"
    sql: str
    tags: List[str] = Field(default_factory=list)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class SavedQueryCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    dataset_id: str
    version_scope: str = "active"
    sql: str
    tags: List[str] = Field(default_factory=list)


class SavedQueryUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    version_scope: Optional[str] = None
    sql: Optional[str] = None
    tags: Optional[List[str]] = None


class SchemaColumnInfo(BaseModel):
    name: str
    physical_type: str
    semantic_type: str = "unknown"
    nullable: bool = True
    cardinality: Optional[int] = None
    sample_values: List[Any] = Field(default_factory=list)


class SchemaTableInfo(BaseModel):
    table_name: str
    table_alias: str
    dataset_id: str
    version_id: str
    row_count: int
    column_count: int
    columns: List[SchemaColumnInfo] = Field(default_factory=list)


class SQLTemplate(BaseModel):
    id: str
    title: str
    description: str
    category: str
    sql: str


class VisualizationRequest(BaseModel):
    dataset_id: str
    version_id: str
    columns: List[SQLColumnDescriptor]
    rows: List[Dict[str, Any]]
    chart_type: Optional[str] = None
    x_field: Optional[str] = None
    y_field: Optional[str] = None
    color_field: Optional[str] = None
