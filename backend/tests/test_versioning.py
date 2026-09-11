"""
Tests for Dataset Versioning & Lineage System
Verifies v1 initialization, v2 creation, lineage persistence, and rollback/activation.
"""

import os
import polars as pl
import pytest
from backend.app.services.cleaning.version_service import VersionService
from backend.app.services.dataset_service import DatasetService
from backend.app.services.duckdb_service import duckdb_service


@pytest.fixture
def test_dataset(tmp_path):
    ds_service = DatasetService()
    # Create a small CSV file for ingestion
    csv_content = b"id,val,category\n1,10.5,A\n2,20.0,B\n3,30.2,A\n"
    import io
    file_obj = io.BytesIO(csv_content)
    response = pytest.run(None) if False else None

    # Sync call helper
    import asyncio
    res = asyncio.run(ds_service.ingest_file(file_obj, "version_test.csv", "text/csv"))
    return res


@pytest.mark.anyio
async def test_version_lifecycle(async_client):
    # Ingest a fresh dataset
    csv_data = b"id,val,category\n1,10.5,A\n2,20.0,B\n3,30.2,A\n"
    files = {"file": ("lifecycle_test.csv", csv_data, "text/csv")}
    upload_res = await async_client.post("/api/v1/datasets/upload", files=files)
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["dataset_id"]

    v_service = VersionService()

    # 1. Baseline v1 initialization
    v1 = v_service.get_or_create_v1(dataset_id)
    assert v1.version_id == "v1"
    assert v1.row_count == 3
    assert v1.column_count == 3
    assert os.path.exists(v1.storage_path)

    # Verify DuckDB views
    with duckdb_service.get_connection() as conn:
        count = conn.execute(f"SELECT count(*) FROM dataset_{dataset_id}").fetchone()[0]
        assert count == 3

    # 2. Create v2 with 1 additional column
    df = v_service.get_version_dataframe(dataset_id, "v1")
    df_v2 = df.with_columns((pl.col("val") * 2).alias("val_doubled"))
    v2 = v_service.create_version(
        dataset_id=dataset_id,
        df=df_v2,
        parent_version_id="v1",
        label="Added val_doubled",
        operation_count=1,
    )
    assert v2.version_id == "v2"
    assert v2.parent_version_id == "v1"
    assert v2.column_count == 4
    assert v2.row_count == 3

    # Active version should now be v2
    active = v_service.get_active_version(dataset_id)
    assert active.version_id == "v2"

    # DuckDB main view should now have 4 columns
    with duckdb_service.get_connection() as conn:
        cols = conn.execute(f"DESCRIBE dataset_{dataset_id}").fetchall()
        assert len(cols) == 4

    # 3. Rollback / Activate v1
    v_service.set_active_version(dataset_id, "v1")
    active_after_rollback = v_service.get_active_version(dataset_id)
    assert active_after_rollback.version_id == "v1"

    with duckdb_service.get_connection() as conn:
        cols_after = conn.execute(f"DESCRIBE dataset_{dataset_id}").fetchall()
        assert len(cols_after) == 3

    # 4. Lineage DAG check
    lineage = v_service.get_lineage(dataset_id)
    assert lineage["active_version_id"] == "v1"
    assert len(lineage["nodes"]) == 2
    assert len(lineage["links"]) == 1
    assert lineage["links"][0]["source"] == "v1"
    assert lineage["links"][0]["target"] == "v2"
