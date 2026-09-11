"""
Workspace Application Service for Phase 16.
Manages workspace lifecycle, slug collisions, archiving, and restoration.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException

from backend.app.core.logging import logger
from backend.app.engines.workspace.models import (
    ActivityRecord,
    ActivityType,
    Workspace,
    WorkspaceCreateRequest,
    WorkspaceStatus,
    WorkspaceUpdateRequest,
    slugify,
)
from backend.app.engines.workspace.repository import WorkspaceRepository, workspace_repo


class WorkspaceService:
    """
    Coordinates workspace lifecycle operations.
    """

    def __init__(self, repo: Optional[WorkspaceRepository] = None):
        self._repo = repo or workspace_repo

    def get_or_create_default_workspace(self) -> Workspace:
        """
        Ensures a default workspace exists for backward compatibility.
        """
        existing = self._repo.list_workspaces()
        if existing:
            return existing[0]

        default_ws = Workspace(
            workspace_id="ws_default",
            name="Default Workspace",
            slug="default-workspace",
            description="Primary workspace for analytical assets and projects.",
            status=WorkspaceStatus.ACTIVE,
        )
        self._repo.save_workspace(default_ws)
        self._repo.record_activity(
            ActivityRecord(
                workspace_id=default_ws.workspace_id,
                project_id="",
                activity_type=ActivityType.WORKSPACE_CREATED,
                metadata={"name": default_ws.name, "is_default": True},
            )
        )
        logger.info("Initialized Default Workspace (ws_default)")
        return default_ws

    def create_workspace(self, req: WorkspaceCreateRequest) -> Workspace:
        base_slug = slugify(req.name)
        slug = base_slug
        counter = 1
        while self._repo.get_workspace_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        ws = Workspace(
            name=req.name.strip(),
            slug=slug,
            description=req.description.strip() if req.description else None,
            status=WorkspaceStatus.ACTIVE,
            metadata=req.metadata,
        )
        saved = self._repo.save_workspace(ws)

        self._repo.record_activity(
            ActivityRecord(
                workspace_id=saved.workspace_id,
                project_id="",
                activity_type=ActivityType.WORKSPACE_CREATED,
                metadata={"name": saved.name, "slug": saved.slug},
            )
        )
        return saved

    def get_workspace(self, workspace_id: str) -> Workspace:
        ws = self._repo.get_workspace(workspace_id)
        if not ws:
            raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' not found")
        return ws

    def list_workspaces(self, status: Optional[WorkspaceStatus] = None) -> List[Workspace]:
        # Ensure default exists if list is empty
        workspaces = self._repo.list_workspaces(status=status)
        if not workspaces and not status:
            return [self.get_or_create_default_workspace()]
        return workspaces

    def update_workspace(self, workspace_id: str, req: WorkspaceUpdateRequest) -> Workspace:
        ws = self.get_workspace(workspace_id)
        if req.name is not None:
            ws.name = req.name.strip()
            # Update slug if renamed
            new_slug = slugify(ws.name)
            existing = self._repo.get_workspace_by_slug(new_slug)
            if existing and existing.workspace_id != ws.workspace_id:
                new_slug = f"{new_slug}-{ws.workspace_id[-4:]}"
            ws.slug = new_slug

        if req.description is not None:
            ws.description = req.description.strip() if req.description else None

        if req.metadata is not None:
            ws.metadata.update(req.metadata)

        ws.updated_at = datetime.now(timezone.utc).isoformat()
        saved = self._repo.save_workspace(ws)

        self._repo.record_activity(
            ActivityRecord(
                workspace_id=saved.workspace_id,
                project_id="",
                activity_type=ActivityType.WORKSPACE_UPDATED,
                metadata={"name": saved.name},
            )
        )
        return saved

    def archive_workspace(self, workspace_id: str) -> Workspace:
        ws = self.get_workspace(workspace_id)
        ws.status = WorkspaceStatus.ARCHIVED
        ws.archived_at = datetime.now(timezone.utc).isoformat()
        saved = self._repo.save_workspace(ws)

        self._repo.record_activity(
            ActivityRecord(
                workspace_id=saved.workspace_id,
                project_id="",
                activity_type=ActivityType.WORKSPACE_ARCHIVED,
                metadata={"name": saved.name},
            )
        )
        return saved

    def restore_workspace(self, workspace_id: str) -> Workspace:
        ws = self.get_workspace(workspace_id)
        ws.status = WorkspaceStatus.ACTIVE
        ws.archived_at = None
        saved = self._repo.save_workspace(ws)

        self._repo.record_activity(
            ActivityRecord(
                workspace_id=saved.workspace_id,
                project_id="",
                activity_type=ActivityType.WORKSPACE_RESTORED,
                metadata={"name": saved.name},
            )
        )
        return saved


workspace_service = WorkspaceService()
