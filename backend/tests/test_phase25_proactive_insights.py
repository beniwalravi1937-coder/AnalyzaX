"""
AnalyzaX — Phase 25 Test Suite: Proactive Insight Engine.
Validates multi-engine signal detection, importance score ranking,
evidence graphs, and insight status updates.
"""

import shutil
import tempfile
import pytest

from backend.app.engines.insights.detector import InsightSignalDetector
from backend.app.engines.insights.models import (
    Insight,
    InsightSeverity,
    InsightStatus,
    InsightType,
)
from backend.app.engines.insights.ranker import InsightRanker
from backend.app.engines.insights.repository import InsightRepository


@pytest.fixture
def temp_insight_repo():
    temp_dir = tempfile.mkdtemp()
    repo = InsightRepository(storage_dir=temp_dir)
    yield repo
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestProactiveInsightDetector:
    def test_quality_degradation_signal(self):
        quality_data = {
            "quality_score": 62.0,
            "rules": [
                {"name": "null_check", "status": "FAIL", "column": "customer_email", "message": "High null rate (28%)"}
            ],
        }
        insights = InsightSignalDetector.detect_signals_from_context(
            workspace_id="ws_1",
            dataset_id="ds_1",
            version_id="v1",
            quality_data=quality_data,
        )
        assert len(insights) >= 1
        qual_ins = [i for i in insights if i.insight_type == InsightType.DATA_QUALITY][0]
        assert "62.0" in qual_ins.summary
        assert qual_ins.severity in (InsightSeverity.MEDIUM, InsightSeverity.HIGH)
        assert len(qual_ins.evidence) >= 1

    def test_eda_correlation_and_outlier_signals(self):
        eda_data = {
            "correlations": [
                {"col1": "sales", "col2": "advertising_spend", "correlation": 0.89}
            ],
            "outliers": [
                {"column": "revenue", "outlier_count": 45, "percentage": 4.5}
            ],
        }
        insights = InsightSignalDetector.detect_signals_from_context(
            workspace_id="ws_1",
            dataset_id="ds_1",
            version_id="v1",
            eda_data=eda_data,
        )
        corr_ins = [i for i in insights if i.insight_type == InsightType.CORRELATION]
        assert len(corr_ins) >= 1
        assert "sales" in corr_ins[0].affected_columns
        assert "advertising_spend" in corr_ins[0].affected_columns

        outlier_ins = [i for i in insights if i.insight_type == InsightType.ANOMALY]
        assert len(outlier_ins) >= 1
        assert "revenue" in outlier_ins[0].affected_columns

    def test_statistical_signal(self):
        stats_data = {
            "test_name": "Two-sample t-test",
            "p_value": 0.002,
            "is_significant": True,
            "metric": "conversion_rate",
            "groups": ["A", "B"],
        }
        insights = InsightSignalDetector.detect_signals_from_context(
            workspace_id="ws_1",
            dataset_id="ds_1",
            version_id="v1",
            stats_data=stats_data,
        )
        stat_ins = [i for i in insights if i.insight_type == InsightType.STATISTICAL_SIGNAL]
        assert len(stat_ins) >= 1
        assert stat_ins[0].evidence[0].metrics["p_value"] == 0.002


class TestInsightRankerAndRepository:
    def test_ranking_importance_score(self):
        quality_ins = Insight(
            insight_id="i1",
            workspace_id="ws_1",
            dataset_id="ds_1",
            dataset_version_id="v1",
            insight_type=InsightType.DATA_QUALITY,
            title="Quality Degraded",
            summary="Quality score dropped to 40",
            severity=InsightSeverity.CRITICAL,
            affected_columns=["id"],
        )
        ranked = InsightRanker.rank_insight(quality_ins)
        assert ranked.importance_score >= 80.0

    def test_staleness_transition(self, temp_insight_repo):
        ins1 = Insight(
            insight_id="i_v1",
            workspace_id="ws_1",
            dataset_id="ds_1",
            dataset_version_id="v1",
            insight_type=InsightType.ANOMALY,
            title="Anomaly in v1",
            summary="Test anomaly",
            severity=InsightSeverity.HIGH,
            status=InsightStatus.CURRENT,
        )
        temp_insight_repo.save_insight(ins1)

        # Dataset advances to v2 -> mark v1 stale
        updated_count = temp_insight_repo.mark_stale_for_dataset("ds_1", current_version_id="v2")
        assert updated_count == 1

        fetched = temp_insight_repo.get_insight("i_v1")
        assert fetched.status == InsightStatus.STALE
