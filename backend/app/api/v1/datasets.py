from typing import Optional
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from backend.app.core.logging import logger
from backend.app.engines.workspace.models import DatasetVersionComparisonResult
from backend.app.schemas.dataset import (
    DatasetListResponse,
    DatasetResponse,
    DatasetUploadResponse,
)
from backend.app.schemas.profile import DatasetProfileResponse
from backend.app.schemas.quality import DataQualityReportResponse
from backend.app.services.dataset_service import dataset_service
from backend.app.services.profiling_service import profiling_service
from backend.app.services.quality_service import quality_service

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post(
    "/upload",
    response_model=DatasetUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a dataset",
    description="Uploads a CSV, XLSX, JSON, or Parquet dataset, validates structure, preserves original immutably, and registers an analytical view in DuckDB.",
)
async def upload_dataset(
    file: UploadFile = File(...),
    workspace_id: Optional[str] = Query(None, description="Target workspace ID for quota metering"),
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename must not be empty.",
        )

    try:
        dataset_meta = await dataset_service.ingest_file(
            file_obj=file.file,
            original_filename=file.filename,
            content_type=file.content_type,
            workspace_id=workspace_id,
        )

        return DatasetUploadResponse(
            dataset_id=dataset_meta.id,
            status=dataset_meta.status,
            filename=dataset_meta.original_filename,
            format=dataset_meta.format,
            file_size_bytes=dataset_meta.file_size_bytes,
            duckdb_table_name=dataset_meta.duckdb_table_name,
            message="Dataset successfully uploaded and ingested into analytical engine",
        )

    except ValueError as e:
        logger.warning(f"Validation failure during upload of {file.filename}: {e}")
        error_msg = str(e)
        status_code = (
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            if "exceeds maximum supported limit" in error_msg
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=error_msg)

    except Exception as e:
        logger.error(f"Unexpected error uploading {file.filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while processing the dataset: {str(e)}",
        )


@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
    summary="Get dataset status and metadata",
    description="Retrieves public structural metadata and current ingestion status for a dataset.",
)
async def get_dataset(dataset_id: str):
    dataset = dataset_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found.",
        )
    return dataset


@router.get(
    "/{dataset_id}/profile",
    response_model=DatasetProfileResponse,
    summary="Get automated dataset profile and semantic intelligence",
    description="Returns detailed structural metrics, physical types, inferred semantic types, distributions, and ML target candidates.",
)
async def get_dataset_profile(dataset_id: str):
    try:
        return profiling_service.profile_dataset(dataset_id=dataset_id, force_refresh=False)
    except ValueError as e:
        err_msg = str(e)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
    except Exception as e:
        logger.error(f"Failed to generate profile for {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to profile dataset: {str(e)}",
        )


@router.post(
    "/{dataset_id}/profile/refresh",
    response_model=DatasetProfileResponse,
    summary="Force refresh dataset profiling",
    description="Invalidates profile cache and re-scans the dataset view in DuckDB.",
)
async def refresh_dataset_profile(dataset_id: str):
    try:
        return profiling_service.profile_dataset(dataset_id=dataset_id, force_refresh=True)
    except ValueError as e:
        err_msg = str(e)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
    except Exception as e:
        logger.error(f"Failed to refresh profile for {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh dataset profile: {str(e)}",
        )


@router.get(
    "/{dataset_id}/quality",
    response_model=DataQualityReportResponse,
    summary="Get or generate dataset quality assessment",
    description="Returns a deterministic, comprehensive Data Quality Report across 6 foundational dimensions.",
)
async def get_dataset_quality(
    dataset_id: str,
    severity: Optional[str] = Query(None, description="Filter issues by severity: CRITICAL, HIGH, MEDIUM, LOW, INFO"),
    dimension: Optional[str] = Query(None, description="Filter issues by dimension: COMPLETENESS, UNIQUENESS, etc."),
    column: Optional[str] = Query(None, description="Filter issues by column name"),
):
    try:
        return quality_service.assess_dataset_quality(
            dataset_id=dataset_id,
            force_refresh=False,
            severity_filter=severity,
            dimension_filter=dimension,
            column_filter=column,
        )
    except ValueError as e:
        err_msg = str(e)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
    except Exception as e:
        logger.error(f"Failed to assess quality for {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assess dataset quality: {str(e)}",
        )


@router.post(
    "/{dataset_id}/quality/refresh",
    response_model=DataQualityReportResponse,
    summary="Force refresh dataset quality assessment",
    description="Invalidates quality cache and re-evaluates all deterministic quality rules against the DuckDB view.",
)
async def refresh_dataset_quality(dataset_id: str):
    try:
        return quality_service.assess_dataset_quality(dataset_id=dataset_id, force_refresh=True)
    except ValueError as e:
        err_msg = str(e)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
    except Exception as e:
        logger.error(f"Failed to refresh quality for {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh dataset quality: {str(e)}",
        )


@router.get(
    "",
    response_model=DatasetListResponse,
    summary="List all registered datasets",
    description="Returns a chronological list of active ingested datasets.",
)
async def list_datasets(include_archived: bool = Query(False, description="Whether to include archived datasets")):
    datasets = dataset_service.list_datasets(include_archived=include_archived)
    return DatasetListResponse(datasets=datasets, total=len(datasets))


@router.post(
    "/{dataset_id}/archive",
    response_model=DatasetResponse,
    summary="Archive dataset",
    description="Sets dataset status to ARCHIVED while preserving historical data and versions.",
)
async def archive_dataset(dataset_id: str):
    dataset = dataset_service.archive_dataset(dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found.",
        )
    return DatasetResponse(
        dataset_id=dataset.dataset_id,
        filename=dataset.filename,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        size_bytes=dataset.size_bytes,
        status=dataset.status.value if hasattr(dataset.status, "value") else str(dataset.status),
        created_at=dataset.created_at,
        current_version_id=dataset.current_version_id,
        schema=[c.model_dump() for c in dataset.schema_cols],
    )


@router.post(
    "/{dataset_id}/restore",
    response_model=DatasetResponse,
    summary="Restore dataset",
    description="Restores an ARCHIVED dataset back to READY status.",
)
async def restore_dataset(dataset_id: str):
    dataset = dataset_service.restore_dataset(dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found.",
        )
    return DatasetResponse(
        dataset_id=dataset.dataset_id,
        filename=dataset.filename,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        size_bytes=dataset.size_bytes,
        status=dataset.status.value if hasattr(dataset.status, "value") else str(dataset.status),
        created_at=dataset.created_at,
        current_version_id=dataset.current_version_id,
        schema=[c.model_dump() for c in dataset.schema_cols],
    )


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete dataset",
    description="Unregisters the dataset from the DuckDB analytical engine.",
)
async def delete_dataset(dataset_id: str):
    success = dataset_service.delete_dataset(dataset_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found.",
        )
    return None


@router.get(
    "/{dataset_id}/versions",
    summary="List all versions for a dataset",
    description="Returns all version snapshots for the specified dataset.",
)
async def list_versions_for_dataset(dataset_id: str):
    from backend.app.services.cleaning import version_service
    dataset = dataset_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    return version_service.list_versions(dataset_id)


@router.get(
    "/{dataset_id}/versions/compare",
    response_model=DatasetVersionComparisonResult,
    summary="Compare metadata between two dataset versions",
    description="Fast metadata-level comparison comparing schemas, row counts, and column counts without re-profiling.",
)
async def compare_dataset_versions_metadata_endpoint(
    dataset_id: str,
    before: str = Query(..., description="Source/Baseline version ID, e.g. 'v1'"),
    after: str = Query(..., description="Target version ID, e.g. 'v2'"),
):
    from backend.app.services.cleaning import comparison_service
    dataset = dataset_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    try:
        res = comparison_service.compare_versions_metadata(dataset_id, before, after)
        return DatasetVersionComparisonResult(**res)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@router.get(
    "/{dataset_id}/versions/{version_id}",
    summary="Get a specific version for a dataset",
    description="Returns metadata for a specific dataset version snapshot.",
)
async def get_single_dataset_version(dataset_id: str, version_id: str):
    from backend.app.services.cleaning import version_service
    dataset = dataset_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    version = version_service.get_version(dataset_id, version_id)
    if not version:
        raise HTTPException(status_code=404, detail=f"Version '{version_id}' not found.")
    return version


