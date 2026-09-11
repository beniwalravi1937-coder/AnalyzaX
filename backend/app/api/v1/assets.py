"""
REST API Router for Phase 16 Asset Registry and Lineage.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from backend.app.api.deps import get_current_user_optional
from backend.app.engines.auth.models import User

from backend.app.core.logging import logger
from backend.app.engines.workspace.models import (
    AssetCreateRequest,
    AssetRelationshipCreateRequest,
    AssetTagRequest,
    AssetUpdateRequest,
)
from backend.app.services.workspace.asset_service import asset_service
from backend.app.engines.workspace.repository import workspace_repo

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("", response_class=JSONResponse, status_code=201)
async def register_asset(request: AssetCreateRequest):
    asset = asset_service.register_asset(request)
    return asset.model_dump()


@router.post("/relationships", response_class=JSONResponse, status_code=201)
async def create_relationship(request: AssetRelationshipCreateRequest):
    rel = asset_service.add_relationship(
        source_asset_id=request.source_asset_id,
        target_asset_id=request.target_asset_id,
        rel_type=request.relationship_type,
        metadata=request.metadata,
    )
    return rel.model_dump()


@router.get("/{asset_id}", response_class=JSONResponse)
async def get_asset(asset_id: str):
    asset = asset_service.get_asset(asset_id)
    # Record access
    asset_service.record_access(asset_id)
    return asset.model_dump()


@router.patch("/{asset_id}", response_class=JSONResponse)
async def update_asset(asset_id: str, request: AssetUpdateRequest):
    asset = asset_service.update_asset(asset_id, request)
    return asset.model_dump()


@router.post("/{asset_id}/favorite", response_class=JSONResponse)
async def favorite_asset(asset_id: str):
    asset = asset_service.set_favorite(asset_id, True)
    return asset.model_dump()


@router.delete("/{asset_id}/favorite", response_class=JSONResponse)
async def unfavorite_asset(asset_id: str):
    asset = asset_service.set_favorite(asset_id, False)
    return asset.model_dump()


@router.post("/{asset_id}/tags", response_class=JSONResponse)
async def tag_asset(asset_id: str, request: AssetTagRequest):
    asset = asset_service.tag_asset(asset_id, request.tags)
    return asset.model_dump()


@router.post("/{asset_id}/archive", response_class=JSONResponse)
async def archive_asset(asset_id: str):
    asset = asset_service.archive_asset(asset_id)
    return asset.model_dump()


@router.post("/{asset_id}/restore", response_class=JSONResponse)
async def restore_asset(asset_id: str):
    asset = asset_service.restore_asset(asset_id)
    return asset.model_dump()


@router.delete("/{asset_id}", response_class=JSONResponse)
async def delete_asset(
    asset_id: str,
    force: bool = Query(False, description="Force delete even if active dependents exist"),
):
    deleted = asset_service.delete_asset(asset_id, force=force)
    return {"deleted": deleted, "asset_id": asset_id}


@router.get("/{asset_id}/dependencies", response_class=JSONResponse)
async def get_asset_dependencies(asset_id: str):
    summary = asset_service.get_dependencies(asset_id)
    return summary.model_dump()


@router.get("/{asset_id}/lineage", response_class=JSONResponse)
async def get_asset_lineage(
    asset_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    user_id = current_user.user_id if current_user else None
    graph = asset_service.get_lineage(asset_id, user_id=user_id)
    return graph.model_dump()


@router.get("/{asset_id}/relationships", response_class=JSONResponse)
async def list_asset_relationships(asset_id: str):
    downstream = workspace_repo.list_relationships(source_asset_id=asset_id)
    upstream = workspace_repo.list_relationships(target_asset_id=asset_id)
    return {
        "asset_id": asset_id,
        "downstream": [r.model_dump() for r in downstream],
        "upstream": [r.model_dump() for r in upstream],
    }
