"""
Phase 9 End-to-End Acceptance Test.
Validates the Golden Visualization Flow (Section 70) and criteria VIZ-01 through VIZ-58.
"""

import os
import tempfile
import polars as pl
import pytest

from backend.app.engines.visualization.models import (
    ChartSpec,
    ChartTopNConfig,
    ChartType,
    SortBy,
    SortDirection,
    StructuredFilter,
    VisualizationIntent,
)
from backend.app.engines.visualization.repository import SavedVisualizationRepository
from backend.app.engines.visualization.rules import ColumnContext
from backend.app.services.visualization_service import VisualizationService


def test_phase9_complete_golden_path_acceptance():
    """
    Validates Golden Flow:
    Dataset -> Recommend -> Select -> Validate -> Hydrate Data -> Filter -> Save -> Inspect -> Version Drift
    """
    temp_dir = tempfile.mkdtemp()
    v1_path = os.path.join(temp_dir, "v1.parquet")
    saved_json = os.path.join(temp_dir, "saved.json")

    # 1. Prepare representative analytical dataset
    df = pl.DataFrame({
        "date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"] * 20,
        "region": ["North", "South", "East", "West", "Central"] * 20,
        "segment": ["Enterprise", "SMB"] * 50,
        "revenue": [500.0, 750.0, 1200.0, 300.0, 950.0] * 20,
        "orders": [5, 8, 12, 3, 9] * 20,
    })
    df.write_parquet(v1_path)

    service = VisualizationService()
    service._saved_repo = SavedVisualizationRepository(file_path=saved_json)

    def mock_resolve(dataset_id: str, version_id: str = None):
        return "v1", v1_path

    service._resolve_version_and_path = mock_resolve

    # 2. Recommendations Generation (VIZ-06 - VIZ-17)
    cols = {
        "date": ColumnContext(name="date", physical_type="date", semantic_type="datetime", cardinality=5),
        "region": ColumnContext(name="region", physical_type="string", semantic_type="categorical", cardinality=5),
        "segment": ColumnContext(name="segment", physical_type="string", semantic_type="categorical", cardinality=2),
        "revenue": ColumnContext(name="revenue", physical_type="float64", semantic_type="numeric", cardinality=5),
        "orders": ColumnContext(name="orders", physical_type="int64", semantic_type="numeric", cardinality=5),
    }
    recs = service._recommender.recommend(columns=cols, row_count=100)
    assert len(recs) > 0

    # Ensure temporal recommendation exists for date + revenue
    line_rec = next((r for r in recs if r.chart_type == ChartType.LINE), None)
    assert line_rec is not None
    assert line_rec.x_field == "date"

    # Ensure categorical comparison exists for region + revenue
    bar_rec = next((r for r in recs if r.chart_type == ChartType.BAR and r.x_field == "region"), None)
    assert bar_rec is not None

    # 3. ChartSpec Construction & Validation (VIZ-01, VIZ-02)
    spec = ChartSpec(
        chart_id="gold_chart_1",
        chart_type=ChartType.BAR,
        title="Revenue by Region",
        dataset_id="golden_ds",
        dataset_version_id="v1",
        x="region",
        y="revenue",
        aggregation="sum",
        sort_direction=SortDirection.DESC,
        sort_by=SortBy.VALUE,
        top_n=ChartTopNConfig(n=3, include_other=True, other_label="Other"),
        filters=[
            StructuredFilter(field="revenue", operator="greater_than", value=400.0)
        ],
    )
    val_res = service.validate_chart_spec(spec)
    assert val_res.is_valid is True

    # 4. Server-Side Data Preparation (VIZ-33 - VIZ-36)
    hydrated = service.preview_chart(spec)
    assert len(hydrated.data) <= 4  # Top 3 + 1 Other
    assert any(r.get("x") == "Other" for r in hydrated.data)
    assert hydrated.sampling is not None

    # 5. Save Visualization with Provenance (VIZ-38 - VIZ-40)
    saved = service.save_visualization(
        name="Golden Regional Revenue",
        spec=hydrated,
        description="Golden path verified chart",
    )
    assert saved.visualization_id.startswith("viz_")
    assert saved.dataset_id == "golden_ds"
    assert saved.dataset_version_id == "v1"

    # 6. Retrieve Saved Visualization
    loaded = service.get_saved_visualization(saved.visualization_id)
    assert loaded is not None
    assert loaded.name == "Golden Regional Revenue"
    assert len(loaded.chart_spec.data) > 0

    # 7. Version Isolation Check (VIZ-41)
    v2_path = os.path.join(temp_dir, "v2.parquet")
    df_v2 = pl.DataFrame({
        "date": ["2026-01-01"],
        "territory": ["North"],  # 'region' removed
        "revenue": [500.0],
    })
    df_v2.write_parquet(v2_path)

    def mock_resolve_v2(dataset_id: str, version_id: str = None):
        if version_id == "v2":
            return "v2", v2_path
        return "v1", v1_path

    service._resolve_version_and_path = mock_resolve_v2

    drift_check = service.check_version_compatibility(saved.visualization_id, "v2")
    assert drift_check.is_compatible is False
    assert "region" in drift_check.incompatibility_reason

    # Cleanup
    for f in [v1_path, v2_path, saved_json]:
        if os.path.exists(f):
            os.remove(f)
    try:
        os.rmdir(temp_dir)
    except Exception:
        pass
