"""
Persistence Repository for Phase 15 Export Engine.
Thread-safe persistence for Export Jobs and artifact files.
"""

import json
import os
import shutil
import threading
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.exports.models import ExportJob, ExportStatus


class ExportRepository:
    """
    Thread-safe repository for persisting and querying export jobs.
    Stores job metadata in a JSON file and artifacts in a subdirectory.
    """

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or os.path.join(
            settings.DATA_EXPORTS_DIR, "jobs.json"
        )
        self.artifacts_dir = os.path.join(settings.DATA_EXPORTS_DIR, "artifacts")
        self._lock = threading.Lock()
        self._ensure_dirs()

    def _ensure_dirs(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        os.makedirs(self.artifacts_dir, exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def get_all(
        self,
        dataset_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[ExportJob]:
        """Get all export jobs, optionally filtered."""
        with self._lock:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                jobs = [ExportJob.model_validate(d) for d in data]

                if dataset_id:
                    jobs = [j for j in jobs if j.dataset_id == dataset_id]

                if status:
                    jobs = [j for j in jobs if j.status.value == status]

                # Sort by created_at desc
                jobs.sort(key=lambda x: x.created_at, reverse=True)
                return jobs
            except Exception as e:
                logger.error(f"ExportRepository.get_all failed: {e}")
                return []

    def get_by_id(self, job_id: str) -> Optional[ExportJob]:
        """Get a specific export job by ID."""
        jobs = self.get_all()
        for job in jobs:
            if job.job_id == job_id:
                return job
        return None

    def save(self, job: ExportJob) -> ExportJob:
        """Save or update an export job."""
        with self._lock:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = []

            # Find and update existing, or append new
            updated = False
            for i, item in enumerate(data):
                if item.get("job_id") == job.job_id:
                    data[i] = json.loads(job.model_dump_json())
                    updated = True
                    break

            if not updated:
                data.append(json.loads(job.model_dump_json()))

            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)

            return job

    def delete(self, job_id: str) -> bool:
        """Delete an export job and its artifact files."""
        with self._lock:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Find the job
                job_data = None
                new_data = []
                for item in data:
                    if item.get("job_id") == job_id:
                        job_data = item
                    else:
                        new_data.append(item)

                if not job_data:
                    return False

                # Remove artifact files
                artifact_dir = os.path.join(self.artifacts_dir, job_id)
                if os.path.isdir(artifact_dir):
                    shutil.rmtree(artifact_dir, ignore_errors=True)

                # Also remove single file if stored directly
                file_path = job_data.get("file_path")
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass

                # Save updated list
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump(new_data, f, indent=2, default=str)

                return True
            except Exception as e:
                logger.error(f"ExportRepository.delete failed: {e}")
                return False

    def get_artifact_dir(self, job_id: str) -> str:
        """Get the artifact directory for a specific job."""
        path = os.path.join(self.artifacts_dir, job_id)
        os.makedirs(path, exist_ok=True)
        return path

    def cleanup_expired(self, ttl_hours: Optional[int] = None) -> int:
        """
        Remove exports older than TTL.
        Returns count of removed jobs.
        """
        ttl = ttl_hours or settings.EXPORT_ARTIFACT_TTL_HOURS
        cutoff = datetime.now(timezone.utc) - timedelta(hours=ttl)
        removed = 0

        jobs = self.get_all()
        for job in jobs:
            try:
                created = datetime.fromisoformat(job.created_at)
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                if created < cutoff:
                    if self.delete(job.job_id):
                        removed += 1
            except Exception as e:
                logger.warning(f"Failed to check job {job.job_id} expiry: {e}")

        if removed:
            logger.info(f"Cleaned up {removed} expired export jobs")

        return removed
