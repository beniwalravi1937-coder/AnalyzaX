"""
Integration tests for Phase 14 Component Data Hydration and Error Isolation.
"""

import os
import duckdb
import pytest

from backend.app.engines.dashboard.hydration import DashboardHydrator
from backend.app.engines.dashboard.models import (
    ComponentPosition,
    ComponentSize,
    ComponentSource,
    ComponentStatus,
    ComponentType,
    DashboardComponent,
    DashboardFilter,
    FilterOperator,
    SourceType,
)


@pytest.fixture
def sample_parquet(tmp_path):
    """Creates a sample parquet file for testing table and KPI hydration."""
    file_path = str(tmp_path / "test_data.parquet")
    conn = duckdb.connect(":memory:")
    conn.execute("""
        CREATE TABLE sample_sales AS
        SELECT * FROM (VALUES
            (1, 'North', 150.0, '2026-01-01'),
            (2, 'South', 250.0, '2026-01-02'),
            (3, 'North', 300.0, '2026-01-03'),
            (4, 'West',  450.0, '2026-01-04'),
            (5, 'South', 100.0, '2026-01-05')
        ) AS t(id, region, revenue, sale_date)
    """)
    conn.execute(f"COPY sample_sales TO '{file_path}' (FORMAT PARQUET)")
    conn.close()
    return file_path


def test_table_component_hydration_and_filter(sample_parquet):
    """Test table component hydration with active filter and bounds."""
    hydrator = DashboardHydrator()
    cmp = DashboardComponent(
        dashboard_id="dsh_1",
        type=ComponentType.TABLE,
        title="Regional Sales",
        configuration={"limit": 10, "sort_by": "revenue", "sort_dir": "DESC"},
        source=ComponentSource(
            source_type=SourceType.SQL_RESULT,
            dataset_id="ds_1",
            dataset_version_id="v1",
            engine="duckdb",
        ),
        dataset_id="ds_1",
        dataset_version_id="v1",
    )

    # 1. Unfiltered: returns all 5 rows
    resp = hydrator.hydrate_single_component(cmp, sample_parquet, filters=[])
    assert resp.status == ComponentStatus.READY
    assert resp.data["total_rows"] == 5
    assert len(resp.data["rows"]) == 5
    assert resp.data["rows"][0]["revenue"] == 450.0  # sorted DESC

    # 2. Filtered: region = 'North'
    flt = DashboardFilter(field="region", operator=FilterOperator.EQUALS, value="North")
    resp_filtered = hydrator.hydrate_single_component(cmp, sample_parquet, filters=[flt])
    assert resp_filtered.data["total_rows"] == 2
    assert len(resp_filtered.data["rows"]) == 2


def test_kpi_component_hydration(sample_parquet):
    """Test scalar KPI calculation (sum and average) over parquet."""
    hydrator = DashboardHydrator()

    # Sum of revenue
    cmp_sum = DashboardComponent(
        dashboard_id="dsh_1",
        type=ComponentType.KPI,
        title="Total Revenue",
        configuration={"metric": "sum", "column": "revenue"},
        source=ComponentSource(
            source_type=SourceType.SQL_RESULT,
            dataset_id="ds_1",
            dataset_version_id="v1",
            engine="duckdb",
        ),
        dataset_id="ds_1",
        dataset_version_id="v1",
    )
    resp = hydrator.hydrate_single_component(cmp_sum, sample_parquet, filters=[])
    assert resp.data["value"] == 1250.0

    # Filtered sum (North only: 150 + 300 = 450)
    flt = DashboardFilter(field="region", operator=FilterOperator.EQUALS, value="North")
    resp_flt = hydrator.hydrate_single_component(cmp_sum, sample_parquet, filters=[flt])
    assert resp_flt.data["value"] == 450.0


def test_stale_dataset_version_detection(sample_parquet):
    """Test detection of components pointing to older dataset versions."""
    hydrator = DashboardHydrator()
    cmp = DashboardComponent(
        dashboard_id="dsh_1",
        type=ComponentType.TABLE,
        title="Sales Data",
        source=ComponentSource(
            source_type=SourceType.SQL_RESULT,
            dataset_id="ds_1",
            dataset_version_id="v1",
            engine="duckdb",
        ),
        dataset_id="ds_1",
        dataset_version_id="v1",  # Configured on v1
    )

    # Active dataset is now on v2!
    components_map, warnings, stale_count = hydrator.hydrate_dashboard(
        components=[cmp],
        active_dataset_id="ds_1",
        active_version_id="v2",
        global_filters=[],
        parquet_path=sample_parquet,
    )

    assert stale_count == 1
    assert len(warnings) == 1
    cmp_resp = components_map[cmp.component_id]
    assert cmp_resp.is_stale is True
    assert cmp_resp.status == ComponentStatus.STALE_VERSION
    assert "version 'v1', but active version is 'v2'" in cmp_resp.stale_reason


def test_error_isolation_between_components(sample_parquet):
    """
    CRITICAL: A broken component must not crash the entire dashboard.
    """
    hydrator = DashboardHydrator()

    good_cmp = DashboardComponent(
        dashboard_id="dsh_1",
        type=ComponentType.TEXT,
        title="Welcome",
        configuration={"content": "Hello World"},
        source=ComponentSource(source_type=SourceType.MANUAL, dataset_id="ds_1", dataset_version_id="v1"),
        dataset_id="ds_1",
        dataset_version_id="v1",
    )

    bad_cmp = DashboardComponent(
        dashboard_id="dsh_1",
        type=ComponentType.TABLE,
        title="Broken Component",
        # Invalid column to force error
        configuration={"sort_by": "non_existent_column_xyz"},
        source=ComponentSource(source_type=SourceType.SQL_RESULT, dataset_id="ds_1", dataset_version_id="v1"),
        dataset_id="ds_1",
        dataset_version_id="v1",
    )

    components_map, warnings, _ = hydrator.hydrate_dashboard(
        components=[good_cmp, bad_cmp],
        active_dataset_id="ds_1",
        active_version_id="v1",
        global_filters=[],
        parquet_path=sample_parquet,
    )

    # Good component is READY
    assert components_map[good_cmp.component_id].status == ComponentStatus.READY

    # Bad component is ERROR without throwing an unhandled exception
    assert components_map[bad_cmp.component_id].status == ComponentStatus.ERROR
    assert components_map[bad_cmp.component_id].error_message is not None
