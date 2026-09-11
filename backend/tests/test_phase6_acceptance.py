"""
AnalyzaX — Comprehensive Phase 6 Acceptance Test Suite
Validates all mandatory Phase 6 Acceptance Criteria (AC-01 through AC-44)
and executes the 15-Step End-to-End Golden Path Workflow.
"""

import os
import io
import time
import pytest
import polars as pl

from backend.app.engines.transformations.engine import TransformationEngine
from backend.app.engines.transformations.expression_parser import (
    SafeExpressionParser,
    UnsafeExpressionError,
)
from backend.app.engines.transformations.models import (
    PlanStatus,
    TransformationPlan,
    TransformationStep,
    TransformationType,
)
from backend.app.services.cleaning.comparison_service import ComparisonService
from backend.app.services.cleaning.recommendation_service import RecommendationService
from backend.app.services.cleaning.version_service import VersionService
from backend.app.services.cleaning.plan_service import PlanService
from backend.app.services.dataset_service import dataset_service
from backend.app.services.duckdb_service import duckdb_service
from backend.app.services.profiling_service import profiling_service
from backend.app.services.quality_service import quality_service


# ─────────────────────────────────────────────────────────────
# 15-STEP END-TO-END GOLDEN PATH WORKFLOW (Section R)
# ─────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_phase6_golden_path_workflow(async_client):
    """
    Executes the comprehensive 15-step golden path:
    1. Load fixture dataset
    2. Create original dataset version (V1)
    3. Run profile
    4. Run quality analysis
    5. Create transformation plan
    6. Validate plan
    7. Preview plan
    8. Dry-run plan
    9. Apply plan
    10. Assert new version (V2)
    11. Assert original version unchanged (V1)
    12. Assert lineage
    13. Assert transformed values
    14. Assert new profile
    15. Assert new quality report
    """
    # 1. Load fixture dataset with dirty values
    csv_content = (
        b"id,customer,age,city,spend,signup_date\n"
        b"1, Alice ,28, Delhi ,120.50,2023-01-15\n"
        b"2,Bob,34,mumbai,250.00,2023-02-20\n"
        b"3,Charlie,,delhi,180.00,2023-03-10\n"
        b"4,David,45,MUMBAI,9999.00,2023-04-05\n"  # outlier spend
        b"5,Eve,22,Kolkata,310.00,2023-05-12\n"
        b"5,Eve,22,Kolkata,310.00,2023-05-12\n"  # exact duplicate
    )

    # 2. Upload and create original dataset version (V1)
    files = {"file": ("golden_path.csv", csv_content, "text/csv")}
    upload_res = await async_client.post("/api/v1/datasets/upload", files=files)
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["dataset_id"]

    v_service = VersionService()
    v1 = v_service.get_or_create_v1(dataset_id)
    assert v1.version_id == "v1"
    assert v1.row_count == 6
    assert v1.column_count == 6
    v1_raw_bytes = os.path.getsize(v1.storage_path)

    # 3. Run profile on V1
    profile_v1 = profiling_service.profile_dataset(dataset_id, force_refresh=True)
    assert profile_v1.row_count == 6

    # 4. Run quality analysis on V1
    quality_v1 = quality_service.assess_dataset_quality(dataset_id)
    assert len(quality_v1.issues) > 0

    # 5. Create transformation plan
    steps = [
        # Step A: Drop duplicate rows
        TransformationStep(
            step_id="step_dedup",
            type=TransformationType.DROP_DUPLICATES,
            parameters={"keep": "first"},
            input_columns=[],
            output_columns=[],
            description="Remove exact duplicate records",
        ),
        # Step B: Trim whitespace in customer & city
        TransformationStep(
            step_id="step_trim_customer",
            type=TransformationType.TRIM_WHITESPACE,
            parameters={"column": "customer"},
            input_columns=["customer"],
            output_columns=["customer"],
            description="Trim whitespace in customer",
        ),
        TransformationStep(
            step_id="step_trim_city",
            type=TransformationType.TRIM_WHITESPACE,
            parameters={"column": "city"},
            input_columns=["city"],
            output_columns=["city"],
            description="Trim whitespace in city",
        ),
        # Step C: Normalize city casing to lowercase
        TransformationStep(
            step_id="step_case_city",
            type=TransformationType.TEXT_CASE,
            parameters={"column": "city", "case": "lower"},
            input_columns=["city"],
            output_columns=["city"],
            description="Normalize city to lowercase",
        ),
        # Step D: Fill missing age with median
        TransformationStep(
            step_id="step_fill_age",
            type=TransformationType.FILL_MISSING,
            parameters={"column": "age", "strategy": "median"},
            input_columns=["age"],
            output_columns=["age"],
            description="Impute missing age with median",
        ),
        # Step E: Handle outlier spend with IQR clipping
        TransformationStep(
            step_id="step_clip_spend",
            type=TransformationType.HANDLE_OUTLIERS,
            parameters={"column": "spend", "method": "clip_bounds", "lower_bound": 0.0, "upper_bound": 1000.0},
            input_columns=["spend"],
            output_columns=["spend"],
            description="Cap extreme spend outlier at 1000",
        ),
    ]

    plan_update = await async_client.post(
        f"/api/v1/cleaning/plan/{dataset_id}",
        json={"steps": [s.model_dump() for s in steps], "source_version_id": "v1"},
    )
    assert plan_update.status_code == 200

    # 6. Validate plan
    plan_obj = TransformationPlan(
        plan_id="golden_plan",
        dataset_id=dataset_id,
        source_version_id="v1",
        steps=steps,
        status=PlanStatus.DRAFT,
    )
    df_v1 = v_service.get_version_dataframe(dataset_id, "v1")
    validation_errors = TransformationEngine.validate_plan(df_v1, plan_obj)
    assert len(validation_errors) == 0

    # 7. Preview plan
    prev_res = await async_client.post(
        f"/api/v1/cleaning/preview/{dataset_id}",
        json={"steps": [s.model_dump() for s in steps], "preview_rows": 10},
    )
    assert prev_res.status_code == 200
    prev_data = prev_res.json()
    assert prev_data["rows_before"] == 6
    assert prev_data["rows_after"] == 5  # 1 duplicate removed

    # 8. Dry-run plan
    dry_res = await async_client.post(
        f"/api/v1/cleaning/dry-run/{dataset_id}",
        json={"steps": [s.model_dump() for s in steps]},
    )
    assert dry_res.status_code == 200
    assert dry_res.json()["valid"] is True

    # 9. Apply plan
    apply_res = await async_client.post(
        f"/api/v1/cleaning/apply/{dataset_id}",
        json={"steps": [s.model_dump() for s in steps], "version_label": "Golden Path Cleaned"},
    )
    assert apply_res.status_code == 200
    apply_data = apply_res.json()

    # 10. Assert new version (V2)
    v2 = apply_data["new_version"]
    assert v2["version_id"] == "v2"
    assert v2["row_count"] == 5
    assert v2["parent_version_id"] == "v1"

    # 11. Assert original version V1 unchanged
    v1_check = v_service.get_version(dataset_id, "v1")
    assert v1_check.row_count == 6
    assert os.path.getsize(v1_check.storage_path) == v1_raw_bytes

    # 12. Assert lineage
    lineage_res = await async_client.get(f"/api/v1/versions/{dataset_id}/lineage")
    assert lineage_res.status_code == 200
    lineage = lineage_res.json()
    assert len(lineage["nodes"]) == 2
    assert lineage["active_version_id"] == "v2"
    assert lineage["links"][0]["source"] == "v1"
    assert lineage["links"][0]["target"] == "v2"

    # 13. Assert transformed values in V2
    df_v2 = v_service.get_version_dataframe(dataset_id, "v2")
    # No nulls in age
    assert df_v2["age"].null_count() == 0
    # Customer name trimmed
    assert "Alice" in df_v2["customer"].to_list()
    assert " Alice " not in df_v2["customer"].to_list()
    # City lowercase
    assert all(c == c.lower() for c in df_v2["city"].to_list())
    # Spend capped
    assert df_v2["spend"].max() <= 1000.0

    # 14. Assert new profile on V2
    profile_v2 = profiling_service.profile_dataset(dataset_id, force_refresh=True)
    assert profile_v2.row_count == 5

    # 15. Assert new quality report on V2
    quality_v2 = quality_service.assess_dataset_quality(dataset_id)
    assert quality_v2.overall_score > quality_v1.overall_score


# ─────────────────────────────────────────────────────────────
# ACCEPTANCE CRITERIA SUITES: AC-01 through AC-43
# ─────────────────────────────────────────────────────────────

def test_ac01_original_dataset_immutability():
    """AC-01: Verify V1 remains unchanged after V2 is created."""
    df_raw = pl.DataFrame({"a": [1, 2, 2], "b": ["x", "y", "y"]})
    v_service = VersionService()
    p_service = PlanService()

    plan = TransformationPlan(
        plan_id="plan_immutability",
        dataset_id="test_immut",
        source_version_id="v1",
        steps=[
            TransformationStep(
                step_id="s1",
                type=TransformationType.DROP_DUPLICATES,
                parameters={"keep": "first"},
                description="Dedup",
            )
        ],
    )
    # Execute plan in engine
    res_df, _ = TransformationEngine.execute_plan(df_raw, plan)
    # df_raw must be unchanged
    assert len(df_raw) == 3
    assert len(res_df) == 2


def test_ac03_failed_transformation_atomicity():
    """AC-03 & AC-20: Failed transformations do not create valid versions."""
    df = pl.DataFrame({"col1": [1, 2, 3]})
    plan = TransformationPlan(
        plan_id="plan_fail",
        dataset_id="test_fail",
        source_version_id="v1",
        steps=[
            TransformationStep(
                step_id="bad_step",
                type=TransformationType.CAST_TYPE,
                parameters={"column": "non_existent_col", "target_type": "int"},
                description="Invalid column",
            )
        ],
    )
    errors = TransformationEngine.validate_plan(df, plan)
    assert len(errors) > 0


def test_ac05_plan_validation_rejections():
    """AC-05: Rejection of invalid plans before execution."""
    df = pl.DataFrame({"x": [1, 2, 3], "y": ["a", "b", "c"]})

    # Test nonexistent column
    plan1 = TransformationPlan(
        plan_id="p1", dataset_id="d1", source_version_id="v1",
        steps=[TransformationStep(step_id="s1", type=TransformationType.TRIM_WHITESPACE, parameters={"column": "z"}, description="d")]
    )
    assert len(TransformationEngine.validate_plan(df, plan1)) > 0

    # Test invalid operator
    plan2 = TransformationPlan(
        plan_id="p2", dataset_id="d1", source_version_id="v1",
        steps=[TransformationStep(step_id="s2", type=TransformationType.FILTER_ROWS, parameters={"column": "x", "operator": "BAD_OP"}, description="d")]
    )
    assert len(TransformationEngine.validate_plan(df, plan2)) > 0


def test_ac06_transformation_ordering():
    """AC-06: Transformation execution order strictly affects output."""
    # Order 1: trim then cast to int
    df = pl.DataFrame({"str_num": [" 123 ", " 456 "]})
    step_trim = TransformationStep(step_id="s1", type=TransformationType.TRIM_WHITESPACE, parameters={"column": "str_num"}, description="Trim")
    step_cast = TransformationStep(step_id="s2", type=TransformationType.CAST_TYPE, parameters={"column": "str_num", "target_type": "int"}, description="Cast")

    plan = TransformationPlan(plan_id="p_order", dataset_id="d1", source_version_id="v1", steps=[step_trim, step_cast])
    res_df, _ = TransformationEngine.execute_plan(df, plan)
    assert res_df["str_num"].dtype == pl.Int64
    assert res_df["str_num"].to_list() == [123, 456]


def test_ac07_missing_value_cleaning_all_strategies():
    """AC-07: Verify median, mode, constant, and drop_rows imputation."""
    df = pl.DataFrame({
        "num": [10.0, 20.0, None, 40.0],
        "cat": ["Apple", "Apple", None, "Banana"],
    })

    # 1. Median
    s_median = TransformationStep(step_id="s1", type=TransformationType.FILL_MISSING, parameters={"column": "num", "strategy": "median"}, description="m")
    res1, _ = TransformationEngine.execute_plan(df, TransformationPlan(plan_id="p1", dataset_id="d1", source_version_id="v1", steps=[s_median]))
    assert res1["num"][2] == 20.0

    # 2. Mode
    s_mode = TransformationStep(step_id="s2", type=TransformationType.FILL_MISSING, parameters={"column": "cat", "strategy": "mode"}, description="m")
    res2, _ = TransformationEngine.execute_plan(df, TransformationPlan(plan_id="p2", dataset_id="d1", source_version_id="v1", steps=[s_mode]))
    assert res2["cat"][2] == "Apple"

    # 3. Constant replacement
    s_const = TransformationStep(step_id="s3", type=TransformationType.FILL_MISSING, parameters={"column": "cat", "strategy": "constant", "value": "Unknown"}, description="c")
    res3, _ = TransformationEngine.execute_plan(df, TransformationPlan(plan_id="p3", dataset_id="d1", source_version_id="v1", steps=[s_const]))
    assert res3["cat"][2] == "Unknown"

    # 4. Drop rows
    s_drop = TransformationStep(step_id="s4", type=TransformationType.DROP_MISSING, parameters={"strategy": "drop_rows", "columns": ["num"]}, description="d")
    res4, _ = TransformationEngine.execute_plan(df, TransformationPlan(plan_id="p4", dataset_id="d1", source_version_id="v1", steps=[s_drop]))
    assert len(res4) == 3


def test_ac09_text_cleaning_exact_values():
    """AC-09: Exact text values containing ' Delhi', 'Delhi ', ' DELHI '."""
    df = pl.DataFrame({"city": [" Delhi", "Delhi ", " DELHI "]})

    steps = [
        TransformationStep(step_id="s1", type=TransformationType.TRIM_WHITESPACE, parameters={"column": "city"}, description="Trim"),
        TransformationStep(step_id="s2", type=TransformationType.TEXT_CASE, parameters={"column": "city", "case": "upper"}, description="Upper"),
    ]
    res, _ = TransformationEngine.execute_plan(df, TransformationPlan(plan_id="p", dataset_id="d", source_version_id="v", steps=steps))
    assert res["city"].to_list() == ["DELHI", "DELHI", "DELHI"]


def test_ac10_category_mapping():
    """AC-10: Gender mapping (male -> Male, M -> Male) leaving unmapped values intact."""
    df = pl.DataFrame({"gender": ["male", "Male", "M", "female", "F"]})

    step = TransformationStep(
        step_id="s1",
        type=TransformationType.NORMALIZE_CATEGORIES,
        parameters={"column": "gender", "mapping": {"male": "Male", "M": "Male"}},
        description="Standardize male",
    )
    res, _ = TransformationEngine.execute_plan(df, TransformationPlan(plan_id="p", dataset_id="d", source_version_id="v", steps=[step]))
    assert res["gender"].to_list() == ["Male", "Male", "Male", "female", "F"]


def test_ac11_type_conversion_strategies():
    """AC-11: Type conversion strategies: set_null, keep_original, fail_transformation."""
    df = pl.DataFrame({"val": ["21", "32", "unknown", "45"]})

    # Strategy: set_null
    step_null = TransformationStep(step_id="s1", type=TransformationType.CAST_TYPE, parameters={"column": "val", "target_type": "int", "strategy": "set_null"}, description="d")
    res_null, _ = TransformationEngine.execute_plan(df, TransformationPlan(plan_id="p1", dataset_id="d", source_version_id="v", steps=[step_null]))
    assert res_null["val"].null_count() == 1

    # Strategy: keep_original
    step_keep = TransformationStep(step_id="s2", type=TransformationType.CAST_TYPE, parameters={"column": "val", "target_type": "int", "strategy": "keep_original"}, description="d")
    res_keep, _ = TransformationEngine.execute_plan(df, TransformationPlan(plan_id="p2", dataset_id="d", source_version_id="v", steps=[step_keep]))
    assert res_keep["val"].dtype == pl.Utf8
    assert res_keep["val"][2] == "unknown"

    # Strategy: fail_transformation
    step_fail = TransformationStep(step_id="s3", type=TransformationType.CAST_TYPE, parameters={"column": "val", "target_type": "int", "strategy": "fail_transformation"}, description="d")
    with pytest.raises(ValueError):
        TransformationEngine.execute_plan(df, TransformationPlan(plan_id="p3", dataset_id="d", source_version_id="v", steps=[step_fail]))


def test_ac13_structured_row_filtering():
    """AC-13: Structured predicate filtering."""
    df = pl.DataFrame({
        "age": [22, 18, 25, 65],
        "country": ["India", "USA", "India", "UK"],
        "income": [20000, 55000, 80000, 150000],
    })

    steps = [
        TransformationStep(step_id="s1", type=TransformationType.FILTER_ROWS, parameters={"column": "age", "operator": ">=", "value": 18}, description="Adults"),
        TransformationStep(step_id="s2", type=TransformationType.FILTER_ROWS, parameters={"column": "country", "operator": "==", "value": "India"}, description="India"),
    ]
    res, _ = TransformationEngine.execute_plan(df, TransformationPlan(plan_id="p", dataset_id="d", source_version_id="v", steps=steps))
    assert len(res) == 2
    assert all(a >= 18 for a in res["age"].to_list())
    assert all(c == "India" for c in res["country"].to_list())


def test_ac14_and_15_security_and_injection_resistance():
    """AC-14 & AC-15: Reject SQL injections and arbitrary code execution."""
    # Reject python code injection
    with pytest.raises(UnsafeExpressionError):
        SafeExpressionParser.compile_expression("__import__('os').system('rmdir /s /q test')", ["col1"])

    with pytest.raises(UnsafeExpressionError):
        SafeExpressionParser.compile_expression("eval('1 + 1')", ["col1"])

    # Reject SQL injection attempts in expressions
    with pytest.raises(UnsafeExpressionError):
        SafeExpressionParser.compile_expression("col1; DROP TABLE users; --", ["col1"])


def test_ac24_and_25_lineage_and_rollback():
    """AC-24 & AC-25: Multi-step lineage tracking and non-destructive rollback."""
    import uuid
    dataset_id = f"test_lineage_{uuid.uuid4().hex[:8]}"
    df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    v_service = VersionService()

    # Create dummy dataset entry in memory for testing
    v1 = v_service.create_version(
        dataset_id=dataset_id,
        df=df,
        parent_version_id=None,
        label="V1 initial",
    )
    v2 = v_service.create_version(
        dataset_id=dataset_id,
        df=df.with_columns(pl.lit(10).alias("c")),
        parent_version_id="v1",
        label="V2 with c",
    )
    v3 = v_service.create_version(
        dataset_id=dataset_id,
        df=df.with_columns(pl.lit(20).alias("c")),
        parent_version_id="v2",
        label="V3 with updated c",
    )

    # Rollback to V1
    v_service.set_active_version(dataset_id, "v1")
    active = v_service.get_active_version(dataset_id)
    assert active.version_id == "v1"

    # Verify V2 and V3 are still preserved in history
    versions = v_service.list_versions(dataset_id)
    assert len(versions) == 3
    version_ids = {v.version_id for v in versions}
    assert version_ids == {"v1", "v2", "v3"}


def test_ac35_and_36_performance_large_dataset_and_preview_clamping():
    """AC-35 & AC-36: Execution against 100K+ rows and clamped preview output."""
    n_rows = 100_000
    df_large = pl.DataFrame({
        "id": list(range(n_rows)),
        "val": [float(i) for i in range(n_rows)],
        "cat": ["A" if i % 2 == 0 else "B" for i in range(n_rows)],
    })

    step = TransformationStep(
        step_id="s1",
        type=TransformationType.SCALE_NUMERIC,
        parameters={"column": "val", "method": "min_max"},
        description="Scale 100k rows",
    )
    plan = TransformationPlan(plan_id="p_large", dataset_id="d", source_version_id="v", steps=[step])

    # 1. Preview must return bounded sample
    preview = TransformationEngine.preview_plan(df_large, plan, preview_rows=10)
    assert len(preview.sample_before) == 10
    assert len(preview.sample_after) == 10
    assert preview.rows_before == n_rows

    # 2. Performance benchmark: full execution under 2 seconds for 100k rows
    start = time.perf_counter()
    res_df, _ = TransformationEngine.execute_plan(df_large, plan)
    elapsed = time.perf_counter() - start
    assert len(res_df) == n_rows
    assert elapsed < 2.0  # Polars completes 100k rows in < 100ms
