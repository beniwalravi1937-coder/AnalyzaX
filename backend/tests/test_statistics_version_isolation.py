"""
AnalyzaX — Phase 10: Statistical Dataset Version Isolation Tests
Verifies that statistical analyses are strictly bound to explicit dataset versions (STAT-03, STAT-52, STAT-76).
Analyses on V1 must not leak or execute against V2, and calculations reflect the exact data in that version.
"""

import asyncio
import io
import polars as pl
import pytest
from starlette.testclient import TestClient

from backend.app.engines.statistics.models import StatisticalAnalysisRequest
from backend.app.main import app
from backend.app.services.cleaning import version_service
from backend.app.services.dataset_service import dataset_service
from backend.app.services.statistics_service import statistics_service

client = TestClient(app)


def test_version_isolation_differing_results():
    """
    Creates V1 with specific revenue values, creates V2 with doubled revenue values,
    and runs independent tests on both versions to ensure complete isolation.
    """
    csv_v1 = (
        "region,revenue\n"
        "North,100\n"
        "North,120\n"
        "North,110\n"
        "South,200\n"
        "South,210\n"
        "South,190\n"
    )
    file_obj = io.BytesIO(csv_v1.encode("utf-8"))
    ds = asyncio.run(dataset_service.ingest_file(file_obj, "regional_sales.csv", "text/csv"))
    ds_id = ds.id

    # Initialize V1
    v1 = version_service.get_or_create_v1(ds_id)
    assert v1.version_id == "v1"

    # Create V2 with doubled revenue values
    df_v1 = version_service.get_version_dataframe(ds_id, "v1")
    df_v2 = df_v1.with_columns(pl.col("revenue") * 2)
    v2 = version_service.create_version(
        dataset_id=ds_id,
        df=df_v2,
        parent_version_id="v1",
        label="Doubled Revenue",
    )
    assert v2.version_id == "v2"

    # 1. Run descriptive statistics on V1
    req_v1 = StatisticalAnalysisRequest(
        dataset_id=ds_id,
        dataset_version_id="v1",
        analysis_type="descriptive",
        method="descriptive_summary",
        target_columns=["revenue"],
    )
    res_v1 = statistics_service.execute_analysis(req_v1)
    v1_mean = res_v1.statistics["columns"]["revenue"]["mean"]

    # 2. Run descriptive statistics on V2
    req_v2 = StatisticalAnalysisRequest(
        dataset_id=ds_id,
        dataset_version_id="v2",
        analysis_type="descriptive",
        method="descriptive_summary",
        target_columns=["revenue"],
    )
    res_v2 = statistics_service.execute_analysis(req_v2)
    v2_mean = res_v2.statistics["columns"]["revenue"]["mean"]

    # Assert V1 and V2 are strictly isolated and differ as expected
    assert v1_mean == pytest.approx(155.0, abs=1e-2)
    assert v2_mean == pytest.approx(310.0, abs=1e-2)
    assert v2_mean == pytest.approx(v1_mean * 2.0, abs=1e-2)

    # Assert provenance records retain exact version IDs
    assert res_v1.dataset_version_id == "v1"
    assert res_v2.dataset_version_id == "v2"

    # Re-retrieve V1 analysis from service to verify persistence doesn't overwrite with V2
    retrieved_v1 = statistics_service.get_analysis(res_v1.result_id)
    assert retrieved_v1 is not None
    assert retrieved_v1.dataset_version_id == "v1"
    assert retrieved_v1.statistics["columns"]["revenue"]["mean"] == pytest.approx(155.0, abs=1e-2)
