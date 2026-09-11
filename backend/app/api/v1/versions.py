"""
Dataset Versions & Lineage API Router
Provides endpoints for version management, rollback/activation, lineage DAG, and version comparisons.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from backend.app.core.logging import logger
from backend.app.engines.transformations.models import DatasetVersion, QualityComparison
from backend.app.schemas.cleaning import LineageResponse, VersionActivateResponse
from backend.app.services.cleaning import comparison_service, version_service
from backend.app.services.dataset_service import dataset_service

router = APIRouter(prefix="/versions", tags=["Dataset Versions & Lineage"])


@router.get(
    "/{dataset_id}",
    response_model=List[DatasetVersion],
    summary="List all versions for a dataset",
)
async def list_dataset_versions(dataset_id: str):
    dataset = dataset_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    try:
        versions = version_service.list_versions(dataset_id)
        return versions
    except Exception as e:
        logger.error(f"Failed to list versions for {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list versions: {str(e)}")


@router.get(
    "/{dataset_id}/active",
    response_model=DatasetVersion,
    summary="Get currently active version for a dataset",
)
async def get_active_dataset_version(dataset_id: str):
    dataset = dataset_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    try:
        active = version_service.get_active_version(dataset_id)
        return active
    except Exception as e:
        logger.error(f"Failed to get active version for {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active version: {str(e)}")


@router.post(
    "/{dataset_id}/activate/{version_id}",
    response_model=VersionActivateResponse,
    summary="Activate or rollback dataset to a specified version",
)
async def activate_dataset_version(dataset_id: str, version_id: str):
    dataset = dataset_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    try:
        active = version_service.set_active_version(dataset_id, version_id)
        return VersionActivateResponse(
            active_version=active,
            message=f"Dataset successfully switched to version {version_id}.",
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to activate version {version_id} for {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to activate version: {str(e)}")


@router.get(
    "/{dataset_id}/lineage",
    response_model=LineageResponse,
    summary="Get lineage DAG data for visualization",
)
async def get_dataset_lineage(dataset_id: str):
    dataset = dataset_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    try:
        lineage = version_service.get_lineage(dataset_id)
        return LineageResponse(**lineage)
    except Exception as e:
        logger.error(f"Failed to get lineage for {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get lineage: {str(e)}")


@router.get(
    "/{dataset_id}/compare",
    response_model=QualityComparison,
    summary="Compare quality metrics between two dataset versions",
)
async def compare_dataset_versions(
    dataset_id: str,
    before: str = Query(..., description="Source/Baseline version ID, e.g. 'v1'"),
    after: str = Query(..., description="Target version ID, e.g. 'v2'"),
):
    dataset = dataset_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    try:
        comparison = comparison_service.compare_versions(
            dataset_id=dataset_id,
            before_version_id=before,
            after_version_id=after,
        )
        return comparison
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to compare versions for {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare versions: {str(e)}")
