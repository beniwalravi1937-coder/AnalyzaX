"""
Tests for server-side Visualization Data Preparer.
"""

import os
import tempfile
import polars as pl
import pytest

from backend.app.engines.visualization.data_preparer import VisualizationDataPreparer
from backend.app.engines.visualization.models import (
    ChartSpec,
    ChartTopNConfig,
    ChartType,
    SortBy,
    SortDirection,
    StructuredFilter,
)


@pytest.fixture
def sample_parquet():
    df = pl.DataFrame({
        "region": ["North", "North", "South", "East", "West", "Central", "North", "South"],
        "category": ["A", "B", "A", "B", "C", "A", "B", "C"],
        "revenue": [100.0, 150.0, 200.0, 300.0, 50.0, 75.0, 120.0, 180.0],
        "units": [10, 15, 20, 30, 5, 8, 12, 18],
    })
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, "test_data.parquet")
    df.write_parquet(file_path)
    yield file_path
    try:
        os.remove(file_path)
        os.rmdir(temp_dir)
    except Exception:
        pass


def test_prepare_aggregated_bar_chart(sample_parquet):
    preparer = VisualizationDataPreparer()
    spec = ChartSpec(
        chart_id="prep_bar_1",
        chart_type=ChartType.BAR,
        title="Revenue by Region",
        dataset_id="test_ds",
        dataset_version_id="v1",
        x="region",
        y="revenue",
        aggregation="sum",
        sort_direction=SortDirection.DESC,
    )

    hydrated = preparer.prepare_data(sample_parquet, spec)

    assert len(hydrated.data) > 0
    # North should have 100 + 150 + 120 = 370
    north_row = next((r for r in hydrated.data if r.get("x") == "North"), None)
    assert north_row is not None
    assert north_row.get("y") == 370.0

    # Ensure sorted desc
    y_vals = [r.get("y") for r in hydrated.data]
    assert y_vals == sorted(y_vals, reverse=True)


def test_prepare_with_structured_filter(sample_parquet):
    preparer = VisualizationDataPreparer()
    spec = ChartSpec(
        chart_id="prep_filt_1",
        chart_type=ChartType.BAR,
        title="Filtered Revenue",
        dataset_id="test_ds",
        dataset_version_id="v1",
        x="region",
        y="revenue",
        aggregation="sum",
        filters=[
            StructuredFilter(field="revenue", operator="greater_than", value=150.0)
        ],
    )

    hydrated = preparer.prepare_data(sample_parquet, spec)
    # Only records with revenue > 150 (South: 200, 180; East: 300) should be included
    regions = [r.get("x") for r in hydrated.data]
    assert "West" not in regions
    assert "Central" not in regions


def test_prepare_top_n_with_other(sample_parquet):
    preparer = VisualizationDataPreparer()
    spec = ChartSpec(
        chart_id="prep_topn_1",
        chart_type=ChartType.BAR,
        title="Top 2 Regions",
        dataset_id="test_ds",
        dataset_version_id="v1",
        x="region",
        y="revenue",
        aggregation="sum",
        top_n=ChartTopNConfig(n=2, include_other=True, other_label="Other Regions"),
    )

    hydrated = preparer.prepare_data(sample_parquet, spec)
    assert len(hydrated.data) <= 3  # 2 top + 1 Other
    other_row = next((r for r in hydrated.data if r.get("x") == "Other Regions"), None)
    assert other_row is not None
    assert other_row.get("y") > 0


def test_prepare_histogram_bins(sample_parquet):
    preparer = VisualizationDataPreparer()
    spec = ChartSpec(
        chart_id="prep_hist_1",
        chart_type=ChartType.HISTOGRAM,
        title="Revenue Distribution",
        dataset_id="test_ds",
        dataset_version_id="v1",
        x="revenue",
    )

    hydrated = preparer.prepare_data(sample_parquet, spec)
    assert len(hydrated.data) == 20  # 20 histogram bins
    total_count = sum(b.get("count", 0) for b in hydrated.data)
    assert total_count == 8  # 8 input rows
