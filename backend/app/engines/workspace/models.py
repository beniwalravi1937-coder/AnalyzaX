"""
Domain models for Phase 16: Workspace, Project & Asset Organization Layer.
Defines entities, enums, relationship graphs, activity records, and search contracts.
"""

from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class WorkspaceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class ProjectStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class AssetType(str, Enum):
    DATASET = "DATASET"
    DATASET_VERSION = "DATASET_VERSION"
    VISUALIZATION = "VISUALIZATION"
    QUERY = "QUERY"
    STATISTICAL_ANALYSIS = "STATISTICAL_ANALYSIS"
    ML_EXPERIMENT = "ML_EXPERIMENT"
    ML_RESULT = "ML_RESULT"
    FORECAST_EXPERIMENT = "FORECAST_EXPERIMENT"
    FORECAST_RESULT = "FORECAST_RESULT"
    AI_SESSION = "AI_SESSION"
    DASHBOARD = "DASHBOARD"
    REPORT = "REPORT"
    EXPORT = "EXPORT"


class AssetStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class RelationshipType(str, Enum):
    DERIVED_FROM = "DERIVED_FROM"
    USES = "USES"
    CONTAINS = "CONTAINS"
    REFERENCES = "REFERENCES"
    GENERATED_FROM = "GENERATED_FROM"
    VISUALIZES = "VISUALIZES"
    SUMMARIZES = "SUMMARIZES"
    EXPORTED_FROM = "EXPORTED_FROM"
    DEPENDS_ON = "DEPENDS_ON"


class ActivityType(str, Enum):
    WORKSPACE_CREATED = "WORKSPACE_CREATED"
    WORKSPACE_UPDATED = "WORKSPACE_UPDATED"
    WORKSPACE_ARCHIVED = "WORKSPACE_ARCHIVED"
    WORKSPACE_RESTORED = "WORKSPACE_RESTORED"

    PROJECT_CREATED = "PROJECT_CREATED"
    PROJECT_UPDATED = "PROJECT_UPDATED"
    PROJECT_ARCHIVED = "PROJECT_ARCHIVED"
    PROJECT_RESTORED = "PROJECT_RESTORED"
    PROJECT_DUPLICATED = "PROJECT_DUPLICATED"
    PROJECT_DELETED = "PROJECT_DELETED"

    DATASET_CREATED = "DATASET_CREATED"
    DATASET_ARCHIVED = "DATASET_ARCHIVED"
    DATASET_RESTORED = "DATASET_RESTORED"
    DATASET_DELETED = "DATASET_DELETED"
    DATASET_VERSION_CREATED = "DATASET_VERSION_CREATED"

    DASHBOARD_CREATED = "DASHBOARD_CREATED"
    DASHBOARD_UPDATED = "DASHBOARD_UPDATED"
    DASHBOARD_DELETED = "DASHBOARD_DELETED"

    REPORT_CREATED = "REPORT_CREATED"
    REPORT_EXPORTED = "REPORT_EXPORTED"

    VISUALIZATION_CREATED = "VISUALIZATION_CREATED"
    QUERY_SAVED = "QUERY_SAVED"
    STATISTICAL_ANALYSIS_CREATED = "STATISTICAL_ANALYSIS_CREATED"
    ML_EXPERIMENT_CREATED = "ML_EXPERIMENT_CREATED"
    FORECAST_CREATED = "FORECAST_CREATED"
    AI_SESSION_CREATED = "AI_SESSION_CREATED"
    EXPORT_COMPLETED = "EXPORT_COMPLETED"

    ASSET_CREATED = "ASSET_CREATED"
    ASSET_UPDATED = "ASSET_UPDATED"
    ASSET_FAVORITED = "ASSET_FAVORITED"
    ASSET_UNFAVORITED = "ASSET_UNFAVORITED"
    ASSET_ARCHIVED = "ASSET_ARCHIVED"
    ASSET_RESTORED = "ASSET_RESTORED"
    ASSET_TAGGED = "ASSET_TAGGED"
    ASSET_DELETED = "ASSET_DELETED"


# ─────────────────────────────────────────────────────────────
# Utility Slug Generator
# ─────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    """Generates a clean URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-") or "item"


# ─────────────────────────────────────────────────────────────
# Workspace Models
# ─────────────────────────────────────────────────────────────

class Workspace(BaseModel):
    workspace_id: str = Field(default_factory=lambda: f"ws_{uuid.uuid4().hex[:10]}")
    name: str
    slug: str
    description: Optional[str] = None
    status: WorkspaceStatus = WorkspaceStatus.ACTIVE
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    archived_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    configuration_version: int = 1


class WorkspaceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkspaceUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = None


# ─────────────────────────────────────────────────────────────
# Project Models
# ─────────────────────────────────────────────────────────────

class Project(BaseModel):
    project_id: str = Field(default_factory=lambda: f"proj_{uuid.uuid4().hex[:10]}")
    workspace_id: str
    name: str
    slug: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    icon: Optional[str] = "📁"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    archived_at: Optional[str] = None
    last_activity_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)
    configuration_version: int = 1


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = Field("📁", max_length=10)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = Field(None, max_length=10)
    metadata: Optional[Dict[str, Any]] = None


class ProjectDuplicateRequest(BaseModel):
    new_name: str = Field(..., min_length=1, max_length=100)
    copy_dashboards: bool = True
    copy_reports: bool = True
    copy_saved_queries: bool = True


# ─────────────────────────────────────────────────────────────
# Asset Registry Models
# ─────────────────────────────────────────────────────────────

class Asset(BaseModel):
    asset_id: str = Field(default_factory=lambda: f"ast_{uuid.uuid4().hex[:12]}")
    asset_type: AssetType
    project_id: str
    workspace_id: str
    source_entity_id: str
    name: str
    description: Optional[str] = None
    status: AssetStatus = AssetStatus.ACTIVE
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_accessed_at: Optional[str] = None
    archived_at: Optional[str] = None
    is_favorite: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    source_version_reference: Optional[str] = None
    provenance_reference: Optional[Dict[str, Any]] = None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: List[str]) -> List[str]:
        cleaned = []
        for tag in v:
            t = re.sub(r"[^\w\s-]", "", tag).strip().lower()
            if t and t not in cleaned:
                cleaned.append(t[:30])
        return cleaned[:15]


class AssetCreateRequest(BaseModel):
    asset_type: AssetType
    project_id: str
    workspace_id: str
    source_entity_id: str
    name: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    source_version_reference: Optional[str] = None
    provenance_reference: Optional[Dict[str, Any]] = None


class AssetUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class AssetTagRequest(BaseModel):
    tags: List[str]


# ─────────────────────────────────────────────────────────────
# Relationships & Lineage
# ─────────────────────────────────────────────────────────────

class AssetRelationship(BaseModel):
    relationship_id: str = Field(default_factory=lambda: f"rel_{uuid.uuid4().hex[:12]}")
    source_asset_id: str
    target_asset_id: str
    relationship_type: RelationshipType
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssetRelationshipCreateRequest(BaseModel):
    source_asset_id: str
    target_asset_id: str
    relationship_type: RelationshipType
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DependencyItem(BaseModel):
    asset_id: str
    name: str
    asset_type: AssetType
    relationship_type: RelationshipType


class DependencySummary(BaseModel):
    asset_id: str
    asset_name: str
    asset_type: AssetType
    dependent_assets: List[DependencyItem] = Field(default_factory=list)
    downstream_dependencies: List[DependencyItem] = Field(default_factory=list)
    upstream_assets: List[DependencyItem] = Field(default_factory=list)
    upstream_dependencies: List[DependencyItem] = Field(default_factory=list)
    can_safely_archive: bool
    can_safely_delete: bool
    warnings: List[str] = Field(default_factory=list)


class LineageNode(BaseModel):
    id: str
    label: str
    type: str
    status: str
    is_stale: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LineageEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str


class LineageGraph(BaseModel):
    root_asset_id: str
    nodes: List[LineageNode]
    edges: List[LineageEdge]


# ─────────────────────────────────────────────────────────────
# Activity Logging
# ─────────────────────────────────────────────────────────────

class ActivityRecord(BaseModel):
    activity_id: str = Field(default_factory=lambda: f"act_{uuid.uuid4().hex[:12]}")
    workspace_id: str
    project_id: str
    asset_id: Optional[str] = None
    activity_type: ActivityType
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────
# Project Health
# ─────────────────────────────────────────────────────────────

class BrokenReference(BaseModel):
    source_asset_id: str
    source_name: str
    source_type: AssetType
    target_asset_id: Optional[str] = None
    target_entity_id: Optional[str] = None
    reason: str


class ProjectHealth(BaseModel):
    project_id: str
    workspace_id: str
    status: str = "HEALTHY"  # HEALTHY, WARNING, CRITICAL
    datasets_ready: int = 0
    datasets_failed: int = 0
    archived_datasets: int = 0
    total_assets: int = 0
    broken_references: List[BrokenReference] = Field(default_factory=list)
    failed_jobs_count: int = 0
    last_evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ─────────────────────────────────────────────────────────────
# Search Contracts
# ─────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field("", max_length=200)
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    asset_types: Optional[List[AssetType]] = None
    is_favorite: Optional[bool] = None
    status: Optional[AssetStatus] = None
    tags: Optional[List[str]] = None
    sort_by: str = "relevance"
    sort_order: str = "desc"
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class SearchResult(BaseModel):
    asset_id: str
    asset_type: AssetType
    name: str
    description: Optional[str] = None
    project_id: str
    project_name: Optional[str] = None
    workspace_id: str
    status: AssetStatus
    is_favorite: bool
    tags: List[str]
    created_at: str
    updated_at: str
    navigation_url: str
    source_entity_id: str


class SearchResponse(BaseModel):
    query: str
    total: int
    page: int
    page_size: int
    results: List[SearchResult]


# ─────────────────────────────────────────────────────────────
# Dataset Version Comparison Result
# ─────────────────────────────────────────────────────────────

class ColumnSchemaDiff(BaseModel):
    name: str
    change: str  # "ADDED", "REMOVED", "TYPE_CHANGED", "UNCHANGED"
    old_dtype: Optional[str] = None
    new_dtype: Optional[str] = None


class DatasetVersionComparisonResult(BaseModel):
    dataset_id: str
    version_a_id: str
    version_b_id: str
    row_count_a: Optional[int] = None
    row_count_b: Optional[int] = None
    row_count_delta: Optional[int] = None
    column_count_a: Optional[int] = None
    column_count_b: Optional[int] = None
    schema_diff: List[ColumnSchemaDiff] = Field(default_factory=list)
    quality_score_a: Optional[float] = None
    quality_score_b: Optional[float] = None
    quality_score_delta: Optional[float] = None
    comparison_available: bool = True
    notes: List[str] = Field(default_factory=list)
