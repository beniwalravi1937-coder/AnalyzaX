"""
Project Application Service for Phase 16.
Coordinates project lifecycle, safe duplication, health checks, and manifest export.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from backend.app.core.logging import logger
from backend.app.engines.workspace.models import (
    ActivityRecord,
    ActivityType,
    Asset,
    AssetStatus,
    AssetType,
    Project,
    ProjectCreateRequest,
    ProjectDuplicateRequest,
    ProjectHealth,
    ProjectStatus,
    ProjectUpdateRequest,
    RelationshipType,
    slugify,
)
from backend.app.engines.workspace.repository import WorkspaceRepository, workspace_repo
from backend.app.engines.workspace.dependency_analyzer import DependencyAnalyzer, dependency_analyzer
from backend.app.services.workspace.workspace_service import workspace_service


class ProjectService:
    """
    Coordinates project operations, safe duplication, and health audits.
    """

    def __init__(
        self,
        repo: Optional[WorkspaceRepository] = None,
        analyzer: Optional[DependencyAnalyzer] = None,
    ):
        self._repo = repo or workspace_repo
        self._analyzer = analyzer or dependency_analyzer
        self._workspace_service = workspace_service

    def get_or_create_default_project(self, workspace_id: Optional[str] = None) -> Project:
        """
        Ensures a default project exists within the workspace.
        """
        if not workspace_id:
            ws = self._workspace_service.get_or_create_default_workspace()
            workspace_id = ws.workspace_id
        else:
            self._workspace_service.get_workspace(workspace_id)

        existing = self._repo.list_projects(workspace_id=workspace_id)
        if existing:
            return existing[0]

        default_proj = Project(
            project_id="proj_default",
            workspace_id=workspace_id,
            name="Default Project",
            slug="default-project",
            description="Primary project for organizing analytical workflows and data assets.",
            status=ProjectStatus.ACTIVE,
            icon="folder",
        )
        self._repo.save_project(default_proj)
        self._repo.record_activity(
            ActivityRecord(
                workspace_id=workspace_id,
                project_id=default_proj.project_id,
                activity_type=ActivityType.PROJECT_CREATED,
                metadata={"name": default_proj.name, "is_default": True},
            )
        )
        logger.info(f"Initialized Default Project (proj_default) in workspace {workspace_id}")
        return default_proj

    def create_project(self, workspace_id: str, req: ProjectCreateRequest) -> Project:
        # Validate workspace
        self._workspace_service.get_workspace(workspace_id)

        # Enforce workspace project count limit under plan
        from backend.app.services.usage import quota_service
        from backend.app.engines.usage.metrics import UsageMetrics
        quota_service.enforce_quota(
            workspace_id=workspace_id,
            metric_key=UsageMetrics.PROJECT_COUNT.key,
            quantity=1.0,
        )

        base_slug = slugify(req.name)
        slug = base_slug
        counter = 1
        while self._repo.get_project_by_slug(workspace_id, slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        proj = Project(
            workspace_id=workspace_id,
            name=req.name.strip(),
            slug=slug,
            description=req.description.strip() if req.description else None,
            icon=req.icon or "📁",
            status=ProjectStatus.ACTIVE,
            metadata=req.metadata,
        )
        saved = self._repo.save_project(proj)

        self._repo.record_activity(
            ActivityRecord(
                workspace_id=workspace_id,
                project_id=saved.project_id,
                activity_type=ActivityType.PROJECT_CREATED,
                metadata={"name": saved.name, "slug": saved.slug},
            )
        )
        return saved

    def get_project(self, project_id: str) -> Project:
        proj = self._repo.get_project(project_id)
        if not proj:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        return proj

    def list_projects(
        self,
        workspace_id: Optional[str] = None,
        status: Optional[ProjectStatus] = None,
    ) -> List[Project]:
        projects = self._repo.list_projects(workspace_id=workspace_id, status=status)
        if not projects and workspace_id and not status:
            return [self.get_or_create_default_project(workspace_id)]
        return projects

    def update_project(self, project_id: str, req: ProjectUpdateRequest) -> Project:
        proj = self.get_project(project_id)
        if req.name is not None:
            proj.name = req.name.strip()
            new_slug = slugify(proj.name)
            existing = self._repo.get_project_by_slug(proj.workspace_id, new_slug)
            if existing and existing.project_id != proj.project_id:
                new_slug = f"{new_slug}-{proj.project_id[-4:]}"
            proj.slug = new_slug

        if req.description is not None:
            proj.description = req.description.strip() if req.description else None

        if req.icon is not None:
            proj.icon = req.icon

        if req.metadata is not None:
            proj.metadata.update(req.metadata)

        proj.updated_at = datetime.now(timezone.utc).isoformat()
        saved = self._repo.save_project(proj)

        self._repo.record_activity(
            ActivityRecord(
                workspace_id=saved.workspace_id,
                project_id=saved.project_id,
                activity_type=ActivityType.PROJECT_UPDATED,
                metadata={"name": saved.name},
            )
        )
        return saved

    def archive_project(self, project_id: str) -> Project:
        proj = self.get_project(project_id)
        proj.status = ProjectStatus.ARCHIVED
        proj.archived_at = datetime.now(timezone.utc).isoformat()
        saved = self._repo.save_project(proj)

        self._repo.record_activity(
            ActivityRecord(
                workspace_id=saved.workspace_id,
                project_id=saved.project_id,
                activity_type=ActivityType.PROJECT_ARCHIVED,
                metadata={"name": saved.name},
            )
        )
        return saved

    def restore_project(self, project_id: str) -> Project:
        proj = self.get_project(project_id)
        proj.status = ProjectStatus.ACTIVE
        proj.archived_at = None
        saved = self._repo.save_project(proj)

        self._repo.record_activity(
            ActivityRecord(
                workspace_id=saved.workspace_id,
                project_id=saved.project_id,
                activity_type=ActivityType.PROJECT_RESTORED,
                metadata={"name": saved.name},
            )
        )
        return saved

    def delete_project(self, project_id: str) -> bool:
        proj = self.get_project(project_id)
        # Check assets inside
        assets = self._repo.list_assets(project_id=project_id)
        active_assets = [a for a in assets if a.status != AssetStatus.DELETED]
        if active_assets:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete project '{proj.name}' containing {len(active_assets)} active asset(s). Archive the project or remove assets first.",
            )

        deleted = self._repo.delete_project(project_id)
        if deleted:
            self._repo.record_activity(
                ActivityRecord(
                    workspace_id=proj.workspace_id,
                    project_id=project_id,
                    activity_type=ActivityType.PROJECT_DELETED,
                    metadata={"name": proj.name},
                )
            )
        return deleted

    def duplicate_project(self, project_id: str, req: ProjectDuplicateRequest) -> Project:
        """
        Safe duplication of project definitions (dashboards, reports, saved queries)
        without copying raw binary datasets or model binaries.
        """
        source = self.get_project(project_id)
        new_proj = self.create_project(
            workspace_id=source.workspace_id,
            req=ProjectCreateRequest(
                name=req.new_name,
                description=f"Duplicate of {source.name}. {source.description or ''}".strip(),
                icon=source.icon,
                metadata={"duplicated_from_project_id": source.project_id},
            ),
        )

        # Copy non-dataset assets as references/clones
        source_assets = self._repo.list_assets(project_id=project_id)
        for sa in source_assets:
            if sa.status == AssetStatus.DELETED:
                continue

            # Skip datasets & heavy binary models (link by reference instead)
            if sa.asset_type in (AssetType.DATASET, AssetType.DATASET_VERSION):
                # We do not duplicate raw datasets; reference the existing dataset
                continue

            if sa.asset_type == AssetType.DASHBOARD and not req.copy_dashboards:
                continue
            if sa.asset_type == AssetType.REPORT and not req.copy_reports:
                continue
            if sa.asset_type == AssetType.QUERY and not req.copy_saved_queries:
                continue

            # Clone asset metadata into the new project
            cloned_asset = Asset(
                asset_type=sa.asset_type,
                project_id=new_proj.project_id,
                workspace_id=new_proj.workspace_id,
                source_entity_id=sa.source_entity_id,
                name=f"{sa.name} (Copy)",
                description=sa.description,
                status=AssetStatus.ACTIVE,
                is_favorite=False,
                tags=list(sa.tags),
                metadata=dict(sa.metadata),
                source_version_reference=sa.source_version_reference,
            )
            self._repo.save_asset(cloned_asset)

        self._repo.record_activity(
            ActivityRecord(
                workspace_id=source.workspace_id,
                project_id=new_proj.project_id,
                activity_type=ActivityType.PROJECT_DUPLICATED,
                metadata={
                    "source_project_id": source.project_id,
                    "new_project_name": new_proj.name,
                },
            )
        )
        return new_proj

    def get_project_health(self, project_id: str) -> ProjectHealth:
        return self._analyzer.evaluate_project_health(project_id)

    def export_project_manifest(self, project_id: str) -> Dict[str, Any]:
        """
        Exports a structured JSON configuration manifest of the project.
        """
        proj = self.get_project(project_id)
        assets = self._repo.list_assets(project_id=project_id)
        asset_ids = {a.asset_id for a in assets}

        rels = []
        for a in assets:
            out_rels = self._repo.list_relationships(source_asset_id=a.asset_id)
            for r in out_rels:
                if r.target_asset_id in asset_ids:
                    rels.append(r.model_dump())

        return {
            "manifest_version": "1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "project": proj.model_dump(),
            "assets": [a.model_dump() for a in assets if a.status != AssetStatus.DELETED],
            "relationships": rels,
        }


project_service = ProjectService()
