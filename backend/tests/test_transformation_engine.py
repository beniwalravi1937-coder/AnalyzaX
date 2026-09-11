"""
Tests for Transformation Engine & Concrete Transformers
Validates execution, preview, and error boundaries across all transformation types.
"""

import pytest
import polars as pl
from backend.app.engines.transformations.engine import TransformationEngine
from backend.app.engines.transformations.models import (
    TransformationPlan,
    TransformationStep,
    TransformationType,
)


@pytest.fixture
def sample_df():
    return pl.DataFrame({
        "id": [1, 2, 3, 4, 4],
        "name": [" Alice ", "bob", "Charlie", None, "Charlie"],
        "category": ["A", "b", "A", "c", "A"],
        "price": [10.0, 20.0, None, 40.0, 1000.0],
        "quantity": [1, 2, 3, 4, 5],
        "date_str": ["2023-01-01", "2023-02-15", "2023-03-30", "2023-04-10", "2023-05-20"],
    })


def test_missing_value_transformers(sample_df):
    # Fill missing with median
    step_fill = TransformationStep(
        step_id="s1",
        type=TransformationType.FILL_MISSING,
        parameters={"column": "price", "strategy": "median"},
        description="Fill missing price with median",
    )
    plan = TransformationPlan(
        plan_id="p1",
        dataset_id="d1",
        source_version_id="v1",
        steps=[step_fill],
    )
    res_df, summaries = TransformationEngine.execute_plan(sample_df, plan)
    assert res_df["price"].null_count() == 0
    # Median of [10, 20, 40, 1000] is 30.0
    assert res_df["price"][2] == 30.0

    # Drop missing rows
    step_drop = TransformationStep(
        step_id="s2",
        type=TransformationType.DROP_MISSING,
        parameters={"strategy": "drop_rows", "columns": ["name"]},
        description="Drop rows where name is null",
    )
    plan_drop = TransformationPlan(
        plan_id="p2",
        dataset_id="d1",
        source_version_id="v1",
        steps=[step_drop],
    )
    res_drop, _ = TransformationEngine.execute_plan(sample_df, plan_drop)
    assert len(res_drop) == 4
    assert res_drop["name"].null_count() == 0


def test_duplicates_transformer(sample_df):
    step = TransformationStep(
        step_id="s1",
        type=TransformationType.DROP_DUPLICATES,
        parameters={"keep": "first"},
        description="Drop duplicate rows",
    )
    plan = TransformationPlan(plan_id="p1", dataset_id="d1", source_version_id="v1", steps=[step])
    res_df, summaries = TransformationEngine.execute_plan(sample_df, plan)
    # The last row has id 4 and name Charlie, which is not identical across all columns to previous rows
    # Let's test subset deduplication on ["id"]
    step_subset = TransformationStep(
        step_id="s2",
        type=TransformationType.DROP_DUPLICATES,
        parameters={"keep": "first", "columns": ["id"]},
        description="Drop duplicate ids",
    )
    res_subset, summaries = TransformationEngine.execute_plan(sample_df, TransformationPlan(plan_id="p2", dataset_id="d1", source_version_id="v1", steps=[step_subset]))
    assert len(res_subset) == 4


def test_text_and_category_transformers(sample_df):
    steps = [
        TransformationStep(
            step_id="s1",
            type=TransformationType.TRIM_WHITESPACE,
            parameters={"column": "name"},
            description="Trim whitespace in name",
        ),
        TransformationStep(
            step_id="s2",
            type=TransformationType.TEXT_CASE,
            parameters={"column": "category", "case": "upper"},
            description="Uppercase category",
        ),
        TransformationStep(
            step_id="s3",
            type=TransformationType.NORMALIZE_CATEGORIES,
            parameters={"column": "category", "mapping": {"B": "BETA"}},
            description="Normalize category B to BETA",
        ),
    ]
    plan = TransformationPlan(plan_id="p_text", dataset_id="d1", source_version_id="v1", steps=steps)
    res_df, _ = TransformationEngine.execute_plan(sample_df, plan)
    assert res_df["name"][0] == "Alice"
    assert "BETA" in res_df["category"].to_list()


def test_column_operations(sample_df):
    steps = [
        TransformationStep(
            step_id="s1",
            type=TransformationType.RENAME_COLUMN,
            parameters={"mapping": {"date_str": "created_date"}},
            description="Rename column",
        ),
        TransformationStep(
            step_id="s2",
            type=TransformationType.DROP_COLUMNS,
            parameters={"columns": ["quantity"]},
            description="Drop quantity column",
        ),
    ]
    plan = TransformationPlan(plan_id="p_cols", dataset_id="d1", source_version_id="v1", steps=steps)
    res_df, _ = TransformationEngine.execute_plan(sample_df, plan)
    assert "created_date" in res_df.columns
    assert "date_str" not in res_df.columns
    assert "quantity" not in res_df.columns


def test_derived_column_and_scaling(sample_df):
    steps = [
        TransformationStep(
            step_id="s1",
            type=TransformationType.DERIVED_COLUMN,
            parameters={"new_column": "total_val", "expression": "id * quantity"},
            description="Calculate total value",
        ),
        TransformationStep(
            step_id="s2",
            type=TransformationType.SCALE_NUMERIC,
            parameters={"column": "quantity", "method": "min_max"},
            description="MinMax scale quantity",
        ),
        TransformationStep(
            step_id="s3",
            type=TransformationType.HANDLE_OUTLIERS,
            parameters={"column": "price", "method": "clip_bounds", "lower_bound": 0.0, "upper_bound": 100.0},
            description="Clip price outlier",
        ),
    ]
    plan = TransformationPlan(plan_id="p_math", dataset_id="d1", source_version_id="v1", steps=steps)
    res_df, _ = TransformationEngine.execute_plan(sample_df, plan)
    assert "total_val" in res_df.columns
    assert res_df["total_val"][0] == 1  # 1 * 1
    assert res_df["quantity"].min() == 0.0
    assert res_df["quantity"].max() == 1.0
    # Price 1000.0 should be clipped to 100.0
    assert res_df["price"].max() == 100.0


def test_filter_rows(sample_df):
    step = TransformationStep(
        step_id="s1",
        type=TransformationType.FILTER_ROWS,
        parameters={"column": "id", "operator": ">=", "value": 3},
        description="Filter id >= 3",
    )
    plan = TransformationPlan(plan_id="p_filter", dataset_id="d1", source_version_id="v1", steps=[step])
    res_df, summaries = TransformationEngine.execute_plan(sample_df, plan)
    assert len(res_df) == 3
    assert res_df["id"].min() == 3


def test_encoding_transformers(sample_df):
    step = TransformationStep(
        step_id="s1",
        type=TransformationType.ONE_HOT_ENCODE,
        parameters={"column": "category", "drop_original": True},
        description="One-hot encode category",
    )
    plan = TransformationPlan(plan_id="p_encode", dataset_id="d1", source_version_id="v1", steps=[step])
    res_df, _ = TransformationEngine.execute_plan(sample_df, plan)
    assert "category" not in res_df.columns
    assert "category_a" in res_df.columns


def test_plan_preview(sample_df):
    step = TransformationStep(
        step_id="s1",
        type=TransformationType.FILTER_ROWS,
        parameters={"column": "id", "operator": "<=", "value": 3},
        description="Filter id <= 3",
    )
    plan = TransformationPlan(plan_id="p_prev", dataset_id="d1", source_version_id="v1", steps=[step])
    preview = TransformationEngine.preview_plan(sample_df, plan, preview_rows=5)
    assert preview.rows_before == 5
    assert preview.rows_after == 3
    assert len(preview.sample_before) == 5
    assert len(preview.sample_after) == 3
    assert len(preview.validation_errors) == 0
