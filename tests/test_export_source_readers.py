"""
Unit tests for Phase 15 Export Source Readers.
Tests reading datasets, saved SQL results, profiles, and reader factory.
"""

import json
import os
import tempfile
import polars as pl
import pytest

from backend.app.core.config import settings
from backend.app.engines.exports.models import ExportSourceType
from backend.app.engines.exports.source_reader import (
    DatasetSourceReader,
    SqlResultSourceReader,
    ProfileSourceReader,
    get_source_reader,
)


def test_dataset_source_reader():
    reader = DatasetSourceReader()
    with tempfile.TemporaryDirectory() as tmpdir:
        pq_path = os.path.join(tmpdir, "data.parquet")
        df = pl.DataFrame({
            "col_a": [10, 20, 30],
            "col_b": ["apple", "banana", "cherry"],
        })
        df.write_parquet(pq_path)

        source_data = reader.read(
            dataset_id="test_ds",
            version_id="v1",
            parquet_path=pq_path,
        )

        assert source_data.row_count == 3
        assert source_data.columns == ["col_a", "col_b"]
        assert len(source_data.data) == 3
        assert source_data.provenance.dataset_id == "test_ds"
        assert source_data.provenance.source_engine == "dataset"


def test_sql_result_source_reader(monkeypatch):
    reader = SqlResultSourceReader()
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(settings, "DATA_SQL_DIR", tmpdir)

        dataset_id = "ds_sql_test"
        ds_sql_dir = os.path.join(tmpdir, dataset_id)
        os.makedirs(ds_sql_dir, exist_ok=True)

        query_result = {
            "query": "SELECT count(*) FROM my_table",
            "execution_time_ms": 14.5,
            "columns": ["count"],
            "rows": [{"count": 42}],
        }
        with open(os.path.join(ds_sql_dir, "query_1.json"), "w", encoding="utf-8") as f:
            json.dump(query_result, f)

        source_data = reader.read(
            dataset_id=dataset_id,
            version_id="v1",
            source_id="query_1",
        )

        assert source_data.row_count == 1
        assert source_data.data == [{"count": 42}]
        assert source_data.metadata["query"] == "SELECT count(*) FROM my_table"
        assert source_data.provenance.source_engine == "sql"


def test_profile_source_reader(monkeypatch):
    reader = ProfileSourceReader()
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(settings, "DATA_PROFILES_DIR", tmpdir)

        dataset_id = "ds_prof_test"
        ds_prof_dir = os.path.join(tmpdir, dataset_id)
        os.makedirs(ds_prof_dir, exist_ok=True)

        prof_result = {
            "dataset_id": dataset_id,
            "row_count": 500,
            "column_count": 4,
            "columns": [
                {"name": "age", "dtype": "Int64", "null_count": 0},
                {"name": "salary", "dtype": "Float64", "null_count": 5},
            ],
        }
        with open(os.path.join(ds_prof_dir, "v1.json"), "w", encoding="utf-8") as f:
            json.dump(prof_result, f)

        source_data = reader.read(
            dataset_id=dataset_id,
            version_id="v1",
        )

        assert source_data.provenance.source_engine == "profiling"
        assert source_data.row_count == 2
        assert len(source_data.data) == 2


def test_get_source_reader_factory():
    assert isinstance(get_source_reader(ExportSourceType.DATASET), DatasetSourceReader)
    assert isinstance(get_source_reader(ExportSourceType.SQL_RESULT), SqlResultSourceReader)
    assert isinstance(get_source_reader(ExportSourceType.PROFILE), ProfileSourceReader)
