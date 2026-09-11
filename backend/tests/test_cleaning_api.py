"""
Tests for Cleaning & Transformation Endpoints
Validates API contracts for recommendations, plans, preview, dry-run, and application.
"""

import pytest


@pytest.mark.anyio
async def test_cleaning_api_flow(async_client):
    # 1. Upload dataset with duplicates and missing values
    csv_data = (
        b"id,name,score,category\n"
        b"1, Alice ,90.0,A\n"
        b"2,Bob,85.5,B\n"
        b"3,Charlie,,A\n"
        b"3,Charlie,,A\n"  # Duplicate row!
    )
    files = {"file": ("cleaning_test.csv", csv_data, "text/csv")}
    upload_res = await async_client.post("/api/v1/datasets/upload", files=files)
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["dataset_id"]

    # 2. Get recommendations
    rec_res = await async_client.get(f"/api/v1/cleaning/recommendations/{dataset_id}")
    assert rec_res.status_code == 200
    recommendations = rec_res.json()
    assert isinstance(recommendations, list)

    # 3. Get or update draft plan
    plan_res = await async_client.get(f"/api/v1/cleaning/plan/{dataset_id}")
    assert plan_res.status_code == 200
    plan = plan_res.json()
    assert plan["dataset_id"] == dataset_id

    # Add 2 steps to plan
    steps = [
        {
            "step_id": "step_dedup",
            "type": "DROP_DUPLICATES",
            "parameters": {"keep": "first"},
            "input_columns": [],
            "output_columns": [],
            "description": "Drop duplicate rows",
            "enabled": True,
        },
        {
            "step_id": "step_trim",
            "type": "TRIM_WHITESPACE",
            "parameters": {"column": "name"},
            "input_columns": ["name"],
            "output_columns": ["name"],
            "description": "Trim whitespace in name",
            "enabled": True,
        },
    ]

    update_res = await async_client.post(
        f"/api/v1/cleaning/plan/{dataset_id}",
        json={"steps": steps, "source_version_id": "v1"},
    )
    assert update_res.status_code == 200
    assert len(update_res.json()["steps"]) == 2

    # 4. Preview plan
    prev_res = await async_client.post(
        f"/api/v1/cleaning/preview/{dataset_id}",
        json={"steps": steps, "preview_rows": 5},
    )
    assert prev_res.status_code == 200
    preview_data = prev_res.json()
    assert preview_data["rows_before"] == 4
    assert preview_data["rows_after"] == 3
    assert len(preview_data["validation_errors"]) == 0

    # 5. Dry run
    dry_res = await async_client.post(
        f"/api/v1/cleaning/dry-run/{dataset_id}",
        json={"steps": steps},
    )
    assert dry_res.status_code == 200
    dry_data = dry_res.json()
    assert dry_data["valid"] is True
    assert dry_data["estimated_rows"] == 3

    # 6. Apply plan
    apply_res = await async_client.post(
        f"/api/v1/cleaning/apply/{dataset_id}",
        json={"steps": steps, "version_label": "Deduplicated & Cleaned Names"},
    )
    assert apply_res.status_code == 200
    apply_data = apply_res.json()
    new_version = apply_data["new_version"]
    assert new_version["version_id"] == "v2"
    assert new_version["row_count"] == 3
    assert apply_data["audit"]["rows_affected"] >= 1
    assert "comparison" in apply_data

    # 7. Verify version listing
    versions_res = await async_client.get(f"/api/v1/versions/{dataset_id}")
    assert versions_res.status_code == 200
    versions = versions_res.json()
    assert len(versions) == 2  # v2 and v1

    # 8. Check compare endpoint
    compare_res = await async_client.get(
        f"/api/v1/versions/{dataset_id}/compare?before=v1&after=v2"
    )
    assert compare_res.status_code == 200
    comparison = compare_res.json()
    assert comparison["before_version_id"] == "v1"
    assert comparison["after_version_id"] == "v2"

    # 9. Test version activation (rollback to v1)
    activate_res = await async_client.post(
        f"/api/v1/versions/{dataset_id}/activate/v1"
    )
    assert activate_res.status_code == 200
    assert activate_res.json()["active_version"]["version_id"] == "v1"
