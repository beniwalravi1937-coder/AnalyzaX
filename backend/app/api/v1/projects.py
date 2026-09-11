"""
REST API Router for Phase 16 Projects.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from backend.app.api.deps import get_current_user_optional
from backend.app.core.logging import logger
from backend.app.engines.auth.models import User
from backend.app.engines.auth.permissions import Permissions
from backend.app.engines.auth.repository import auth_repo
from backend.app.engines.workspace.models import (
    AssetStatus,
    ProjectDuplicateRequest,
    ProjectUpdateRequest,
)
from backend.app.engines.workspace.repository import workspace_repo
from backend.app.services.auth.authorization_service import authorization_service
from backend.app.services.workspace.project_service import project_service
from backend.app.services.workspace.asset_service import asset_service

router = APIRouter(prefix="/projects", tags=["projects"])


def _verify_project_access(project_id: str, permission: str, user: Optional[User]):
    """Defends against cross-tenant IDOR attacks while preserving backward compatibility."""
    if user:
        if not authorization_service.can(user.user_id, permission, project_id=project_id):
            raise HTTPException(status_code=403, detail=f"Forbidden: Insufficient permissions for project '{permission}'")
    else:
        proj = workspace_repo.get_project(project_id)
        if proj:
            members = auth_repo.list_workspace_members(proj.workspace_id)
            if members:
                raise HTTPException(status_code=401, detail="Authentication required to access project")


@router.get("/{project_id}", response_class=JSONResponse)
async def get_project(
    project_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    _verify_project_access(project_id, Permissions.PROJECT_READ, current_user)
    proj = project_service.get_project(project_id)
    return proj.model_dump()


@router.patch("/{project_id}", response_class=JSONResponse)
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    _verify_project_access(project_id, Permissions.PROJECT_UPDATE, current_user)
    proj = project_service.update_project(project_id, request)
    return proj.model_dump()


@router.post("/{project_id}/archive", response_class=JSONResponse)
async def archive_project(
    project_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    _verify_project_access(project_id, Permissions.PROJECT_DELETE, current_user)
    proj = project_service.archive_project(project_id)
    return proj.model_dump()


@router.post("/{project_id}/restore", response_class=JSONResponse)
async def restore_project(
    project_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    _verify_project_access(project_id, Permissions.PROJECT_UPDATE, current_user)
    proj = project_service.restore_project(project_id)
    return proj.model_dump()


@router.post("/{project_id}/duplicate", response_class=JSONResponse, status_code=201)
async def duplicate_project(
    project_id: str,
    request: ProjectDuplicateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    _verify_project_access(project_id, Permissions.PROJECT_CREATE, current_user)
    try:
        new_proj = project_service.duplicate_project(project_id, request)
        return new_proj.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to duplicate project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}", response_class=JSONResponse)
async def delete_project(
    project_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    _verify_project_access(project_id, Permissions.PROJECT_DELETE, current_user)
    deleted = project_service.delete_project(project_id)
    return {"deleted": deleted, "project_id": project_id}


@router.get("/{project_id}/assets", response_class=JSONResponse)
async def list_project_assets(
    project_id: str,
    asset_type: Optional[str] = Query(None, description="Filter by AssetType"),
    status: Optional[str] = Query("ACTIVE", description="Filter by status (ACTIVE, ARCHIVED, DELETED)"),
    is_favorite: Optional[bool] = Query(None, description="Filter by favorite flag"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    _verify_project_access(project_id, Permissions.PROJECT_READ, current_user)
    try:
        # Validate project exists
        project_service.get_project(project_id)

        asset_status = AssetStatus(status) if status else None
        assets = asset_service.list_assets(
            project_id=project_id,
            asset_type=asset_type,
            status=asset_status,
            is_favorite=is_favorite,
        )
        total = len(assets)
        start = (page - 1) * page_size
        paginated = assets[start : start + page_size]
        return {
            "assets": [a.model_dump() for a in paginated],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid asset status: {status}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list assets for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/activity", response_class=JSONResponse)
async def list_project_activity(
    project_id: str,
    limit: int = Query(50, ge=1, le=200, description="Max activity items to return"),
):
    try:
        project_service.get_project(project_id)
        activities = workspace_repo.list_activity(project_id=project_id, limit=limit)
        return [act.model_dump() for act in activities]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch activity for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/health", response_class=JSONResponse)
async def get_project_health(project_id: str):
    try:
        health = project_service.get_project_health(project_id)
        return health.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compute health for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/export-manifest", response_class=JSONResponse)
async def export_project_manifest(project_id: str):
    try:
        manifest = project_service.export_project_manifest(project_id)
        return manifest
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export manifest for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
