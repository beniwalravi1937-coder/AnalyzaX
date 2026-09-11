"""
Tests for Phase 8 Query History & Saved Queries Repositories.
"""

import os
import pytest
from backend.app.engines.sql.history import QueryHistoryRepository
from backend.app.engines.sql.models import (
    QueryHistoryEntry,
    QueryStatus,
    SavedQueryCreateRequest,
    SavedQueryUpdateRequest,
)
from backend.app.engines.sql.saved_queries import SavedQueryRepository


@pytest.fixture
def temp_sql_dir(tmp_path):
    d = os.path.join(tmp_path, "sql_test")
    os.makedirs(d, exist_ok=True)
    return str(d)


def test_query_history_flow(temp_sql_dir):
    repo = QueryHistoryRepository(storage_dir=temp_sql_dir)

    entry1 = QueryHistoryEntry(
        query_id="q1",
        dataset_id="ds_alpha",
        version_id="v1",
        query_text="SELECT * FROM dataset LIMIT 10",
        query_hash="hash1",
        status=QueryStatus.COMPLETED,
        execution_time_ms=12.5,
        row_count=10,
    )
    entry2 = QueryHistoryEntry(
        query_id="q2",
        dataset_id="ds_beta",
        version_id="v1",
        query_text="SELECT count(*) FROM orders",
        query_hash="hash2",
        status=QueryStatus.FAILED,
        execution_time_ms=5.0,
        row_count=0,
        error_message="Table not found",
    )

    repo.add_entry(entry1)
    repo.add_entry(entry2)

    all_entries = repo.list_entries()
    assert len(all_entries) == 2
    # Check descending order (most recent first)
    assert all_entries[0].query_id == "q2"

    # Filter by dataset
    alpha_entries = repo.list_entries(dataset_id="ds_alpha")
    assert len(alpha_entries) == 1
    assert alpha_entries[0].query_id == "q1"

    # Search
    search_entries = repo.list_entries(search="orders")
    assert len(search_entries) == 1
    assert search_entries[0].query_id == "q2"

    # Clear specific dataset
    cleared = repo.clear(dataset_id="ds_alpha")
    assert cleared == 1
    assert len(repo.list_entries()) == 1


def test_saved_queries_crud(temp_sql_dir):
    repo = SavedQueryRepository(storage_dir=temp_sql_dir)

    create_req = SavedQueryCreateRequest(
        name="Monthly Revenue Summary",
        description="Aggregates monthly revenue",
        dataset_id="ds_sales",
        version_scope="active",
        sql="SELECT date_trunc('month', sale_date), sum(amount) FROM dataset GROUP BY 1;",
        tags=["reporting", "finance"],
    )

    saved = repo.create(create_req)
    assert saved.id is not None
    assert saved.name == "Monthly Revenue Summary"
    assert len(saved.tags) == 2

    # Get by ID
    fetched = repo.get(saved.id)
    assert fetched is not None
    assert fetched.sql == saved.sql

    # List by dataset & tag
    listed = repo.list(dataset_id="ds_sales", tag="finance")
    assert len(listed) == 1

    # Update
    updated = repo.update(
        saved.id,
        SavedQueryUpdateRequest(name="Updated Monthly Revenue", tags=["finance", "q3"]),
    )
    assert updated.name == "Updated Monthly Revenue"
    assert "q3" in updated.tags

    # Delete
    deleted = repo.delete(saved.id)
    assert deleted is True
    assert repo.get(saved.id) is None
