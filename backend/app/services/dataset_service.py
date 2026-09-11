import hashlib
import json
import os
import shutil
import time
from datetime import datetime, timezone
from typing import BinaryIO, Dict, List, Optional

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.ingestion import (
    detect_file_format,
    generate_dataset_id,
    generate_safe_sql_identifier,
    normalize_dataset,
    register_dataset_view,
    sanitize_filename,
    unregister_dataset_view,
    validate_dataset_content,
)
from backend.app.models.dataset import DatasetStatus
from backend.app.schemas.dataset import DatasetResponse
from backend.app.services.duckdb_service import duckdb_service


class DatasetService:
    """
    Application Service coordinating dataset ingestion workflows.
    Enforces security, immutability, metadata persistence, and analytical registration.
    """

    def __init__(self) -> None:
        self._uploads_dir = os.path.abspath(settings.DATA_UPLOADS_DIR)
        self._processed_dir = os.path.abspath(settings.DATA_PROCESSED_DIR)
        self._temp_dir = os.path.abspath(settings.DATA_TEMP_DIR)
        self._max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

        # Catalog storage for standalone/dev resilience
        self._catalog_file = os.path.join(self._uploads_dir, "_catalog.json")
        self._ensure_directories()
        self._catalog: Dict[str, dict] = self._load_catalog()

    def _ensure_directories(self) -> None:
        os.makedirs(self._uploads_dir, exist_ok=True)
        os.makedirs(self._processed_dir, exist_ok=True)
        os.makedirs(self._temp_dir, exist_ok=True)

    def _load_catalog(self) -> Dict[str, dict]:
        if os.path.exists(self._catalog_file):
            try:
                with open(self._catalog_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read catalog file, resetting: {e}")
        return {}

    def _save_catalog(self) -> None:
        try:
            with open(self._catalog_file, "w", encoding="utf-8") as f:
                json.dump(self._catalog, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to persist dataset catalog: {e}")

    async def ingest_file(
        self,
        file_obj: BinaryIO,
        original_filename: str,
        content_type: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> DatasetResponse:
        """
        Executes the 6-stage analytical ingestion pipeline with quota enforcement:
        1. Staging & size validation
        2. Hash computation
        3. Format detection & structural validation
        4. Immutable storage preservation
        5. Parquet normalization (if needed)
        6. DuckDB view registration & metadata cataloging
        """
        if workspace_id:
            from backend.app.services.usage import quota_service
            from backend.app.engines.usage.metrics import UsageMetrics

            # Check feature entitlement and upload quota
            quota_service.enforce_feature(workspace_id, "DATASET_UPLOAD")
            quota_service.enforce_quota(
                workspace_id=workspace_id,
                metric_key=UsageMetrics.DATASET_UPLOADS.key,
                quantity=1.0,
            )

        dataset_id = generate_dataset_id()
        sanitized_name = sanitize_filename(original_filename)
        temp_file_path = os.path.join(self._temp_dir, f"{dataset_id}_{sanitized_name}")

        try:
            # ── Stage 1: Stream to temporary staging & enforce size limit ──
            total_bytes = 0
            hasher = hashlib.sha256()

            # Resolve plan-specific max size if workspace is known
            max_size_bytes = self._max_size_bytes
            if workspace_id:
                from backend.app.services.usage import plan_service
                ent = plan_service.get_entitlement(workspace_id, "MAX_DATASET_SIZE_MB")
                if ent and ent.limit is not None:
                    max_size_bytes = min(max_size_bytes, int(ent.limit * 1024 * 1024))

            with open(temp_file_path, "wb") as temp_out:
                while chunk := file_obj.read(1024 * 1024):  # 1MB chunks
                    total_bytes += len(chunk)
                    if total_bytes > max_size_bytes:
                        if workspace_id:
                            from backend.app.core.errors import QuotaExceededException
                            from backend.app.services.usage import plan_service
                            wp = plan_service.get_workspace_plan(workspace_id)
                            raise QuotaExceededException(
                                message=f"Uploaded file exceeds maximum allowed size of {max_size_bytes // (1024 * 1024)}MB.",
                                metric="max_dataset_size_mb",
                                feature="DATASET_UPLOAD",
                                current_usage=round(total_bytes / (1024 * 1024), 2),
                                requested=round(total_bytes / (1024 * 1024), 2),
                                limit=max_size_bytes // (1024 * 1024),
                                remaining=0.0,
                                period="CURRENT",
                                plan=wp.plan_code if wp else "UNKNOWN",
                            )
                        raise ValueError(
                            f"File size exceeds maximum supported limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
                        )
                    hasher.update(chunk)
                    temp_out.write(chunk)

            if total_bytes == 0:
                raise ValueError("Uploaded file is empty (0 bytes).")

            file_hash = hasher.hexdigest()
            logger.info(f"Staged upload: {sanitized_name} ({total_bytes} bytes, hash: {file_hash[:10]}...)")

            # ── Stage 2: Format Detection ──
            detected_format = detect_file_format(temp_file_path, sanitized_name, content_type)
            logger.info(f"Detected format: {detected_format} for dataset {dataset_id}")

            # ── Stage 3: Structural Content Validation ──
            validation_meta = validate_dataset_content(temp_file_path, detected_format)
            selected_sheet = validation_meta.get("selected_sheet")

            # ── Stage 4: Immutable Storage Preservation ──
            dataset_original_dir = os.path.join(self._uploads_dir, dataset_id, "original")
            os.makedirs(dataset_original_dir, exist_ok=True)
            permanent_original_path = os.path.join(dataset_original_dir, sanitized_name)

            # Copy temp file to immutable location
            shutil.copy2(temp_file_path, permanent_original_path)
            logger.info(f"Preserved immutable original at: {permanent_original_path}")

            # ── Stage 5: Normalization (if Excel or JSON) ──
            dataset_processed_dir = os.path.join(self._processed_dir, dataset_id)
            normalized_path = normalize_dataset(
                original_path=permanent_original_path,
                format_str=detected_format,
                processed_dir=dataset_processed_dir,
                sheet_name=selected_sheet,
            )

            # Target file for DuckDB registration
            duckdb_target_path = normalized_path if normalized_path else permanent_original_path
            target_format = "parquet" if normalized_path else detected_format

            # ── Stage 6: DuckDB Registration ──
            sql_table_name = generate_safe_sql_identifier(dataset_id)
            register_dataset_view(
                duckdb_svc=duckdb_service,
                table_name=sql_table_name,
                file_path=duckdb_target_path,
                format_str=target_format,
            )

            # ── Stage 7: Metadata Record Creation ──
            now_iso = datetime.now(timezone.utc).isoformat()
            metadata_record = {
                "id": dataset_id,
                "name": os.path.splitext(sanitized_name)[0].replace("_", " ").title(),
                "original_filename": sanitized_name,
                "file_hash": file_hash,
                "format": detected_format,
                "mime_type": content_type,
                "file_size_bytes": total_bytes,
                "status": DatasetStatus.READY.value,
                "duckdb_table_name": sql_table_name,
                "original_file_path": permanent_original_path,
                "processed_file_path": normalized_path,
                "sheet_name": selected_sheet,
                "created_at": now_iso,
                "updated_at": now_iso,
                "error_message": None,
            }

            self._catalog[dataset_id] = metadata_record
            self._save_catalog()

            if workspace_id:
                from backend.app.services.usage import usage_service
                from backend.app.engines.usage.metrics import UsageMetrics
                usage_service.record_usage(
                    workspace_id=workspace_id,
                    metric_key=UsageMetrics.DATASET_UPLOADS.key,
                    quantity=1.0,
                    operation_type="dataset_upload",
                    resource_type="dataset",
                    resource_id=dataset_id,
                    idempotency_key=f"upload_{dataset_id}",
                )

            return DatasetResponse(**metadata_record)

        except Exception as e:
            logger.error(f"Ingestion failed for {original_filename}: {e}")
            # Register failed metadata if dataset_id was created
            now_iso = datetime.now(timezone.utc).isoformat()
            failed_record = {
                "id": dataset_id,
                "name": sanitized_name,
                "original_filename": sanitized_name,
                "file_hash": "",
                "format": "unknown",
                "mime_type": content_type,
                "file_size_bytes": 0,
                "status": DatasetStatus.FAILED.value,
                "duckdb_table_name": "",
                "original_file_path": "",
                "processed_file_path": None,
                "sheet_name": None,
                "created_at": now_iso,
                "updated_at": now_iso,
                "error_message": str(e),
            }
            self._catalog[dataset_id] = failed_record
            self._save_catalog()
            raise e

        finally:
            # Clean temporary file
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    logger.debug(f"Cleaned staging temp file: {temp_file_path}")
                except Exception as ex:
                    logger.warning(f"Could not remove temp file {temp_file_path}: {ex}")

    def get_dataset(self, dataset_id: str) -> Optional[DatasetResponse]:
        """Retrieves public metadata for a dataset by ID."""
        record = self._catalog.get(dataset_id)
        if not record:
            return None
        return DatasetResponse(**record)

    def list_datasets(self, include_archived: bool = False) -> List[DatasetResponse]:
        """Lists all registered datasets in descending chronological order."""
        records = sorted(
            self._catalog.values(),
            key=lambda r: r.get("created_at", ""),
            reverse=True,
        )
        allowed_statuses = [DatasetStatus.READY.value]
        if include_archived:
            allowed_statuses.append(DatasetStatus.ARCHIVED.value)
        return [DatasetResponse(**r) for r in records if r.get("status") in allowed_statuses]

    def archive_dataset(self, dataset_id: str) -> Optional[DatasetResponse]:
        """Marks a dataset as ARCHIVED while preserving historical files and views."""
        record = self._catalog.get(dataset_id)
        if not record:
            return None
        record["status"] = DatasetStatus.ARCHIVED.value
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save_catalog()
        return DatasetResponse(**record)

    def restore_dataset(self, dataset_id: str) -> Optional[DatasetResponse]:
        """Restores an ARCHIVED dataset back to READY status."""
        record = self._catalog.get(dataset_id)
        if not record:
            return None
        record["status"] = DatasetStatus.READY.value
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save_catalog()
        return DatasetResponse(**record)

    def delete_dataset(self, dataset_id: str) -> bool:
        """Unregisters from DuckDB and removes metadata entry, clearing all associated caches."""
        record = self._catalog.get(dataset_id)
        if not record:
            return False

        # Drop from DuckDB
        table_name = record.get("duckdb_table_name")
        if table_name:
            unregister_dataset_view(duckdb_service, table_name)

        del self._catalog[dataset_id]
        self._save_catalog()

        # Invalidate analytical caches
        try:
            from backend.app.core.cache import cache_service
            cache_service.invalidate_pattern(dataset_id)
            from backend.app.engines.sql.cache import query_cache
            query_cache.invalidate(dataset_id)
        except Exception as e:
            logger.warning(f"Error invalidating cache for deleted dataset {dataset_id}: {e}")

        return True

    def re_register_all_views(self) -> int:
        """Re-registers all valid datasets from catalog into DuckDB upon startup or service reload."""
        count = 0
        for ds_id, meta in self._catalog.items():
            if meta.get("status") == DatasetStatus.READY.value:
                table_name = meta.get("duckdb_table_name")
                norm_path = meta.get("processed_file_path")
                orig_path = meta.get("original_file_path")
                target_path = norm_path if norm_path and os.path.exists(norm_path) else orig_path
                target_format = "parquet" if norm_path else meta.get("format")

                if target_path and os.path.exists(target_path) and table_name:
                    try:
                        register_dataset_view(
                            duckdb_svc=duckdb_service,
                            table_name=table_name,
                            file_path=target_path,
                            format_str=target_format,
                        )
                        count += 1
                    except Exception as e:
                        logger.warning(f"Could not re-register DuckDB view for {ds_id}: {e}")
        logger.info(f"Re-registered {count} dataset view(s) in DuckDB engine.")
        return count


dataset_service = DatasetService()
