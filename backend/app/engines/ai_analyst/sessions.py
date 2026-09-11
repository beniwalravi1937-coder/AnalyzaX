"""
AI Analyst Engine — Session Persistence & Context Manager (Phase 13)
Persists conversation state, structured context, and provenance references.
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import polars as pl

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.ai_analyst.exceptions import AIAnalystException, AIErrorCode
from backend.app.engines.ai_analyst.models import (
    AnalystMessage,
    AnalystSession,
    DatasetContextSummary,
)
from backend.app.services.cleaning.version_service import VersionService
from backend.app.services.dataset_service import dataset_service


class ContextManager:
    """Extracts compact, bounded metadata from datasets for the AI Analyst context."""

    def __init__(self) -> None:
        self._version_service = VersionService()

    def get_dataset_context(
        self,
        dataset_id: str,
        version_id: Optional[str] = None,
    ) -> DatasetContextSummary:
        dataset = dataset_service.get_dataset(dataset_id)
        if not dataset:
            raise AIAnalystException(
                AIErrorCode.AI_DATASET_CONTEXT_INVALID,
                f"Dataset with ID '{dataset_id}' not found.",
            )

        if not version_id:
            active_ver = self._version_service.get_active_version(dataset_id)
            version_id = active_ver.version_id if active_ver else "v1"

        version = self._version_service.get_version(dataset_id, version_id)
        file_path = version.storage_path if version else None

        row_count, col_count, cols, col_types = 0, 0, [], {}
        numeric_cols, cat_cols, dt_cols = [], [], []
        sample_rows = []

        if file_path and os.path.exists(file_path):
            try:
                df = pl.read_parquet(file_path)
                row_count = df.height
                col_count = df.width
                cols = df.columns
                for col in cols:
                    dtype = df[col].dtype
                    col_types[col] = str(dtype)
                    if dtype.is_numeric():
                        numeric_cols.append(col)
                    elif dtype.is_temporal():
                        dt_cols.append(col)
                    else:
                        cat_cols.append(col)

                # Bounded preview: top 3 rows
                sample_rows = df.head(3).to_dicts()
            except Exception as e:
                logger.warning(f"Failed to read parquet for dataset context: {e}")

        return DatasetContextSummary(
            dataset_id=dataset_id,
            dataset_version_id=version_id,
            dataset_name=dataset.name,
            row_count=row_count,
            column_count=col_count,
            column_names=cols,
            column_types=col_types,
            numeric_columns=numeric_cols,
            categorical_columns=cat_cols,
            datetime_columns=dt_cols,
            sample_preview=sample_rows,
            available_engines=["profile", "quality", "eda", "sql", "statistics", "ml", "forecasting", "visualization"],
        )


class SessionManager:
    """Manages disk persistence and lifecycle of AI Analyst conversation sessions."""

    def __init__(self) -> None:
        self.storage_dir = os.path.abspath(settings.DATA_AI_ANALYST_DIR)
        self.sessions_dir = os.path.join(self.storage_dir, "sessions")
        os.makedirs(self.sessions_dir, exist_ok=True)

    def _get_session_path(self, session_id: str) -> str:
        return os.path.join(self.sessions_dir, f"{session_id}.json")

    def create_session(
        self,
        title: str = "New Analysis",
        dataset_id: Optional[str] = None,
        dataset_version_id: Optional[str] = None,
    ) -> AnalystSession:
        session = AnalystSession(
            title=title,
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
        )
        self.save_session(session)
        return session

    def get_session(self, session_id: str) -> AnalystSession:
        path = self._get_session_path(session_id)
        if not os.path.exists(path):
            raise AIAnalystException(
                AIErrorCode.AI_SESSION_NOT_FOUND,
                f"Session with ID '{session_id}' not found.",
            )
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return AnalystSession(**data)
        except Exception as exc:
            logger.error(f"Failed to load session {session_id}: {exc}")
            raise AIAnalystException(
                AIErrorCode.AI_SESSION_NOT_FOUND,
                f"Failed to read session '{session_id}': {str(exc)}",
            )

    def save_session(self, session: AnalystSession) -> None:
        session.updated_at = datetime.now(timezone.utc).isoformat()
        path = self._get_session_path(session.session_id)
        with open(path, "w", encoding="utf-8") as f:
            f.write(session.model_dump_json(indent=2))

    def list_sessions(self) -> List[AnalystSession]:
        sessions = []
        for fname in os.listdir(self.sessions_dir):
            if fname.endswith(".json"):
                sess_id = fname[:-5]
                try:
                    sess = self.get_session(sess_id)
                    sessions.append(sess)
                except Exception:
                    continue
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        path = self._get_session_path(session_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def append_message(self, session_id: str, message: AnalystMessage) -> AnalystSession:
        session = self.get_session(session_id)
        session.messages.append(message)
        # Update active columns / recent references
        if message.citations:
            session.recent_result_references.extend(message.citations)
            session.recent_result_references = session.recent_result_references[-20:]

        self.save_session(session)
        return session


context_manager = ContextManager()
session_manager = SessionManager()
