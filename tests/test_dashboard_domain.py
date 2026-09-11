"""
Unit tests for Phase 14 Dashboard Domain Models, Provenance, and Repository.
"""

import pytest
from datetime import datetime, timezone
import os

from backend.app.engines.dashboard.models import (
    ComponentPosition,
    ComponentProvenance,
    ComponentSize,
    ComponentSource,
    ComponentType,
    Dashboard,
    DashboardComponent,
    DashboardLayout,
    DashboardTheme,
    DashboardVersion,
    FilterOperator,
    FilterScope,
    RefreshPolicy,
    SourceType,
)
from backend.app.engines.dashboard.repository import (
    DashboardHistoryRepository,
    DashboardRepository,
)


def test_dashboard_model_creation():
    """Verify clean creation and hashing of a Dashboard aggregate."""
    d = Dashboard(
        name="Quarterly Revenue Dashboard",
        description="Core financial and operational metrics",
        dataset_id="ds_12345",
        dataset_version_id="v1",
    )
    assert d.name == "Quarterly Revenue Dashboard"
    assert d.version == 1
    assert d.layout.columns == 12

    h1 = d.compute_hash()
    assert len(h1) == 64  # SHA-256 length

    # Changing a property changes hash
    d.name = "Updated Revenue Dashboard"
    h2 = d.compute_hash()
    assert h1 != h2


def test_dashboard_component_creation_and_bounds():
    """Verify component coordinates and type support."""
    cmp = DashboardComponent(
        dashboard_id="dsh_test",
        type=ComponentType.KPI,
        title="Total Revenue",
        position=ComponentPosition(x=2, y=0),
        size=ComponentSize(width=4, height=3),
        source=ComponentSource(
            source_type=SourceType.SQL_RESULT,
            dataset_id="ds_12345",
            dataset_version_id="v1",
            engine="duckdb",
        ),
        dataset_id="ds_12345",
        dataset_version_id="v1",
    )
    assert cmp.type == ComponentType.KPI
    assert cmp.size.width == 4
    assert cmp.size.height == 3
    assert cmp.position.x == 2


def test_dashboard_repository_crud(tmp_path):
    """Test saving, retrieving, updating, and deleting from repository."""
    file_path = str(tmp_path / "dashboards.json")
    repo = DashboardRepository(file_path=file_path)

    d = Dashboard(
        dashboard_id="dsh_alpha",
        name="Alpha Dashboard",
        dataset_id="ds_1",
        dataset_version_id="v1",
    )
    repo.save(d)

    loaded = repo.get_by_id("dsh_alpha")
    assert loaded is not None
    assert loaded.name == "Alpha Dashboard"
    assert loaded.configuration_hash != ""

    # List & Search
    all_d = repo.get_all(search="alpha")
    assert len(all_d) == 1

    # Delete
    assert repo.delete("dsh_alpha") is True
    assert repo.get_by_id("dsh_alpha") is None


def test_dashboard_history_repository(tmp_path):
    """Test immutable version snapshot persistence."""
    hist_dir = str(tmp_path / "history")
    repo = DashboardHistoryRepository(history_dir=hist_dir)

    d = Dashboard(
        dashboard_id="dsh_beta",
        name="Beta Dashboard",
        dataset_id="ds_1",
        dataset_version_id="v1",
        version=1,
    )

    ver1 = DashboardVersion(
        dashboard_id="dsh_beta",
        version_number=1,
        snapshot=d,
        comment="First version",
    )
    repo.save_version(ver1)

    d.version = 2
    d.name = "Beta Dashboard v2"
    ver2 = DashboardVersion(
        dashboard_id="dsh_beta",
        version_number=2,
        snapshot=d,
        comment="Second version",
    )
    repo.save_version(ver2)

    versions = repo.get_versions("dsh_beta")
    assert len(versions) == 2
    assert versions[0].version_number == 2  # Sorted desc

    fetched_v1 = repo.get_version("dsh_beta", 1)
    assert fetched_v1 is not None
    assert fetched_v1.snapshot.name == "Beta Dashboard"
