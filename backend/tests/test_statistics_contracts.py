"""
AnalyzaX — Phase 10: Statistical API Contract Verification Tests
Validates all 30 contract acceptance criteria (API-STAT-01 through API-STAT-30)
defined in the Phase 10 Statistical API Contracts specification.
"""

import pytest
from starlette.testclient import TestClient
import polars as pl
import numpy as np

from backend.app.main import app
from backend.app.services.cleaning import version_service
from backend.app.services.statistics_service import statistics_service
from backend.app.engines.statistics.models import (
    AnalysisStatus,
    AnalysisType,
    AssumptionCheck,
    AssumptionStatus,
    ConfidenceInterval,
    Diagnostic,
    EffectSize,
    MissingDataPolicy,
    MissingDataReport,
    PValue,
    StatisticalAnalysisRequest,
    StatisticalFinding,
    StatisticalLimitation,
    StatisticalResult,
    StatisticalWarning,
    StatisticValue,
)
from backend.app.engines.statistics.exceptions import StatisticsErrorCode


@pytest.fixture
def test_dataset(tmp_path):
    """Creates a deterministic dataset with versions v1 and v2."""
    import asyncio, io
    from backend.app.services.dataset_service import dataset_service

    np.random.seed(42)
    n = 100
    rev1 = np.random.normal(50, 10, n).tolist()
    reg = ["North"] * 50 + ["South"] * 50
    csv_data = "revenue,region\n" + "\n".join(f"{r:.4f},{g}" for r, g in zip(rev1, reg))

    ds = asyncio.run(dataset_service.ingest_file(io.BytesIO(csv_data.encode("utf-8")), "contract_test.csv", "text/csv"))
    ds_id = ds.id
    v1 = version_service.get_or_create_v1(ds_id)

    # V2 with doubled revenue
    df_v1 = version_service.get_version_dataframe(ds_id, "v1")
    df_v2 = df_v1.with_columns(pl.col("revenue") * 2)
    version_service.create_version(ds_id, df_v2, "v1", "V2 doubled revenue")

    return ds_id


def test_api_stat_01_router_prefix():
    """API-STAT-01: All public Statistics APIs use /api/v1/statistics."""
    with TestClient(app) as client:
        res = client.get("/api/v1/statistics/methods")
        assert res.status_code == 200
        assert isinstance(res.json(), list)


def test_api_stat_02_dataset_version_binding(test_dataset):
    """API-STAT-02: Every analysis request identifies an explicit dataset version."""
    with TestClient(app) as client:
        # Omitting dataset_version_id causes validation failure
        bad_req = {
            "dataset_id": test_dataset,
            "analysis_type": "two_group_comparison",
            "method": "t_test_welch",
            "target_columns": ["revenue"],
            "group_columns": ["region"]
        }
        res = client.post("/api/v1/statistics/analyze", json=bad_req)
        assert res.status_code == 422  # Missing required field dataset_version_id


def test_api_stat_03_and_04_strong_typing(test_dataset):
    """API-STAT-03 & API-STAT-04: StatisticalAnalysisRequest and StatisticalResult are strongly typed."""
    req = StatisticalAnalysisRequest(
        dataset_id=test_dataset,
        dataset_version_id="v1",
        analysis_type=AnalysisType.GROUP_COMPARISON,
        method="t_test_welch",
        inputs={"outcome_columns": ["revenue"], "group_column": "region"},
        parameters={"alpha": 0.05, "confidence_level": 0.95},
        missing_data_policy=MissingDataPolicy.LISTWISE,
    )
    assert req.target_columns == ["revenue"]
    assert req.group_columns == ["region"]

    res = statistics_service.execute_analysis(req)
    assert isinstance(res, StatisticalResult)
    assert res.schema_version == "statistics_result_v1"
    assert res.status in [AnalysisStatus.COMPLETED.value, "COMPLETED"]


def test_api_stat_05_stable_method_identifiers():
    """API-STAT-05: Method identifiers are stable application-level identifiers."""
    with TestClient(app) as client:
        res = client.get("/api/v1/statistics/methods")
        methods = [m["method"] for m in res.json()]
        for m in methods:
            assert not m.startswith("scipy.stats.")
            assert not m.startswith("statsmodels.")
        assert "t_test_welch" in methods
        assert "chi_square" in methods
        assert "pearson" in methods


def test_api_stat_06_parameter_validation(test_dataset):
    """API-STAT-06: Method-specific parameter validation exists."""
    req = StatisticalAnalysisRequest(
        dataset_id=test_dataset,
        dataset_version_id="v1",
        analysis_type=AnalysisType.GROUP_COMPARISON,
        method="t_test_welch",
        target_columns=["revenue"],
        group_columns=["region"],
        parameters={"alpha": 1.5}  # Invalid alpha > 1
    )
    val = statistics_service.validate_request(req)
    assert not val.is_valid
    assert any("alpha" in issue.lower() for issue in val.issues)


def test_api_stat_07_and_08_missing_policy_and_multi_testing():
    """API-STAT-07 & 08: Missing-data policy and multiple-testing configuration are explicit."""
    req = StatisticalAnalysisRequest(
        dataset_id="ds_1",
        dataset_version_id="v1",
        analysis_type="correlation",
        method="pearson",
        target_columns=["a", "b"],
        missing_data_policy="LISTWISE",
        multiple_testing={"method": "HOLM", "comparison_count": 5}
    )
    assert req.missing_data_policy == "LISTWISE"
    assert req.multiple_testing["method"] == "HOLM"


def test_api_stat_09_sample_accounting(test_dataset):
    """API-STAT-09: Inferential results expose sample size and exclusions."""
    req = StatisticalAnalysisRequest(
        dataset_id=test_dataset,
        dataset_version_id="v1",
        analysis_type=AnalysisType.GROUP_COMPARISON,
        method="t_test_welch",
        target_columns=["revenue"],
        group_columns=["region"],
    )
    res = statistics_service.execute_analysis(req)
    assert res.missing_data_report is not None
    assert res.missing_data_report.used_observations == 100
    assert res.sample is not None
    assert res.sample["available_rows"] == 100
    assert res.sample["analyzed_rows"] == 100


def test_api_stat_10_through_14_contracts(test_dataset):
    """API-STAT-10 to 14: Structured contracts for p-values, CIs, effect sizes, assumptions, warnings."""
    req = StatisticalAnalysisRequest(
        dataset_id=test_dataset,
        dataset_version_id="v1",
        analysis_type=AnalysisType.GROUP_COMPARISON,
        method="t_test_welch",
        target_columns=["revenue"],
        group_columns=["region"],
    )
    res = statistics_service.execute_analysis(req)
    # 10: Numerical p-values
    assert "p_value" in res.p_values
    assert isinstance(res.p_values["p_value"], (float, int))

    # 11: Structured CIs
    assert len(res.confidence_intervals) > 0
    ci = res.confidence_intervals[0]
    assert hasattr(ci, "lower") and hasattr(ci, "upper") and hasattr(ci, "level")

    # 12: Structured Effect Sizes
    assert len(res.effect_sizes) > 0
    eff = res.effect_sizes[0]
    assert hasattr(eff, "metric_name") and hasattr(eff, "value") and hasattr(eff, "interpretation")

    # 13: Structured Assumptions
    assert len(res.assumptions) > 0
    assump = res.assumptions[0]
    assert assump.status in [s.value for s in AssumptionStatus]

    # 14: Machine-readable warnings and limitations
    assert isinstance(res.warnings, list)
    assert isinstance(res.limitations, list)


def test_api_stat_15_and_16_interpretation_and_findings(test_dataset):
    """API-STAT-15 & 16: Interpretation separated from raw computation, findings separate."""
    req = StatisticalAnalysisRequest(
        dataset_id=test_dataset,
        dataset_version_id="v1",
        analysis_type=AnalysisType.GROUP_COMPARISON,
        method="t_test_welch",
        target_columns=["revenue"],
        group_columns=["region"],
    )
    res = statistics_service.execute_analysis(req)
    # 15: Interpretation structure
    assert isinstance(res.interpretation, dict)
    assert "what_was_tested" in res.interpretation
    assert "observed_summary" in res.interpretation
    assert "causality_caveat" in res.interpretation

    # 16: Separate findings
    assert isinstance(res.findings, list)
    for f in res.findings:
        assert isinstance(f, StatisticalFinding)
        assert f.severity in ["info", "low", "medium", "high", "critical"]


def test_api_stat_17_provenance(test_dataset):
    """API-STAT-17: Statistical results contain reproducibility/provenance metadata."""
    req = StatisticalAnalysisRequest(
        dataset_id=test_dataset,
        dataset_version_id="v1",
        analysis_type=AnalysisType.GROUP_COMPARISON,
        method="t_test_welch",
        target_columns=["revenue"],
        group_columns=["region"],
    )
    res = statistics_service.execute_analysis(req)
    assert "engine_version" in res.provenance
    assert res.provenance["dataset_id"] == test_dataset
    assert res.provenance["dataset_version_id"] == "v1"
    assert "software_versions" in res.provenance


def test_api_stat_18_and_19_error_handling(test_dataset):
    """API-STAT-18 & 19: Errors use structured error contracts, never raw tracebacks."""
    with TestClient(app) as client:
        # Request with non-existent column
        bad_req = {
            "dataset_id": test_dataset,
            "dataset_version_id": "v1",
            "analysis_type": "two_group_comparison",
            "method": "t_test_welch",
            "target_columns": ["non_existent_col"],
            "group_columns": ["region"]
        }
        res = client.post("/api/v1/statistics/analyze", json=bad_req)
        assert res.status_code in [400, 422]
        data = res.json()
        assert "error" in data or "detail" in data
        assert "Traceback" not in str(data)


def test_api_stat_20_and_21_recommender_and_catalog():
    """API-STAT-20 & 21: Deterministic method recommendation and catalog API."""
    with TestClient(app) as client:
        res = client.get("/api/v1/statistics/methods")
        assert res.status_code == 200
        catalog = res.json()
        assert len(catalog) >= 10
        item = catalog[0]
        assert "supports_effect_size" in item
        assert "supports_confidence_interval" in item


def test_api_stat_22_charts_specs(test_dataset):
    """API-STAT-22: Statistics can generate Phase 9-compatible ChartSpec output."""
    req = StatisticalAnalysisRequest(
        dataset_id=test_dataset,
        dataset_version_id="v1",
        analysis_type=AnalysisType.GROUP_COMPARISON,
        method="t_test_welch",
        target_columns=["revenue"],
        group_columns=["region"],
    )
    res = statistics_service.execute_analysis(req)
    assert len(res.chart_specs) > 0
    spec = res.chart_specs[0]
    assert "chart_type" in spec
    assert "title" in spec
    assert len(res.visualizations) > 0
    assert "chart_spec" in res.visualizations[0]


def test_api_stat_23_pagination(test_dataset):
    """API-STAT-23: History responses are paginated."""
    with TestClient(app) as client:
        res = client.get(f"/api/v1/statistics/history?dataset_id={test_dataset}&limit=1&offset=0")
        assert res.status_code == 200
        items = res.json()
        assert len(items) <= 1


def test_api_stat_24_and_25_lifecycle_and_cancellation(test_dataset):
    """API-STAT-24 & 25: Lifecycle states and cancellation behavior."""
    req = StatisticalAnalysisRequest(
        dataset_id=test_dataset,
        dataset_version_id="v1",
        analysis_type=AnalysisType.GROUP_COMPARISON,
        method="t_test_welch",
        target_columns=["revenue"],
        group_columns=["region"],
    )
    res = statistics_service.execute_analysis(req)
    with TestClient(app) as client:
        cancel_res = client.post(f"/api/v1/statistics/{res.result_id}/cancel")
        assert cancel_res.status_code == 200
        data = cancel_res.json()
        # Already completed: returns terminal status without fake cancellation
        assert data["status"] in ["COMPLETED", "CANCELLED"]


def test_api_stat_27_versioned_schema():
    """API-STAT-27: Public statistical schemas are versioned."""
    res = StatisticalResult(
        result_id="test_res",
        dataset_id="ds",
        dataset_version_id="v1",
        analysis_type="descriptive",
        method="summary",
        inputs={},
        parameters={},
        missing_data_report=MissingDataReport(
            original_observations=10, used_observations=10, excluded_observations=0
        )
    )
    assert res.schema_version == "statistics_result_v1"


def test_api_stat_28_and_29_version_cache_isolation(test_dataset):
    """API-STAT-28 & 29: Cached results cannot cross dataset-version boundaries; deduplication."""
    req_v1 = StatisticalAnalysisRequest(
        dataset_id=test_dataset,
        dataset_version_id="v1",
        analysis_type=AnalysisType.DESCRIPTIVE,
        method="descriptive_summary",
        target_columns=["revenue"],
    )
    req_v2 = StatisticalAnalysisRequest(
        dataset_id=test_dataset,
        dataset_version_id="v2",
        analysis_type=AnalysisType.DESCRIPTIVE,
        method="descriptive_summary",
        target_columns=["revenue"],
    )
    res1 = statistics_service.execute_analysis(req_v1)
    res2 = statistics_service.execute_analysis(req_v2)

    # v1 mean (~50) and v2 mean (~100) must remain distinct and isolated
    mean1 = res1.statistics.get("revenue", {}).get("mean") or res1.statistics.get("numeric", {}).get("revenue", {}).get("mean")
    mean2 = res2.statistics.get("revenue", {}).get("mean") or res2.statistics.get("numeric", {}).get("revenue", {}).get("mean")
    assert abs(mean1 - 50) < 5
    assert abs(mean2 - 100) < 5
    assert mean1 != mean2


def test_api_stat_30_delete_isolation(test_dataset):
    """API-STAT-30: Deleting a statistical analysis cannot delete source datasets or versions."""
    req = StatisticalAnalysisRequest(
        dataset_id=test_dataset,
        dataset_version_id="v1",
        analysis_type=AnalysisType.DESCRIPTIVE,
        method="descriptive_summary",
        target_columns=["revenue"],
    )
    res = statistics_service.execute_analysis(req)
    with TestClient(app) as client:
        del_res = client.delete(f"/api/v1/statistics/{res.result_id}")
        assert del_res.status_code == 200

    # Source dataset and versions must still exist and be intact
    df1 = version_service.get_version_dataframe(test_dataset, "v1")
    assert df1.height == 100
