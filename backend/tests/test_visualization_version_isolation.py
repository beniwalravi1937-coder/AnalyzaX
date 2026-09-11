"""
Phase 9 Golden Test: Visualization Version Isolation & Schema Drift Detection.
Section 71 & Criteria VIZ-05, VIZ-39, VIZ-41, VIZ-61.
"""

import os
import tempfile
import polars as pl
import pytest

from backend.app.engines.visualization.models import (
    ChartSpec,
    ChartType,
    SavedVisualization,
)
from backend.app.engines.visualization.repository import SavedVisualizationRepository
from backend.app.engines.visualization.validation import ChartSpecValidator
from backend.app.services.visualization_service import VisualizationService


def test_version_isolation_and_schema_drift_detection(monkeypatch):
    """
    Golden Test from Section 71:
    V1: date, region, revenue
    V2: date, region, sales_amount (revenue changed/removed)

    A visualization created against V1 must NOT silently adapt to V2.
    It must report INCOMPATIBLE.
    """
    temp_dir = tempfile.mkdtemp()
    v1_path = os.path.join(temp_dir, "v1.parquet")
    v2_path = os.path.join(temp_dir, "v2.parquet")
    saved_json = os.path.join(temp_dir, "saved.json")

    # 1. Create V1 and V2 parquet files
    df_v1 = pl.DataFrame({
        "date": ["2026-01-01", "2026-01-02"],
        "region": ["North", "South"],
        "revenue": [500.0, 700.0],
    })
    df_v1.write_parquet(v1_path)

    df_v2 = pl.DataFrame({
        "date": ["2026-01-01", "2026-01-02"],
        "region": ["North", "South"],
        "sales_amount": [550.0, 750.0],  # revenue renamed/removed
    })
    df_v2.write_parquet(v2_path)

    # 2. Setup service with isolated temp repo and path resolver
    service = VisualizationService()
    service._saved_repo = SavedVisualizationRepository(file_path=saved_json)

    def mock_resolve(dataset_id: str, version_id: str = None):
        if version_id == "v2":
            return "v2", v2_path
        return "v1", v1_path

    monkeypatch.setattr(service, "_resolve_version_and_path", mock_resolve)

    # 3. Create visualization on V1 referencing 'revenue'
    spec_v1 = ChartSpec(
        chart_id="chart_v1_sales",
        chart_type=ChartType.BAR,
        title="Revenue by Region",
        dataset_id="test_ds",
        dataset_version_id="v1",
        x="region",
        y="revenue",
        aggregation="sum",
    )

    saved = service.save_visualization(
        name="V1 Regional Revenue",
        spec=spec_v1,
    )

    assert saved.dataset_version_id == "v1"
    assert saved.chart_spec.y == "revenue"

    # 4. Check compatibility against V2
    compat_res = service.check_version_compatibility(
        visualization_id=saved.visualization_id,
        target_version_id="v2",
    )

    # MUST be incompatible!
    assert compat_res.is_compatible is False
    assert compat_res.is_valid is False
    assert "revenue" in compat_res.incompatibility_reason
    assert any(e.code == "SCHEMA_INCOMPATIBLE" for e in compat_res.errors)

    # Cleanup
    for f in [v1_path, v2_path, saved_json]:
        if os.path.exists(f):
            os.remove(f)
    try:
        os.rmdir(temp_dir)
    except Exception:
        pass
