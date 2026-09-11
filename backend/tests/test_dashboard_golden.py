"""
Golden Scenario Fixture tests for Phase 14 Dashboard Engine.
Verifies all 12 canonical dashboard archetypes and requirements (DASH-01 through DASH-67).
"""

import pytest
from backend.app.engines.dashboard.hydration import DashboardHydrator
from backend.app.engines.dashboard.models import (
    ComponentPosition,
    ComponentSize,
    ComponentSource,
    ComponentStatus,
    ComponentType,
    Dashboard,
    DashboardComponent,
    DashboardFilter,
    FilterOperator,
    FilterScope,
    RefreshPolicy,
    SourceType,
)


@pytest.fixture
def hydrator():
    return DashboardHydrator()


def test_golden_01_empty_dashboard(hydrator):
    """Fixture 1: Empty dashboard initial state."""
    d = Dashboard(name="Blank Dashboard", dataset_id="ds_1", dataset_version_id="v1")
    assert len(d.components) == 0
    assert len(d.filters) == 0
    assert d.version == 1
    data_map, warnings, stale = hydrator.hydrate_dashboard(d.components, "ds_1", "v1", [])
    assert len(data_map) == 0
    assert stale == 0


def test_golden_02_kpi_dashboard(hydrator):
    """Fixture 2: KPI dashboard with multiple metrics."""
    kpis = [
        DashboardComponent(
            dashboard_id="dsh_kpi",
            type=ComponentType.KPI,
            title="Total Revenue",
            configuration={"value": 1540000, "metric": "sum", "formatting": "currency"},
            source=ComponentSource(source_type=SourceType.SQL_RESULT, dataset_id="ds_1", dataset_version_id="v1"),
            dataset_id="ds_1",
            dataset_version_id="v1",
        ),
        DashboardComponent(
            dashboard_id="dsh_kpi",
            type=ComponentType.KPI,
            title="Active Customers",
            configuration={"value": 1420, "metric": "distinct_count", "formatting": "compact"},
            source=ComponentSource(source_type=SourceType.SQL_RESULT, dataset_id="ds_1", dataset_version_id="v1"),
            dataset_id="ds_1",
            dataset_version_id="v1",
        ),
    ]
    data_map, _, _ = hydrator.hydrate_dashboard(kpis, "ds_1", "v1", [])
    assert len(data_map) == 2
    assert data_map[kpis[0].component_id].data["value"] == 1540000


def test_golden_03_sales_dashboard(hydrator):
    """Fixture 3: Sales breakdown with chart and table."""
    components = [
        DashboardComponent(
            dashboard_id="dsh_sales",
            type=ComponentType.CHART,
            title="Quarterly Sales Trend",
            configuration={"spec": {"chart_type": "line", "title": "Quarterly Trend", "encodings": []}},
            source=ComponentSource(source_type=SourceType.VISUALIZATION, dataset_id="ds_1", dataset_version_id="v1"),
            dataset_id="ds_1",
            dataset_version_id="v1",
        ),
        DashboardComponent(
            dashboard_id="dsh_sales",
            type=ComponentType.TABLE,
            title="Recent Transactions",
            configuration={"limit": 20},
            source=ComponentSource(source_type=SourceType.SQL_RESULT, dataset_id="ds_1", dataset_version_id="v1"),
            dataset_id="ds_1",
            dataset_version_id="v1",
        ),
    ]
    data_map, _, _ = hydrator.hydrate_dashboard(components, "ds_1", "v1", [])
    assert len(data_map) == 2


def test_golden_04_eda_dashboard(hydrator):
    """Fixture 4: EDA findings and quality audit cards."""
    cmp = DashboardComponent(
        dashboard_id="dsh_eda",
        type=ComponentType.EDA_FINDING,
        title="Distribution Anomaly Detected",
        configuration={
            "finding": {
                "title": "Severe Right Skew",
                "severity": "HIGH",
                "description": "Income variable exhibits heavy right skew with kurtosis > 4.5.",
            }
        },
        source=ComponentSource(source_type=SourceType.EDA_RESULT, dataset_id="ds_1", dataset_version_id="v1"),
        dataset_id="ds_1",
        dataset_version_id="v1",
    )
    data_map, _, _ = hydrator.hydrate_dashboard([cmp], "ds_1", "v1", [])
    assert data_map[cmp.component_id].data["title"] == "Severe Right Skew"


def test_golden_05_statistics_dashboard(hydrator):
    """Fixture 5: Hypothesis testing and ANOVA result card."""
    cmp = DashboardComponent(
        dashboard_id="dsh_stat",
        type=ComponentType.STATISTICS,
        title="Regional Conversion Difference",
        configuration={
            "result": {
                "method": "One-Way ANOVA",
                "statistic": 5.84,
                "p_value": 0.003,
                "decision": "Reject Null Hypothesis",
                "interpretation": "Significant variance across regions.",
            }
        },
        source=ComponentSource(source_type=SourceType.STATISTICAL_RESULT, dataset_id="ds_1", dataset_version_id="v1"),
        dataset_id="ds_1",
        dataset_version_id="v1",
    )
    data_map, _, _ = hydrator.hydrate_dashboard([cmp], "ds_1", "v1", [])
    assert data_map[cmp.component_id].data["statistic"] == 5.84


def test_golden_06_ml_dashboard(hydrator):
    """Fixture 6: Machine learning model performance card."""
    cmp = DashboardComponent(
        dashboard_id="dsh_ml",
        type=ComponentType.ML_RESULT,
        title="Churn Prediction Champion",
        configuration={
            "result": {
                "model_name": "GradientBoostingClassifier",
                "primary_metric": "roc_auc",
                "metric_value": 0.932,
                "baseline_lift": "+14.2%",
            }
        },
        source=ComponentSource(source_type=SourceType.ML_RESULT, dataset_id="ds_1", dataset_version_id="v1"),
        dataset_id="ds_1",
        dataset_version_id="v1",
    )
    data_map, _, _ = hydrator.hydrate_dashboard([cmp], "ds_1", "v1", [])
    assert data_map[cmp.component_id].data["primary_metric"] == "roc_auc"


def test_golden_07_forecasting_dashboard(hydrator):
    """Fixture 7: Time-series forecasting horizon card."""
    cmp = DashboardComponent(
        dashboard_id="dsh_fc",
        type=ComponentType.FORECAST,
        title="Q3 Demand Forecast",
        configuration={
            "result": {
                "horizon": 90,
                "model": "AutoARIMA",
                "mape": 3.8,
                "predicted_total": 482000,
            }
        },
        source=ComponentSource(source_type=SourceType.FORECAST_RESULT, dataset_id="ds_1", dataset_version_id="v1"),
        dataset_id="ds_1",
        dataset_version_id="v1",
    )
    data_map, _, _ = hydrator.hydrate_dashboard([cmp], "ds_1", "v1", [])
    assert data_map[cmp.component_id].data["horizon"] == 90


def test_golden_08_mixed_analytical_dashboard(hydrator):
    """Fixture 8: Mixed dashboard combining narrative, KPI, stats, and ML."""
    cmps = [
        DashboardComponent(
            dashboard_id="dsh_mix",
            type=ComponentType.TEXT,
            title="Overview",
            configuration={"content": "### End-to-End Executive Summary"},
            source=ComponentSource(source_type=SourceType.MANUAL, dataset_id="ds_1", dataset_version_id="v1"),
            dataset_id="ds_1",
            dataset_version_id="v1",
        ),
        DashboardComponent(
            dashboard_id="dsh_mix",
            type=ComponentType.KPI,
            title="Total Revenue",
            configuration={"value": 850000},
            source=ComponentSource(source_type=SourceType.SQL_RESULT, dataset_id="ds_1", dataset_version_id="v1"),
            dataset_id="ds_1",
            dataset_version_id="v1",
        ),
        DashboardComponent(
            dashboard_id="dsh_mix",
            type=ComponentType.STATISTICS,
            title="Significance Test",
            configuration={"result": {"p_value": 0.001}},
            source=ComponentSource(source_type=SourceType.STATISTICAL_RESULT, dataset_id="ds_1", dataset_version_id="v1"),
            dataset_id="ds_1",
            dataset_version_id="v1",
        ),
    ]
    data_map, _, _ = hydrator.hydrate_dashboard(cmps, "ds_1", "v1", [])
    assert len(data_map) == 3


def test_golden_09_filtered_dashboard(hydrator):
    """Fixture 9: Filter propagation across compatible components."""
    flt = DashboardFilter(field="category", operator=FilterOperator.EQUALS, value="Furniture")
    cmp_kpi = DashboardComponent(
        dashboard_id="dsh_flt",
        type=ComponentType.KPI,
        title="Filtered Revenue",
        configuration={"value": 120000},
        source=ComponentSource(source_type=SourceType.SQL_RESULT, dataset_id="ds_1", dataset_version_id="v1"),
        dataset_id="ds_1",
        dataset_version_id="v1",
    )
    cmp_stat = DashboardComponent(
        dashboard_id="dsh_flt",
        type=ComponentType.STATISTICS,
        title="Filtered Test",
        configuration={"result": {"p_value": 0.02}},
        source=ComponentSource(source_type=SourceType.STATISTICAL_RESULT, dataset_id="ds_1", dataset_version_id="v1"),
        dataset_id="ds_1",
        dataset_version_id="v1",
    )
    data_map, _, _ = hydrator.hydrate_dashboard([cmp_kpi, cmp_stat], "ds_1", "v1", [flt])
    # Stat component correctly warns about altered population
    assert data_map[cmp_stat.component_id].requires_recomputation is True


def test_golden_10_version_isolated_dashboard(hydrator):
    """Fixture 10: Explicit binding to dataset version v1."""
    d = Dashboard(name="V1 Baseline", dataset_id="ds_1", dataset_version_id="v1")
    assert d.dataset_version_id == "v1"


def test_golden_11_stale_component_dashboard(hydrator):
    """Fixture 11: Stale version detection when dataset upgrades to v2."""
    cmp = DashboardComponent(
        dashboard_id="dsh_stale",
        type=ComponentType.TABLE,
        title="Legacy Data View",
        source=ComponentSource(source_type=SourceType.SQL_RESULT, dataset_id="ds_1", dataset_version_id="v1"),
        dataset_id="ds_1",
        dataset_version_id="v1",
    )
    data_map, warnings, stale_count = hydrator.hydrate_dashboard([cmp], "ds_1", "v2", [])
    assert stale_count == 1
    assert data_map[cmp.component_id].is_stale is True
    assert data_map[cmp.component_id].status == ComponentStatus.STALE_VERSION


def test_golden_12_ai_insight_dashboard(hydrator):
    """Fixture 12: Embedded AI Analyst narrative with verified evidence citations."""
    cmp = DashboardComponent(
        dashboard_id="dsh_ai",
        type=ComponentType.AI_INSIGHT,
        title="AI Executive Analysis",
        configuration={
            "insight": {
                "session_id": "sess_abc123",
                "response_id": "resp_999",
                "summary": "Revenue grew 14% primarily driven by top 3 enterprise tiers.",
                "evidence_references": ["sql_result_441", "eda_correlation_02"],
            }
        },
        source=ComponentSource(source_type=SourceType.AI_ANALYST_RESULT, dataset_id="ds_1", dataset_version_id="v1"),
        dataset_id="ds_1",
        dataset_version_id="v1",
    )
    data_map, _, _ = hydrator.hydrate_dashboard([cmp], "ds_1", "v1", [])
    assert data_map[cmp.component_id].data["session_id"] == "sess_abc123"
    assert len(data_map[cmp.component_id].data["evidence_references"]) == 2
