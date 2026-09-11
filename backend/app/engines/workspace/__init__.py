"""
Phase 16 Workspace Domain Engine Package.
"""

from backend.app.engines.workspace.models import (
    ActivityRecord,
    ActivityType,
    Asset,
    AssetRelationship,
    AssetStatus,
    AssetType,
    BrokenReference,
    DependencyItem,
    DependencySummary,
    LineageEdge,
    LineageGraph,
    LineageNode,
    Project,
    ProjectHealth,
    ProjectStatus,
    RelationshipType,
    SearchRequest,
    SearchResponse,
    SearchResult,
    Workspace,
    WorkspaceStatus,
    slugify,
)
from backend.app.engines.workspace.repository import WorkspaceRepository
from backend.app.engines.workspace.dependency_analyzer import DependencyAnalyzer

workspace_repo = WorkspaceRepository()
dependency_analyzer = DependencyAnalyzer(workspace_repo)

__all__ = [
    "Workspace",
    "WorkspaceStatus",
    "Project",
    "ProjectStatus",
    "Asset",
    "AssetType",
    "AssetStatus",
    "AssetRelationship",
    "RelationshipType",
    "ActivityRecord",
    "ActivityType",
    "BrokenReference",
    "ProjectHealth",
    "DependencyItem",
    "DependencySummary",
    "LineageNode",
    "LineageEdge",
    "LineageGraph",
    "SearchRequest",
    "SearchResult",
    "SearchResponse",
    "slugify",
    "WorkspaceRepository",
    "DependencyAnalyzer",
    "workspace_repo",
    "dependency_analyzer",
]
