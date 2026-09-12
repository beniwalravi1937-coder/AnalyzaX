import io
import os
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app

CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "student_exam_performance.csv"))


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_student_exam_performance_full_lifecycle():
    assert os.path.exists(CSV_PATH), f"Target dataset not found at {CSV_PATH}"

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", timeout=180.0
    ) as client:
        # ── 1. DATASET INGESTION & STRUCTURAL VALIDATION ──
        with open(CSV_PATH, "rb") as f:
            file_bytes = f.read()

        upload_resp = await client.post(
            "/api/v1/datasets/upload",
            files={"file": ("student_exam_performance.csv", io.BytesIO(file_bytes), "text/csv")},
        )
        assert upload_resp.status_code == 201, f"Upload failed: {upload_resp.text}"
        upload_data = upload_resp.json()
        dataset_id = upload_data["dataset_id"]
        assert dataset_id.startswith("ds_")
        assert upload_data["status"] == "READY"
        assert upload_data["format"] == "csv"
        assert upload_data["file_size_bytes"] == len(file_bytes)

        # Retrieve dataset metadata
        ds_resp = await client.get(f"/api/v1/datasets/{dataset_id}")
        assert ds_resp.status_code == 200
        ds_meta = ds_resp.json()
        assert ds_meta["id"] == dataset_id
        assert ds_meta["status"] == "READY"

        # ── 2. AUTOMATED PROFILING & SEMANTIC UNDERSTANDING ──
        prof_resp = await client.get(f"/api/v1/datasets/{dataset_id}/profile")
        assert prof_resp.status_code == 200, f"Profiling failed: {prof_resp.text}"
        profile = prof_resp.json()
        assert profile["dataset_id"] == dataset_id
        assert profile["row_count"] == 100000
        assert profile["column_count"] == 44
        assert len(profile["columns"]) == 44

        # Verify key student columns and numeric metrics
        exam_score_col = next(c for c in profile["columns"] if c["name"] == "exam_score")
        assert exam_score_col["numeric_metrics"] is not None
        assert exam_score_col["numeric_metrics"]["min"] >= 0
        assert exam_score_col["numeric_metrics"]["max"] <= 100
        assert exam_score_col["numeric_metrics"]["mean"] > 0

        # Verify target candidates identified by profiling
        targets = profile.get("target_candidates", [])
        assert len(targets) > 0

        # ── 3. DATA QUALITY AUDIT & INTEGRITY VERIFICATION ──
        quality_resp = await client.get(f"/api/v1/datasets/{dataset_id}/quality")
        assert quality_resp.status_code == 200, f"Quality audit failed: {quality_resp.text}"
        quality_data = quality_resp.json()
        assert "overall_score" in quality_data
        assert 0 <= quality_data["overall_score"] <= 100
        assert "dimension_scores" in quality_data
        assert "COMPLETENESS" in quality_data["dimension_scores"]
        assert "VALIDITY" in quality_data["dimension_scores"]
        assert quality_data["total_issues"] >= 0

        # ── 4. DATA CLEANING & DETERMINISTIC TRANSFORMATION ──
        # Fetch cleaning recommendations
        rec_resp = await client.get(f"/api/v1/cleaning/recommendations/{dataset_id}")
        assert rec_resp.status_code == 200, f"Cleaning recommendations failed: {rec_resp.text}"
        recommendations = rec_resp.json()
        assert isinstance(recommendations, list)

        # Formulate a safe cleaning step (trim whitespace on gender column)
        cleaning_steps = [
            {
                "step_id": "step_trim",
                "type": "TRIM_WHITESPACE",
                "parameters": {"column": "gender"},
                "input_columns": ["gender"],
                "output_columns": ["gender"],
                "description": "Trim whitespace in gender column",
                "enabled": True,
            }
        ]

        # Dry run preview
        dry_run_resp = await client.post(
            f"/api/v1/cleaning/dry-run/{dataset_id}",
            json={"steps": cleaning_steps},
        )
        assert dry_run_resp.status_code == 200, f"Dry run failed: {dry_run_resp.text}"
        dry_run_data = dry_run_resp.json()
        assert dry_run_data["valid"] is True
        assert dry_run_data["estimated_rows"] == 100000

        # Apply transformation plan to create an immutable new version
        apply_resp = await client.post(
            f"/api/v1/cleaning/apply/{dataset_id}",
            json={"steps": cleaning_steps, "version_label": "Trimmed Gender Whitespace"},
        )
        assert apply_resp.status_code == 200, f"Apply transformation failed: {apply_resp.text}"
        apply_data = apply_resp.json()
        assert "new_version" in apply_data or "dataset_id" in apply_data

        # ── 5. DETERMINISTIC SQL QUERY ENGINE ──
        # Top 10 students by exam score
        sql_query = (
            "SELECT student_id, gender, attendance_percentage, study_hours_per_day, exam_score "
            "FROM dataset ORDER BY exam_score DESC LIMIT 10;"
        )
        sql_resp = await client.post(
            "/api/v1/sql/query",
            json={"dataset_id": dataset_id, "sql": sql_query},
        )
        assert sql_resp.status_code == 200, f"SQL query failed: {sql_resp.text}"
        sql_data = sql_resp.json()
        assert sql_data["status"] == "COMPLETED"
        assert sql_data["row_count"] == 10
        assert len(sql_data["columns"]) == 5

        # Aggregate SQL query: Average exam score and pass count by family income
        agg_query = (
            "SELECT family_income, count(*) as total_students, "
            "round(avg(exam_score), 2) as avg_score "
            "FROM dataset "
            "WHERE family_income IS NOT NULL "
            "GROUP BY family_income "
            "ORDER BY avg_score DESC;"
        )
        agg_resp = await client.post(
            "/api/v1/sql/query",
            json={"dataset_id": dataset_id, "sql": agg_query},
        )
        assert agg_resp.status_code == 200, f"Agg SQL failed: {agg_resp.text}"
        agg_data = agg_resp.json()
        assert agg_data["status"] == "COMPLETED"
        assert agg_data["row_count"] > 0

        # ── 6. EXPLORATORY DATA ANALYSIS (EDA) ──
        eda_resp = await client.get(f"/api/v1/datasets/{dataset_id}/eda")
        assert eda_resp.status_code == 200, f"EDA failed: {eda_resp.text}"
        eda_data = eda_resp.json()
        assert eda_data["dataset_id"] == dataset_id
        assert "overview" in eda_data
        assert eda_data["overview"]["row_count"] == 100000
        assert "charts" in eda_data
        assert len(eda_data["charts"]) > 0

        # ── 7. MACHINE LEARNING ENGINE ──
        # Suitability check
        suit_resp = await client.post(
            "/api/v1/ml/suitability",
            json={
                "dataset_id": dataset_id,
                "dataset_version_id": "v1",
                "target_column": "exam_score",
                "task_type": "regression",
                "candidate_features": ["study_hours_per_day", "attendance_percentage", "previous_exam_score"],
            },
        )
        assert suit_resp.status_code == 200
        assert suit_resp.json()["is_suitable"] is True

        # Run regression experiment
        reg_resp = await client.post(
            "/api/v1/ml/experiments",
            json={
                "dataset_id": dataset_id,
                "dataset_version_id": "v1",
                "task_type": "regression",
                "target_column": "exam_score",
                "feature_columns": ["study_hours_per_day", "attendance_percentage", "previous_exam_score"],
                "models": ["linear_regression", "ridge"],
                "primary_metric": "rmse",
                "random_seed": 42,
            },
        )
        assert reg_resp.status_code == 200, f"ML experiment failed: {reg_resp.text}"
        reg_data = reg_resp.json()
        assert reg_data["status"] == "COMPLETED"
        assert len(reg_data["model_runs"]) >= 2
        assert reg_data["best_model_run_id"] is not None

        # ── 8. AI ANALYST MULTI-STEP PLAN ──
        plan_resp = await client.post(
            "/api/v1/ai-analyst/plan",
            json={
                "dataset_id": dataset_id,
                "dataset_version_id": "v1",
                "question": "Analyze key factors driving high student exam performance and suggest targeted study recommendations.",
            },
        )
        assert plan_resp.status_code == 200, f"AI Analyst plan failed: {plan_resp.text}"
        plan_data = plan_resp.json()
        assert "steps" in plan_data
        assert len(plan_data["steps"]) > 0

        # ── 9. EXPORTS ENGINE ──
        export_resp = await client.post(
            "/api/v1/exports",
            json={
                "dataset_id": dataset_id,
                "version_id": "v1",
                "source_type": "DATASET",
                "format": "CSV",
            },
        )
        assert export_resp.status_code == 200, f"Export failed: {export_resp.text}"
        export_data = export_resp.json()
        assert export_data["status"] in ("COMPLETED", "PENDING", "PROCESSING")
