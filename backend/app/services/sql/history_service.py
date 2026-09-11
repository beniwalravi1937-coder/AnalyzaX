"""
AnalyzaX — Phase 8: SQL History Service
Provides query execution history retrieval, search, and clearing.
"""

from typing import List, Optional
from backend.app.engines.sql.history import query_history_repo
from backend.app.engines.sql.models import QueryHistoryEntry


class SQLHistoryService:
    """
    Coordinates access to persisted query execution logs.
    """

    def __init__(self) -> None:
        self._repo = query_history_repo

    def list_history(
        self,
        dataset_id: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
    ) -> List[QueryHistoryEntry]:
        return self._repo.list_entries(
            dataset_id=dataset_id,
            status=status,
            search=search,
            limit=limit,
        )

    def clear_history(self, dataset_id: Optional[str] = None) -> int:
        return self._repo.clear(dataset_id=dataset_id)


sql_history_service = SQLHistoryService()
