"""
AnalyzaX — Phase 22: Safe Storage Cleanup Service.
Safely purges abandoned partial uploads and stale temporary files
without endangering immutable original datasets or versioned lineage.
"""

import os
import time
from typing import Dict
from backend.app.core.config import settings
from backend.app.core.logging import logger


class StorageCleanupService:
    """Safely cleans ephemeral workspace files."""

    def cleanup_stale_temp_files(self, max_age_seconds: int = 3600) -> Dict[str, int]:
        """
        Removes temporary files older than max_age_seconds from DATA_TEMP_DIR.
        STRICT CONSTITUTIONAL RULE: Never deletes from uploads or processed directories!
        """
        temp_dir = os.path.abspath(settings.DATA_TEMP_DIR)
        if not os.path.exists(temp_dir):
            return {"deleted_files": 0, "freed_bytes": 0}

        now = time.time()
        deleted_count = 0
        freed_bytes = 0

        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    mtime = os.path.getmtime(file_path)
                    if now - mtime > max_age_seconds:
                        size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_count += 1
                        freed_bytes += size
                except Exception as e:
                    logger.debug(f"Could not remove temporary file {file_path}: {e}")

        logger.info(f"Cleaned {deleted_count} stale temporary files ({freed_bytes} bytes freed)")
        return {"deleted_files": deleted_count, "freed_bytes": freed_bytes}


storage_cleanup_service = StorageCleanupService()
