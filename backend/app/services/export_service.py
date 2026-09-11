"""
Application Service for Phase 15 Advanced Export, Reporting & Presentation Engine.
Coordinates export job lifecycle, source reading, rendering, and artifact persistence.
"""

from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.exports.models import (
    EXPORT_CONTENT_TYPES,
    EXPORT_FILE_EXTENSIONS,
    ExportFormat,
    ExportJob,
    ExportProvenance,
    ExportRequest,
    ExportSourceType,
    ExportStatus,
    ReportGenerateRequest,
    ReportTemplate,
)
from backend.app.engines.notifications.models import ApplicationEventType
from backend.app.services.notifications.event_dispatcher import event_dispatcher
from backend.app.engines.exports.renderers import (
    CsvRenderer,
    HtmlReportRenderer,
    JsonRenderer,
    MarkdownReportRenderer,
    XlsxRenderer,
)
from backend.app.engines.exports.report_builder import ReportBuilder
from backend.app.engines.exports.repository import ExportRepository
from backend.app.engines.exports.source_reader import (
    DatasetSourceReader,
    get_source_reader,
)
from backend.app.services.cleaning.version_service import VersionService
from backend.app.services.dataset_service import dataset_service


class ExportService:
    """
    Coordinates the full export lifecycle:
    1. Validates the source exists and resolves dataset version.
    2. Reads finalized analytical results via source readers.
    3. Dispatches to format-specific renderers.
    4. Persists export artifacts and job metadata.
    """

    # Tabular formats that work with list[dict] data
    TABULAR_FORMATS = {ExportFormat.CSV, ExportFormat.JSON, ExportFormat.XLSX}
    # Report formats that require ReportDefinition
    REPORT_FORMATS = {ExportFormat.HTML_REPORT, ExportFormat.MARKDOWN_REPORT}

    def __init__(self):
        self._repository = ExportRepository()
        self._version_service = VersionService()
        self._report_builder = ReportBuilder()

    def _resolve_version(
        self, dataset_id: str, version_id: Optional[str] = None
    ) -> Tuple[str, str]:
        """Resolve dataset version and return (version_id, parquet_path)."""
        if not version_id:
            version = self._version_service.get_or_create_v1(dataset_id)
            version_id = version.version_id
        else:
            version = self._version_service.get_version(dataset_id, version_id)
            if not version:
                version = self._version_service.get_or_create_v1(dataset_id)
                version_id = version.version_id

        parquet_path = version.storage_path
        if not os.path.exists(parquet_path):
            ds = dataset_service.get_dataset(dataset_id)
            if ds and hasattr(ds, "file_path") and os.path.exists(ds.file_path):
                parquet_path = ds.file_path
            else:
                raise ValueError(
                    f"Parquet file not found for dataset {dataset_id} version {version_id}"
                )

        return version_id, parquet_path

    def create_export(self, request: ExportRequest) -> ExportJob:
        """
        Create and execute a new export job.
        Validates source, reads data, renders to format, persists artifact.
        """
        # Validate dataset exists
        ds = dataset_service.get_dataset(request.dataset_id)
        if not ds:
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Resolve version
        version_id, parquet_path = self._resolve_version(
            request.dataset_id, request.version_id
        )

        # Validate format/source compatibility
        if request.format in self.REPORT_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Use the /exports/reports endpoint for {request.format.value} format",
            )

        workspace_id = getattr(request, "workspace_id", None) or request.options.get("workspace_id")
        if workspace_id:
            from backend.app.services.usage import quota_service
            from backend.app.engines.usage.metrics import UsageMetrics

            quota_service.enforce_feature(workspace_id, "REPORT_EXPORT")
            quota_service.enforce_quota(
                workspace_id=workspace_id,
                metric_key=UsageMetrics.EXPORTS_GENERATED.key,
                quantity=1.0,
            )

        # Create job
        job = ExportJob(
            dataset_id=request.dataset_id,
            version_id=version_id,
            source_type=request.source_type,
            source_id=request.source_id,
            format=request.format,
            status=ExportStatus.PROCESSING,
            content_type=EXPORT_CONTENT_TYPES.get(request.format, "application/octet-stream"),
            options=request.options,
        )
        self._repository.save(job)

        try:
            # Read source data
            source_data = self._read_source(
                request.source_type,
                request.dataset_id,
                version_id,
                parquet_path,
                request.source_id,
            )

            # Render to format
            artifact_dir = self._repository.get_artifact_dir(job.job_id)
            file_ext = EXPORT_FILE_EXTENSIONS.get(request.format, ".dat")
            file_name = self._generate_filename(
                request.dataset_id, request.source_type, request.format
            )
            output_path = os.path.join(artifact_dir, file_name)

            renderer = self._get_renderer(request.format)
            file_path, file_size, row_count = renderer.render(
                source_data, output_path, request.options
            )

            # Check file size limit
            if file_size > settings.EXPORT_MAX_FILE_SIZE_BYTES:
                os.remove(file_path)
                raise ValueError(
                    f"Export file exceeds maximum size limit "
                    f"({file_size} > {settings.EXPORT_MAX_FILE_SIZE_BYTES})"
                )

            # Update job
            job.status = ExportStatus.COMPLETED
            job.file_path = file_path
            job.file_name = file_name
            job.file_size_bytes = file_size
            job.row_count = row_count
            job.completed_at = datetime.now(timezone.utc).isoformat()
            job.provenance = source_data.provenance

            # Dispatch EXPORT_COMPLETED event
            event_dispatcher.create_and_dispatch(
                event_type=ApplicationEventType.EXPORT_COMPLETED,
                actor_user_id=request.options.get("user_id"),
                resource_type="EXPORT",
                resource_id=job.job_id,
                metadata={
                    "recipient_user_id": request.options.get("user_id"),
                    "resource_name": file_name,
                    "file_name": file_name,
                    "format": request.format.value,
                    "row_count": row_count,
                    "dataset_id": request.dataset_id,
                },
            )

            # Record usage if workspace is known
            if workspace_id:
                from backend.app.services.usage import usage_service
                from backend.app.engines.usage.metrics import UsageMetrics
                usage_service.record_usage(
                    workspace_id=workspace_id,
                    metric_key=UsageMetrics.EXPORTS_GENERATED.key,
                    quantity=1.0,
                    operation_type="export",
                    resource_type="export_job",
                    resource_id=job.job_id,
                    idempotency_key=f"export_{job.job_id}",
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Export job {job.job_id} failed: {e}")
            job.status = ExportStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc).isoformat()

            # Dispatch EXPORT_FAILED event
            event_dispatcher.create_and_dispatch(
                event_type=ApplicationEventType.EXPORT_FAILED,
                actor_user_id=request.options.get("user_id"),
                resource_type="EXPORT",
                resource_id=job.job_id,
                metadata={
                    "recipient_user_id": request.options.get("user_id"),
                    "resource_name": f"{request.format.value} Export",
                    "error_summary": str(e)[:150],
                    "dataset_id": request.dataset_id,
                },
            )

        self._repository.save(job)
        return job

    def get_export(self, job_id: str) -> ExportJob:
        """Get export job details."""
        job = self._repository.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Export job not found")
        return job

    def list_exports(
        self,
        dataset_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[ExportJob]:
        """List export jobs with optional filters."""
        return self._repository.get_all(dataset_id=dataset_id, status=status)

    def download_export(self, job_id: str) -> Tuple[str, str, str]:
        """
        Get file path for download.
        Returns (file_path, file_name, content_type).
        """
        job = self.get_export(job_id)

        if job.status != ExportStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"Export job is not completed (status: {job.status.value})",
            )

        if not job.file_path or not os.path.exists(job.file_path):
            raise HTTPException(
                status_code=404, detail="Export artifact file not found"
            )

        return (
            job.file_path,
            job.file_name or os.path.basename(job.file_path),
            job.content_type or "application/octet-stream",
        )

    def delete_export(self, job_id: str) -> bool:
        """Delete an export job and its artifacts."""
        job = self._repository.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Export job not found")
        return self._repository.delete(job_id)

    def generate_report(self, request: ReportGenerateRequest) -> ExportJob:
        """
        Generate a report from a template and render to requested format.
        """
        # Validate dataset
        ds = dataset_service.get_dataset(request.dataset_id)
        if not ds:
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Resolve version
        version_id, _parquet_path = self._resolve_version(
            request.dataset_id, request.version_id
        )

        # Validate format
        if request.format not in self.REPORT_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Report generation requires HTML_REPORT or MARKDOWN_REPORT format, got {request.format.value}",
            )

        # Create job
        job = ExportJob(
            dataset_id=request.dataset_id,
            version_id=version_id,
            source_type=ExportSourceType.DATASET,
            format=request.format,
            status=ExportStatus.PROCESSING,
            content_type=EXPORT_CONTENT_TYPES.get(request.format, "text/html"),
        )
        self._repository.save(job)

        try:
            # Build report definition from template
            report_def = self._report_builder.build(
                dataset_id=request.dataset_id,
                version_id=version_id,
                template=request.template,
                title=request.title,
                subtitle=request.subtitle,
                custom_sections=request.sections,
            )

            # Render report
            artifact_dir = self._repository.get_artifact_dir(job.job_id)
            file_ext = EXPORT_FILE_EXTENSIONS.get(request.format, ".html")
            file_name = self._generate_report_filename(
                request.dataset_id, request.template, request.format
            )
            output_path = os.path.join(artifact_dir, file_name)

            report_data = {
                "title": report_def.title,
                "subtitle": report_def.subtitle,
                "sections": [s.model_dump() for s in report_def.sections],
                "provenance": report_def.provenance.model_dump() if report_def.provenance else {},
                "dataset_id": report_def.dataset_id,
            }

            if request.format == ExportFormat.HTML_REPORT:
                renderer = HtmlReportRenderer()
            else:
                renderer = MarkdownReportRenderer()

            file_path, file_size, section_count = renderer.render(
                report_data, output_path
            )

            # Check file size
            if file_size > settings.EXPORT_MAX_FILE_SIZE_BYTES:
                os.remove(file_path)
                raise ValueError("Report exceeds maximum file size limit")

            job.status = ExportStatus.COMPLETED
            job.file_path = file_path
            job.file_name = file_name
            job.file_size_bytes = file_size
            job.row_count = section_count
            job.completed_at = datetime.now(timezone.utc).isoformat()
            job.provenance = report_def.provenance

            # Dispatch REPORT_EXPORTED event
            event_dispatcher.create_and_dispatch(
                event_type=ApplicationEventType.REPORT_EXPORTED,
                actor_user_id=request.options.get("user_id"),
                resource_type="REPORT",
                resource_id=job.job_id,
                metadata={
                    "recipient_user_id": request.options.get("user_id"),
                    "resource_name": report_def.title or "Analytical Report",
                    "file_name": file_name,
                    "format": request.format.value,
                    "dataset_id": request.dataset_id,
                },
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Report generation {job.job_id} failed: {e}")
            job.status = ExportStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc).isoformat()

            # Dispatch EXPORT_FAILED event
            event_dispatcher.create_and_dispatch(
                event_type=ApplicationEventType.EXPORT_FAILED,
                actor_user_id=request.options.get("user_id"),
                resource_type="REPORT",
                resource_id=job.job_id,
                metadata={
                    "recipient_user_id": request.options.get("user_id"),
                    "resource_name": f"{request.format.value} Report",
                    "error_summary": str(e)[:150],
                    "dataset_id": request.dataset_id,
                },
            )

        self._repository.save(job)
        return job

    def list_report_templates(self) -> List[Dict[str, Any]]:
        """Return available report templates with metadata."""
        return self._report_builder.list_templates()

    def cleanup_expired(self) -> int:
        """Remove exports older than the configured TTL."""
        return self._repository.cleanup_expired()

    # ─────────────────────────────────────────────────────────
    # Private Helpers
    # ─────────────────────────────────────────────────────────

    def _read_source(
        self,
        source_type: ExportSourceType,
        dataset_id: str,
        version_id: str,
        parquet_path: str,
        source_id: Optional[str] = None,
    ):
        """Read source data using the appropriate reader."""
        if source_type == ExportSourceType.DATASET:
            reader = DatasetSourceReader()
            return reader.read(dataset_id, version_id, parquet_path)
        else:
            reader = get_source_reader(source_type)
            return reader.read(dataset_id, version_id, source_id)

    def _get_renderer(self, export_format: ExportFormat):
        """Get the appropriate renderer for the format."""
        renderers = {
            ExportFormat.CSV: CsvRenderer,
            ExportFormat.JSON: JsonRenderer,
            ExportFormat.XLSX: XlsxRenderer,
        }
        renderer_class = renderers.get(export_format)
        if not renderer_class:
            raise ValueError(f"Unsupported tabular format: {export_format.value}")
        return renderer_class()

    def _generate_filename(
        self,
        dataset_id: str,
        source_type: ExportSourceType,
        export_format: ExportFormat,
    ) -> str:
        """Generate a descriptive filename for the export artifact."""
        ds_short = dataset_id[:12] if len(dataset_id) > 12 else dataset_id
        source_label = source_type.value.lower()
        ext = EXPORT_FILE_EXTENSIONS.get(export_format, ".dat")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"{ds_short}_{source_label}_{timestamp}{ext}"

    def _generate_report_filename(
        self,
        dataset_id: str,
        template: ReportTemplate,
        export_format: ExportFormat,
    ) -> str:
        """Generate a filename for a report artifact."""
        ds_short = dataset_id[:12] if len(dataset_id) > 12 else dataset_id
        template_label = template.value.lower()
        ext = EXPORT_FILE_EXTENSIONS.get(export_format, ".html")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"{ds_short}_{template_label}_{timestamp}{ext}"


# Module-level singleton
export_service = ExportService()
