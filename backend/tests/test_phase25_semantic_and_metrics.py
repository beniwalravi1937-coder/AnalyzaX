"""
AnalyzaX — Phase 25 Test Suite: Governed Metrics & Semantic Intelligence.
Validates AST formula parsing, allowlisted functions, injection defense,
circular dependency detection, DuckDB preview calculation, and metric versioning.
"""

import os
import shutil
import tempfile
import polars as pl
import pytest

from backend.app.engines.semantic.engine import SemanticEngine
from backend.app.engines.semantic.expression import MetricExpressionValidator
from backend.app.engines.semantic.models import (
    AggregationType,
    MetricDefinition,
    MetricStatus,
)
from backend.app.engines.semantic.repository import SemanticRepository
from backend.app.services.semantic_service import SemanticService


@pytest.fixture
def temp_semantic_repo():
    temp_dir = tempfile.mkdtemp()
    repo = SemanticRepository(storage_dir=temp_dir)
    yield repo
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_parquet_path():
    temp_dir = tempfile.mkdtemp()
    parquet_path = os.path.join(temp_dir, "test_dataset.parquet")
    df = pl.DataFrame({
        "revenue": [100.0, 200.0, 300.0, 400.0],
        "cost": [40.0, 60.0, 80.0, 100.0],
        "region": ["North", "North", "South", "South"],
    })
    df.write_parquet(parquet_path)
    yield parquet_path
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestMetricExpressionValidator:
    def test_valid_formula(self):
        res = MetricExpressionValidator.validate_expression("SUM(revenue) - SUM(cost)")
        assert res.is_valid is True
        assert "revenue" in res.parsed_columns
        assert "cost" in res.parsed_columns
        assert "SUM" in res.parsed_functions

    def test_forbidden_function_or_sql_injection(self):
        res = MetricExpressionValidator.validate_expression("SUM(revenue); DROP TABLE users;")
        assert res.is_valid is False
        assert "forbidden" in res.error_message.lower() or "syntax" in res.error_message.lower()

    def test_eval_or_exec_forbidden(self):
        res = MetricExpressionValidator.validate_expression("eval('__import__(\"os\").system(\"calc\")')")
        assert res.is_valid is False
        assert "forbidden" in res.error_message.lower()

    def test_column_validation_against_schema(self):
        res = MetricExpressionValidator.validate_expression(
            expression="SUM(revenue) + AVG(unknown_column)",
            available_columns=["revenue", "cost"],
        )
        assert res.is_valid is False
        assert "unknown_column" in res.error_message

    def test_circular_dependency_detection(self):
        # A depends on B, B depends on C, C depends on A
        existing_graph = {
            "metric_b": ["metric_c"],
            "metric_c": ["metric_a"],
        }
        res = MetricExpressionValidator.validate_expression(
            expression="metric_b * 1.1",
            existing_metrics=existing_graph,
            current_metric_name="metric_a",
        )
        assert res.is_valid is False
        assert "circular dependency" in res.error_message.lower()


class TestSemanticServiceAndCalculation:
    def test_metric_lifecycle_and_versioning(self, temp_semantic_repo):
        service = SemanticService()
        service.create_metric = lambda **kwargs: temp_semantic_repo.save_metric(
            MetricDefinition(
                metric_id="metric_rev",
                workspace_id="ws_1",
                name="Revenue",
                expression="SUM(revenue)",
                owner_id="user_1",
            ),
            changed_by="user_1",
            change_summary="Initial creation",
        )

        m = service.create_metric()
        assert m.version == 1
        assert m.name == "Revenue"

        # Update metric to create version 2
        m.expression = "SUM(revenue) * 1.05"
        m2 = temp_semantic_repo.save_metric(m, changed_by="user_2", change_summary="Tax adjustment")
        assert m2.version == 2

        # Check version history
        history = temp_semantic_repo.get_version_history("metric_rev")
        assert len(history) == 2
        assert history[0].version == 1
        assert history[1].version == 2
        assert "Tax adjustment" in history[1].change_summary

    def test_deterministic_preview_calculation(self, sample_parquet_path):
        metric = MetricDefinition(
            metric_id="m1",
            workspace_id="ws_1",
            name="Gross Profit",
            expression="SUM(revenue) - SUM(cost)",
            owner_id="u1",
        )
        calc_result = SemanticEngine.calculate_metric(
            metric=metric,
            dataset_path=sample_parquet_path,
        )
        # Total revenue = 1000, Total cost = 280 -> Profit = 720
        assert calc_result.value == 720.0
        assert calc_result.row_count >= 1

    def test_term_resolution_and_ambiguity(self):
        metrics = [
            MetricDefinition(
                metric_id="m_gross_margin",
                workspace_id="ws_1",
                name="Gross Margin",
                expression="SUM(profit) / SUM(revenue)",
                synonyms=["margin", "gross profit margin"],
                owner_id="u1",
            ),
            MetricDefinition(
                metric_id="m_net_margin",
                workspace_id="ws_1",
                name="Net Margin",
                expression="SUM(net_income) / SUM(revenue)",
                synonyms=["margin", "net profit margin"],
                owner_id="u1",
            ),
        ]

        # Ambiguity check when user says "margin"
        ambiguous = SemanticEngine.detect_ambiguity("show me the margin", metrics)
        assert len(ambiguous) == 2
        names = [m.name for m in ambiguous]
        assert "Gross Margin" in names
        assert "Net Margin" in names
