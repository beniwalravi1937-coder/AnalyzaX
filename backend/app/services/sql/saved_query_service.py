"""
AnalyzaX — Phase 8: Saved Query Service
Coordinates persistent CRUD management for user-saved analytical queries.
"""

from typing import List, Optional

from backend.app.engines.sql.models import (
    SavedQuery,
    SavedQueryCreateRequest,
    SavedQueryUpdateRequest,
)
from backend.app.engines.sql.saved_queries import saved_queries_repo


class SQLSavedQueryService:
    """
    Coordinates CRUD operations for saved SQL queries.
    """

    def __init__(self) -> None:
        self._repo = saved_queries_repo

    def create(self, req: SavedQueryCreateRequest) -> SavedQuery:
        return self._repo.create(req)

    def get(self, query_id: str) -> Optional[SavedQuery]:
        return self._repo.get(query_id)

    def list(self, dataset_id: Optional[str] = None, tag: Optional[str] = None) -> List[SavedQuery]:
        return self._repo.list(dataset_id=dataset_id, tag=tag)

    def update(self, query_id: str, req: SavedQueryUpdateRequest) -> Optional[SavedQuery]:
        return self._repo.update(query_id, req)

    def delete(self, query_id: str) -> bool:
        return self._repo.delete(query_id)


sql_saved_query_service = SQLSavedQueryService()
