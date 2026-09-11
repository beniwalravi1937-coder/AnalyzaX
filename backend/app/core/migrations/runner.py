"""
AnalyzaX — Phase 22: Versioned Database Migration Runner.
Applies forward-compatible, reviewable migrations with exclusive locking,
execution time tracking, and safe rollback semantics.
"""

import importlib
import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.migrations.locking import MigrationLock


class MigrationRecord(BaseModel):
    version: str
    description: str
    applied_at: str
    duration_ms: float
    status: str  # "APPLIED" | "ROLLED_BACK"


class MigrationStatus(BaseModel):
    total_available: int
    total_applied: int
    pending_count: int
    applied: List[MigrationRecord] = Field(default_factory=list)
    pending: List[str] = Field(default_factory=list)


class MigrationRunner:
    """Manages versioned migrations and execution history."""

    def __init__(self) -> None:
        self._migrations_dir = os.path.dirname(__file__)
        self._state_dir = os.path.abspath(os.path.join(settings.DATA_STORAGE_ROOT, "migrations"))
        os.makedirs(self._state_dir, exist_ok=True)
        self._history_file = os.path.join(self._state_dir, "schema_migrations.json")
        self._lock = MigrationLock(lock_dir=self._state_dir)

    def _load_history(self) -> Dict[str, MigrationRecord]:
        if not os.path.exists(self._history_file):
            return {}
        try:
            with open(self._history_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
                return {k: MigrationRecord(**v) for k, v in raw.items()}
        except Exception as e:
            logger.warning(f"Failed to read migration history: {e}")
            return {}

    def _save_history(self, history: Dict[str, MigrationRecord]) -> None:
        temp_file = f"{self._history_file}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump({k: v.model_dump() for k, v in history.items()}, f, indent=2)
        os.replace(temp_file, self._history_file)

    def _discover_migrations(self) -> List[tuple[str, str, Any]]:
        """Finds all versioned migration script modules in numerical order."""
        scripts = []
        for filename in sorted(os.listdir(self._migrations_dir)):
            if filename.startswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")) and filename.endswith(".py"):
                version = filename.split("_")[0]
                desc = filename[len(version) + 1 : -3].replace("_", " ")
                module_name = f"backend.app.core.migrations.{filename[:-3]}"
                try:
                    mod = importlib.import_module(module_name)
                    scripts.append((version, desc, mod))
                except Exception as e:
                    logger.error(f"Failed to import migration script {filename}: {e}")
        return scripts

    def status(self) -> MigrationStatus:
        """Returns the migration status, applied versions, and pending versions."""
        history = self._load_history()
        available = self._discover_migrations()
        applied_records = [r for r in history.values() if r.status == "APPLIED"]
        applied_versions = {r.version for r in applied_records}

        pending_versions = [v for v, _, _ in available if v not in applied_versions]

        return MigrationStatus(
            total_available=len(available),
            total_applied=len(applied_versions),
            pending_count=len(pending_versions),
            applied=applied_records,
            pending=pending_versions,
        )

    def migrate(self) -> List[MigrationRecord]:
        """Applies all pending migrations under an exclusive distributed lock."""
        applied_now: List[MigrationRecord] = []

        with self._lock:
            history = self._load_history()
            available = self._discover_migrations()

            for version, desc, mod in available:
                if version in history and history[version].status == "APPLIED":
                    continue  # Already applied

                logger.info(f"Applying migration [{version}] — {desc}...")
                t0 = time.perf_counter()
                try:
                    # Run migration upgrade hook
                    if hasattr(mod, "upgrade"):
                        mod.upgrade()

                    dur_ms = round((time.perf_counter() - t0) * 1000, 2)
                    rec = MigrationRecord(
                        version=version,
                        description=desc,
                        applied_at=datetime.now(timezone.utc).isoformat(),
                        duration_ms=dur_ms,
                        status="APPLIED",
                    )
                    history[version] = rec
                    applied_now.append(rec)
                    self._save_history(history)
                    logger.info(f"Successfully applied migration [{version}] in {dur_ms}ms")
                except Exception as e:
                    dur_ms = round((time.perf_counter() - t0) * 1000, 2)
                    logger.error(f"Migration [{version}] FAILED: {e}", exc_info=True)
                    raise RuntimeError(f"Migration [{version}] failed: {e}") from e

        return applied_now

    def rollback(self, target_version: str) -> Optional[MigrationRecord]:
        """Rolls back the most recent applied migration if downgrade hook exists."""
        with self._lock:
            history = self._load_history()
            available = {v: (d, m) for v, d, m in self._discover_migrations()}

            if target_version not in history or history[target_version].status != "APPLIED":
                logger.warning(f"Target version [{target_version}] is not applied.")
                return None

            desc, mod = available.get(target_version, (history[target_version].description, None))
            if not mod or not hasattr(mod, "downgrade"):
                raise RuntimeError(f"Migration [{target_version}] does not implement downgrade.")

            logger.info(f"Rolling back migration [{target_version}]...")
            t0 = time.perf_counter()
            mod.downgrade()
            dur_ms = round((time.perf_counter() - t0) * 1000, 2)

            rec = history[target_version]
            rec.status = "ROLLED_BACK"
            self._save_history(history)
            logger.info(f"Successfully rolled back migration [{target_version}] in {dur_ms}ms")
            return rec


migration_runner = MigrationRunner()
