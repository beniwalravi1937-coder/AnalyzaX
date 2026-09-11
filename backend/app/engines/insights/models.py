"""
AnalyzaX — Phase 25: Proactive Insight Intelligence Models.
Structured models representing automated analytical signals, multi-criteria importance scores,
and evidence graphs linking to deterministic engine results.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class InsightType(str, Enum):
    TREND_CHANGE = "TREND_CHANGE"
    ANOMALY = "ANOMALY"
    SEGMENT_DIFFERENCE = "SEGMENT_DIFFERENCE"
    CORRELATION = "CORRELATION"
    DATA_QUALITY = "DATA_QUALITY"
    FORECAST_DEVIATION = "FORECAST_DEVIATION"
    STATISTICAL_SIGNAL = "STATISTICAL_SIGNAL"
    MODEL_SIGNAL = "MODEL_SIGNAL"
    CONCENTRATION = "CONCENTRATION"
    DISTRIBUTION_SHIFT = "DISTRIBUTION_SHIFT"
    TIME_SERIES_CHANGE = "TIME_SERIES_CHANGE"


class InsightSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    WARNING = "WARNING"
    MEDIUM = "MEDIUM"
    INFO = "INFO"
    LOW = "LOW"


class InsightStatus(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    SUPERSEDED = "SUPERSEDED"
    DISMISSED = "DISMISSED"


class InsightConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class InsightEvidence(BaseModel):
    """Concrete proof element linking an insight back to a deterministic engine result."""
    evidence_id: str
    evidence_type: str  # 'statistical_test', 'sql_query', 'quality_metric', 'eda_correlation', 'forecast', 'profile'
    source_entity_id: Optional[str] = None
    description: str
    metrics: Dict[str, Any] = Field(default_factory=dict)  # e.g. {'p_value': 0.001, 'correlation': 0.88, 'delta_pct': -14.2}
    chart_spec: Optional[Dict[str, Any]] = None
    sql_executed: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EvidenceGraphNode(BaseModel):
    id: str
    label: str
    node_type: str  # 'insight', 'dataset_version', 'statistical_result', 'chart', 'sql_query', 'forecast'
    properties: Dict[str, Any] = Field(default_factory=dict)


class EvidenceGraphEdge(BaseModel):
    source: str
    target: str
    relation: str  # 'GROUNDED_BY', 'DERIVED_FROM', 'VISUALIZES', 'EVALUATES'


class EvidenceGraph(BaseModel):
    """Lightweight graph connecting an insight to all its underlying evidence objects."""
    nodes: List[EvidenceGraphNode] = Field(default_factory=list)
    edges: List[EvidenceGraphEdge] = Field(default_factory=list)


class RecommendedAction(BaseModel):
    """Contextual next-step action triggered by an insight."""
    action_id: str
    title: str
    description: str
    action_type: str  # 'run_eda', 'run_statistical_test', 'create_chart', 'propose_cleaning', 'forecast'
    tool_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class Insight(BaseModel):
    """Governed proactive insight produced by deterministic discovery + AI synthesis."""
    insight_id: str = Field(..., description="Unique insight identifier (e.g. ins_12345)")
    workspace_id: str
    project_id: Optional[str] = None
    dataset_id: str
    dataset_version_id: str
    insight_type: InsightType
    title: str
    summary: str
    severity: InsightSeverity
    importance_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Deterministic analytical priority score (0-100)")
    confidence: InsightConfidence = Field(default=InsightConfidence.HIGH)
    affected_columns: List[str] = Field(default_factory=list)
    affected_dimensions: List[str] = Field(default_factory=list)
    evidence: List[InsightEvidence] = Field(default_factory=list)
    evidence_graph: Optional[EvidenceGraph] = None
    explanation: Optional[str] = None
    recommended_actions: List[RecommendedAction] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    status: InsightStatus = Field(default=InsightStatus.CURRENT)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

