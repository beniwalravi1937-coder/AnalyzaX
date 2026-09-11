"""
REST API Router for Phase 15 Advanced Export, Reporting & Presentation Engine.
Thin orchestration layer — delegates to ExportService.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

from backend.app.core.logging import logger
from backend.app.engines.exports.models import (
    ExportFormat,
    ExportRequest,
    ExportSourceType,
    ExportStatus,
    ReportGenerateRequest,
    ReportTemplate,
)
from backend.app.services.export_service import export_service

router = APIRouter(prefix="/exports", tags=["exports"])


# ─────────────────────────────────────────────────────────────
# Export Job Endpoints
# ─────────────────────────────────────────────────────────────


@router.post("", response_class=JSONResponse)
async def create_export(request: ExportRequest):
    """Create a new export job. Returns the job with status and download info."""
    try:
        job = export_service.create_export(request)
        return job.model_dump()
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Export creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")


@router.get("", response_class=JSONResponse)
async def list_exports(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
):
    """List all export jobs with optional filtering."""
    try:
        jobs = export_service.list_exports(dataset_id=dataset_id, status=status)
        return [job.model_dump() for job in jobs]
    except Exception as e:
        logger.error(f"Export listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/templates", response_class=JSONResponse)
async def list_report_templates():
    """List available report templates with descriptions."""
    try:
        return export_service.list_report_templates()
    except Exception as e:
        logger.error(f"Template listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}", response_class=JSONResponse)
async def get_export(job_id: str):
    """Get export job details and status."""
    try:
        job = export_service.get_export(job_id)
        return job.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/download")
async def download_export(job_id: str):
    """Download the export artifact file."""
    try:
        file_path, file_name, content_type = export_service.download_export(job_id)
        return FileResponse(
            path=file_path,
            filename=file_name,
            media_type=content_type,
            headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export download failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{job_id}", response_class=JSONResponse)
async def delete_export(job_id: str):
    """Delete an export job and its artifact."""
    try:
        deleted = export_service.delete_export(job_id)
        return {"deleted": deleted, "job_id": job_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Report Endpoints
# ─────────────────────────────────────────────────────────────


@router.post("/reports", response_class=JSONResponse)
async def generate_report(request: ReportGenerateRequest):
    """Generate a report from a template. Returns the export job with download info."""
    try:
        job = export_service.generate_report(request)
        return job.model_dump()
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")


# ─────────────────────────────────────────────────────────────
# Maintenance Endpoints
# ─────────────────────────────────────────────────────────────


@router.post("/cleanup", response_class=JSONResponse)
async def cleanup_expired():
    """Trigger manual cleanup of expired export artifacts."""
    try:
        removed = export_service.cleanup_expired()
        return {"removed": removed, "message": f"Cleaned up {removed} expired exports"}
    except Exception as e:
        logger.error(f"Export cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
