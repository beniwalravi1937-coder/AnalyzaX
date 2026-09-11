"""
REST API Router for Phase 16 Global Search.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from backend.app.core.logging import logger
from backend.app.engines.workspace.models import (
    AssetStatus,
    AssetType,
    SearchRequest,
)
from backend.app.api.deps import get_current_user_optional
from backend.app.engines.auth.models import User
from backend.app.services.workspace.search_service import search_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_class=JSONResponse)
async def search_assets(
    q: str = Query("", max_length=200, description="Search query string"),
    workspace_id: Optional[str] = Query(None, description="Scope to workspace"),
    project_id: Optional[str] = Query(None, description="Scope to project"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    asset_types: Optional[List[str]] = Query(None, description="Filter by asset types"),
    asset_type: Optional[str] = Query(None, description="Filter by single asset type"),
    is_favorite: Optional[bool] = Query(None, description="Filter favorites"),
    status: Optional[str] = Query("ACTIVE", description="Filter by status"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    sort_by: str = Query("relevance", description="Sort field (relevance, name, created_at, updated_at)"),
    sort_order: str = Query("desc", description="Sort direction (asc, desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
):
    try:
        merged_types: List[str] = []
        if asset_types:
            merged_types.extend(asset_types)
        if asset_type and asset_type not in merged_types:
            merged_types.append(asset_type)

        types = [AssetType(t) for t in merged_types] if merged_types else None
        ast_status = AssetStatus(status) if status else None

        req = SearchRequest(
            query=q,
            workspace_id=workspace_id,
            project_id=project_id,
            asset_types=types,
            is_favorite=is_favorite,
            status=ast_status,
            tags=tags,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
        )
        user_id = current_user.user_id if current_user else None
        res = search_service.search(req, user_id=user_id)
        return res.model_dump()
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
