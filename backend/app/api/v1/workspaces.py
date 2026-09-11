"""
REST API Router for Phase 16 Workspaces.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from backend.app.api.deps import get_current_user_optional
from backend.app.core.logging import logger
from backend.app.engines.auth.models import User
from backend.app.engines.auth.permissions import Permissions
from backend.app.engines.auth.repository import auth_repo
from backend.app.engines.workspace.models import (
    Workspace,
    WorkspaceCreateRequest,
    WorkspaceStatus,
    WorkspaceUpdateRequest,
    Project,
    ProjectCreateRequest,
)
from backend.app.services.auth.authorization_service import authorization_service
from backend.app.services.workspace.workspace_service import workspace_service
from backend.app.services.workspace.project_service import project_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def _verify_workspace_access(workspace_id: str, permission: str, user: Optional[User]):
    """Defends against cross-tenant IDOR attacks while preserving backward compatibility."""
    if user:
        if not authorization_service.can(user.user_id, permission, workspace_id=workspace_id):
            raise HTTPException(status_code=403, detail=f"Forbidden: Insufficient permissions for workspace '{permission}'")
    else:
        members = auth_repo.list_workspace_members(workspace_id)
        if members:
            raise HTTPException(status_code=401, detail="Authentication required to access workspace")


@router.get("", response_class=JSONResponse)
async def list_workspaces(
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, ARCHIVED)"),
):
    try:
        ws_status = WorkspaceStatus(status) if status else None
        workspaces = workspace_service.list_workspaces(status=ws_status)
        return [w.model_dump() for w in workspaces]
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid workspace status: {status}")
    except Exception as e:
        logger.error(f"Failed to list workspaces: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_class=JSONResponse, status_code=201)
async def create_workspace(request: WorkspaceCreateRequest):
    try:
        ws = workspace_service.create_workspace(request)
        return ws.model_dump()
    except Exception as e:
        logger.error(f"Failed to create workspace: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workspace_id}", response_class=JSONResponse)
async def get_workspace(
    workspace_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    _verify_workspace_access(workspace_id, Permissions.WORKSPACE_READ, current_user)
    ws = workspace_service.get_workspace(workspace_id)
    return ws.model_dump()


@router.patch("/{workspace_id}", response_class=JSONResponse)
async def update_workspace(
    workspace_id: str,
    request: WorkspaceUpdateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    _verify_workspace_access(workspace_id, Permissions.WORKSPACE_UPDATE, current_user)
    ws = workspace_service.update_workspace(workspace_id, request)
    return ws.model_dump()


@router.post("/{workspace_id}/archive", response_class=JSONResponse)
async def archive_workspace(
    workspace_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    _verify_workspace_access(workspace_id, Permissions.WORKSPACE_DELETE, current_user)
    ws = workspace_service.archive_workspace(workspace_id)
    return ws.model_dump()


@router.post("/{workspace_id}/restore", response_class=JSONResponse)
async def restore_workspace(
    workspace_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    _verify_workspace_access(workspace_id, Permissions.WORKSPACE_UPDATE, current_user)
    ws = workspace_service.restore_workspace(workspace_id)
    return ws.model_dump()


@router.get("/{workspace_id}/projects", response_class=JSONResponse)
async def list_workspace_projects(
    workspace_id: str,
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, ARCHIVED)"),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    _verify_workspace_access(workspace_id, Permissions.WORKSPACE_READ, current_user)
    try:
        proj_status = None
        if status:
            from backend.app.engines.workspace.models import ProjectStatus
            proj_status = ProjectStatus(status)
        projects = project_service.list_projects(workspace_id=workspace_id, status=proj_status)
        return [p.model_dump() for p in projects]
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid project status: {status}")
    except Exception as e:
        logger.error(f"Failed to list projects for workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workspace_id}/projects", response_class=JSONResponse, status_code=201)
async def create_workspace_project(
    workspace_id: str,
    request: ProjectCreateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    _verify_workspace_access(workspace_id, Permissions.PROJECT_CREATE, current_user)
    try:
        proj = project_service.create_project(workspace_id, request)
        return proj.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create project in workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
