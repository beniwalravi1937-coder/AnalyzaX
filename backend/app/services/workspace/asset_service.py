"""
Asset Registry Application Service for Phase 16.
Provides centralized asset registration, favoriting, tagging, recent tracking,
deletion safeguards, and lineage resolution.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from backend.app.core.logging import logger
from backend.app.engines.workspace.models import (
    ActivityRecord,
    ActivityType,
    Asset,
    AssetCreateRequest,
    AssetRelationship,
    AssetStatus,
    AssetType,
    AssetUpdateRequest,
    DependencySummary,
    LineageGraph,
    RelationshipType,
)
from backend.app.engines.workspace.repository import WorkspaceRepository, workspace_repo
from backend.app.engines.workspace.dependency_analyzer import DependencyAnalyzer, dependency_analyzer
from backend.app.services.workspace.project_service import project_service


class AssetRegistryService:
    """
    Coordinates unified asset registration, dependency checks, and lineage navigation.
    """

    def __init__(
        self,
        repo: Optional[WorkspaceRepository] = None,
        analyzer: Optional[DependencyAnalyzer] = None,
    ):
        self._repo = repo or workspace_repo
        self._analyzer = analyzer or dependency_analyzer
        self._project_service = project_service

    def register_asset(self, req: AssetCreateRequest) -> Asset:
        # Validate project exists
        proj = self._project_service.get_project(req.project_id)
        if proj.workspace_id != req.workspace_id:
            raise HTTPException(
                status_code=400,
                detail=f"Project '{req.project_id}' does not belong to workspace '{req.workspace_id}'",
            )

        # Check if already registered
        existing = self._repo.get_asset_by_source(req.project_id, req.source_entity_id)
        if existing:
            # Update existing asset
            existing.name = req.name
            existing.description = req.description or existing.description
            existing.status = AssetStatus.ACTIVE
            if req.metadata:
                existing.metadata.update(req.metadata)
            if req.tags:
                existing.tags = list(set(existing.tags + req.tags))
            return self._repo.save_asset(existing)

        asset = Asset(
            asset_type=req.asset_type,
            project_id=req.project_id,
            workspace_id=req.workspace_id,
            source_entity_id=req.source_entity_id,
            name=req.name.strip(),
            description=req.description.strip() if req.description else None,
            status=AssetStatus.ACTIVE,
            metadata=req.metadata,
            tags=req.tags,
            source_version_reference=req.source_version_reference,
            provenance_reference=req.provenance_reference,
        )
        saved = self._repo.save_asset(asset)

        # Map activity
        act_map = {
            AssetType.DATASET: ActivityType.DATASET_CREATED,
            AssetType.DASHBOARD: ActivityType.DASHBOARD_CREATED,
            AssetType.REPORT: ActivityType.REPORT_CREATED,
            AssetType.VISUALIZATION: ActivityType.VISUALIZATION_CREATED,
            AssetType.QUERY: ActivityType.QUERY_SAVED,
            AssetType.STATISTICAL_ANALYSIS: ActivityType.STATISTICAL_ANALYSIS_CREATED,
            AssetType.ML_EXPERIMENT: ActivityType.ML_EXPERIMENT_CREATED,
            AssetType.FORECAST_EXPERIMENT: ActivityType.FORECAST_CREATED,
            AssetType.AI_SESSION: ActivityType.AI_SESSION_CREATED,
            AssetType.EXPORT: ActivityType.EXPORT_COMPLETED,
        }
        activity_type = act_map.get(saved.asset_type, ActivityType.ASSET_TAGGED)

        self._repo.record_activity(
            ActivityRecord(
                workspace_id=saved.workspace_id,
                project_id=saved.project_id,
                asset_id=saved.asset_id,
                activity_type=activity_type,
                metadata={"name": saved.name, "asset_type": saved.asset_type.value},
            )
        )
        return saved

    def get_asset(self, asset_id: str) -> Asset:
        asset = self._repo.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found")
        return asset

    def record_access(self, asset_id: str) -> Asset:
        """Records user access for recent assets view."""
        asset = self.get_asset(asset_id)
        asset.last_accessed_at = datetime.now(timezone.utc).isoformat()
        return self._repo.save_asset(asset)

    def list_assets(
        self,
        project_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        asset_type: Optional[str] = None,
        status: Optional[AssetStatus] = None,
        is_favorite: Optional[bool] = None,
    ) -> List[Asset]:
        return self._repo.list_assets(
            project_id=project_id,
            workspace_id=workspace_id,
            asset_type=asset_type,
            status=status,
            is_favorite=is_favorite,
        )

    def update_asset(self, asset_id: str, req: AssetUpdateRequest) -> Asset:
        asset = self.get_asset(asset_id)
        if req.name is not None:
            asset.name = req.name.strip()
        if req.description is not None:
            asset.description = req.description.strip() if req.description else None
        if req.tags is not None:
            asset.tags = req.tags
        if req.metadata is not None:
            asset.metadata.update(req.metadata)

        return self._repo.save_asset(asset)

    def set_favorite(self, asset_id: str, is_favorite: bool) -> Asset:
        asset = self.get_asset(asset_id)
        asset.is_favorite = is_favorite
        saved = self._repo.save_asset(asset)

        self._repo.record_activity(
            ActivityRecord(
                workspace_id=saved.workspace_id,
                project_id=saved.project_id,
                asset_id=saved.asset_id,
                activity_type=ActivityType.ASSET_FAVORITED if is_favorite else ActivityType.ASSET_UNFAVORITED,
                metadata={"name": saved.name, "is_favorite": is_favorite},
            )
        )
        return saved

    def tag_asset(self, asset_id: str, tags: List[str]) -> Asset:
        asset = self.get_asset(asset_id)
        asset.tags = tags
        saved = self._repo.save_asset(asset)

        self._repo.record_activity(
            ActivityRecord(
                workspace_id=saved.workspace_id,
                project_id=saved.project_id,
                asset_id=saved.asset_id,
                activity_type=ActivityType.ASSET_TAGGED,
                metadata={"tags": saved.tags},
            )
        )
        return saved

    def archive_asset(self, asset_id: str) -> Asset:
        asset = self.get_asset(asset_id)
        asset.status = AssetStatus.ARCHIVED
        asset.archived_at = datetime.now(timezone.utc).isoformat()
        saved = self._repo.save_asset(asset)

        self._repo.record_activity(
            ActivityRecord(
                workspace_id=saved.workspace_id,
                project_id=saved.project_id,
                asset_id=saved.asset_id,
                activity_type=ActivityType.ASSET_ARCHIVED,
                metadata={"name": saved.name},
            )
        )
        return saved

    def restore_asset(self, asset_id: str) -> Asset:
        asset = self.get_asset(asset_id)
        asset.status = AssetStatus.ACTIVE
        asset.archived_at = None
        saved = self._repo.save_asset(asset)

        self._repo.record_activity(
            ActivityRecord(
                workspace_id=saved.workspace_id,
                project_id=saved.project_id,
                asset_id=saved.asset_id,
                activity_type=ActivityType.ASSET_RESTORED,
                metadata={"name": saved.name},
            )
        )
        return saved

    def delete_asset(self, asset_id: str, force: bool = False) -> bool:
        """
        Safely deletes an asset after evaluating dependencies.
        """
        asset = self.get_asset(asset_id)
        summary = self._analyzer.get_dependencies(asset_id)

        if not summary.can_safely_delete and not force:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete '{asset.name}' because it has active dependents: {'; '.join(summary.warnings)}. Use Archive instead, or specify force=True.",
            )

        # Soft delete in asset registry
        asset.status = AssetStatus.DELETED
        self._repo.save_asset(asset)
        self._repo.delete_relationships_for_asset(asset_id)

        self._repo.record_activity(
            ActivityRecord(
                workspace_id=asset.workspace_id,
                project_id=asset.project_id,
                asset_id=asset.asset_id,
                activity_type=ActivityType.ASSET_DELETED,
                metadata={"name": asset.name},
            )
        )
        return True

    # ─────────────────────────────────────────────────────────────
    # Relationships & Lineage
    # ─────────────────────────────────────────────────────────────

    def add_relationship(
        self,
        source_asset_id: str,
        target_asset_id: str,
        rel_type: RelationshipType,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AssetRelationship:
        # Validate existence
        self.get_asset(source_asset_id)
        self.get_asset(target_asset_id)

        rel = AssetRelationship(
            source_asset_id=source_asset_id,
            target_asset_id=target_asset_id,
            relationship_type=rel_type,
            metadata=metadata or {},
        )
        return self._repo.save_relationship(rel)

    create_relationship = add_relationship


    def get_dependencies(self, asset_id: str) -> DependencySummary:
        return self._analyzer.get_dependencies(asset_id)

    def get_lineage(self, asset_id: str, user_id: Optional[str] = None) -> LineageGraph:
        return self._analyzer.build_lineage_graph(asset_id, user_id=user_id)


asset_service = AssetRegistryService()
