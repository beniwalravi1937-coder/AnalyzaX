"""
Tests for ChartSpec Validator and Security Guards.
"""

import pytest
from backend.app.engines.visualization.models import (
    AggregationType,
    ChartSpec,
    ChartType,
    StructuredFilter,
)
from backend.app.engines.visualization.validation import ChartSpecValidator


def test_validator_accepts_clean_spec():
    validator = ChartSpecValidator()
    spec = ChartSpec(
        chart_id="clean_1",
        chart_type=ChartType.BAR,
        title="Revenue by Region",
        dataset_id="ds_1",
        dataset_version_id="v1",
        x="region",
        y="revenue",
        aggregation="sum",
        filters=[
            StructuredFilter(field="revenue", operator="greater_than", value=0)
        ],
    )
    schema = {"region": "string", "revenue": "float64"}
    res = validator.validate(spec, schema_columns=schema)

    assert res.is_valid is True
    assert len(res.errors) == 0
    assert res.is_compatible is True


def test_validator_detects_missing_schema_field():
    validator = ChartSpecValidator()
    spec = ChartSpec(
        chart_id="bad_field",
        chart_type=ChartType.LINE,
        title="Unknown Column",
        dataset_id="ds_1",
        dataset_version_id="v1",
        x="missing_date",
        y="revenue",
    )
    schema = {"region": "string", "revenue": "float64"}
    res = validator.validate(spec, schema_columns=schema)

    assert res.is_valid is False
    assert res.is_compatible is False
    assert any(e.code == "SCHEMA_INCOMPATIBLE" for e in res.errors)


def test_validator_blocks_malicious_filter_payloads():
    validator = ChartSpecValidator()
    spec = ChartSpec(
        chart_id="hack_filter",
        chart_type=ChartType.BAR,
        title="Test",
        dataset_id="ds_1",
        dataset_version_id="v1",
        x="region",
        y="revenue",
        filters=[
            StructuredFilter(
                field="region",
                operator="equals",
                value="North'; DROP TABLE users; --",
            )
        ],
    )
    schema = {"region": "string", "revenue": "float64"}
    res = validator.validate(spec, schema_columns=schema)

    assert res.is_valid is False
    assert any(e.code == "MALICIOUS_FILTER_INPUT" for e in res.errors)


def test_validator_warns_on_non_numeric_aggregation():
    validator = ChartSpecValidator()
    spec = ChartSpec(
        chart_id="agg_warn",
        chart_type=ChartType.BAR,
        title="Test",
        dataset_id="ds_1",
        dataset_version_id="v1",
        x="region",
        y="region_name",
        aggregation="sum",
    )
    schema = {"region": "string", "region_name": "string"}
    res = validator.validate(spec, schema_columns=schema)

    assert any(w.code == "NON_NUMERIC_AGGREGATION" for w in res.warnings)
