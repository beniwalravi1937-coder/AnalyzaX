"""
AnalyzaX — Phase 22: Migration Distributed Lock.
Prevents multiple concurrent deployment instances (e.g., rolling deployments)
from executing database migrations simultaneously.
"""

import os
import time
from typing import Optional

from backend.app.core.config import settings
from backend.app.core.logging import logger

_MIGRATION_LOCK_ID = 884729103  # Fixed advisory lock key for AnalyzaX migrations


class MigrationLock:
    """Manages migration locking via file lock or database advisory lock."""

    def __init__(self, lock_dir: Optional[str] = None) -> None:
        self._lock_dir = os.path.abspath(lock_dir or os.path.join(settings.DATA_STORAGE_ROOT, "migrations"))
        os.makedirs(self._lock_dir, exist_ok=True)
        self._lock_file = os.path.join(self._lock_dir, ".migration.lock")
        self._locked = False

    def acquire(self, timeout_seconds: int = 15) -> bool:
        """Attempts to acquire exclusive migration lock."""
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            try:
                # O_CREAT | O_EXCL ensures atomic acquisition
                fd = os.open(self._lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(fd, "w") as f:
                    f.write(f"pid={os.getpid()};timestamp={time.time()}")
                self._locked = True
                logger.info(f"Acquired migration lock: {self._lock_file}")
                return True
            except FileExistsError:
                # Check if lock file is stale (> 5 minutes)
                try:
                    mtime = os.path.getmtime(self._lock_file)
                    if time.time() - mtime > 300:
                        logger.warning("Detected stale migration lock (> 5m). Releasing stale lock.")
                        os.remove(self._lock_file)
                        continue
                except Exception:
                    pass
                time.sleep(0.5)

        logger.error(f"Failed to acquire migration lock within {timeout_seconds}s timeout.")
        return False

    def release(self) -> None:
        """Releases migration lock."""
        if self._locked and os.path.exists(self._lock_file):
            try:
                os.remove(self._lock_file)
                self._locked = False
                logger.info("Released migration lock.")
            except Exception as e:
                logger.warning(f"Error releasing migration lock: {e}")

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError("Concurrent migration in progress. Migration lock could not be acquired.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
