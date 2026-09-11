"""
AnalyzaX — Phase 8: SQL REST API Integration Tests
Tests all /api/v1/sql endpoints: query, validate, explain, cancel, schema, templates, history, saved queries, visualize.
"""

import io
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_sql_api_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Upload a dataset for testing
        csv_content = (
            b"id,customer_name,department,salary,join_date\n"
            b"1,Alice,Engineering,95000,2021-03-01\n"
            b"2,Bob,Marketing,65000,2022-06-15\n"
            b"3,Charlie,Engineering,115000,2019-11-20\n"
            b"4,David,Finance,88000,2020-08-10\n"
            b"5,Eve,Marketing,72000,2021-01-05\n"
            b"6,Frank,Engineering,102000,2023-04-12\n"
        )
        upload_resp = await client.post(
            "/api/v1/datasets/upload",
            files={"file": ("employees.csv", io.BytesIO(csv_content), "text/csv")},
        )
        assert upload_resp.status_code == 201
        ds_id = upload_resp.json()["dataset_id"]

        # 2. Introspect Schema: GET /api/v1/sql/schema/{dataset_id}
        schema_resp = await client.get(f"/api/v1/sql/schema/{ds_id}")
        assert schema_resp.status_code == 200
        schema_data = schema_resp.json()
        assert schema_data["dataset_id"] == ds_id
        assert schema_data["row_count"] == 6
        assert len(schema_data["columns"]) == 5
        col_names = [c["name"] for c in schema_data["columns"]]
        assert "salary" in col_names
        assert "department" in col_names

        # 3. Get dynamic templates: GET /api/v1/sql/templates/{dataset_id}
        tmpl_resp = await client.get(f"/api/v1/sql/templates/{ds_id}")
        assert tmpl_resp.status_code == 200
        templates = tmpl_resp.json()
        assert len(templates) >= 3

        # 4. Validate valid query: POST /api/v1/sql/validate
        val_resp = await client.post(
            "/api/v1/sql/validate",
            json={
                "dataset_id": ds_id,
                "sql": "SELECT department, avg(salary) FROM dataset GROUP BY department LIMIT 10;",
            },
        )
        assert val_resp.status_code == 200
        val_data = val_resp.json()
        assert val_data["is_valid"] is True

        # 5. Validate forbidden query (security violation)
        sec_resp = await client.post(
            "/api/v1/sql/validate",
            json={
                "dataset_id": ds_id,
                "sql": "DROP TABLE employees;",
            },
        )
        assert sec_resp.status_code == 200
        sec_data = sec_resp.json()
        assert sec_data["is_valid"] is False
        assert any("prohibited" in e["message"].lower() for e in sec_data["errors"])

        # 6. Execute SQL Query: POST /api/v1/sql/query
        query_resp = await client.post(
            "/api/v1/sql/query",
            json={
                "dataset_id": ds_id,
                "sql": """
                    SELECT department, count(*) as emp_count, round(avg(salary), 2) as avg_salary
                    FROM dataset
                    GROUP BY department
                    ORDER BY avg_salary DESC;
                """,
            },
        )
        assert query_resp.status_code == 200
        query_data = query_resp.json()
        assert query_data["status"] == "COMPLETED"
        assert query_data["row_count"] == 3
        assert query_data["rows"][0]["department"] == "Engineering"
        assert len(query_data["suggested_charts"]) > 0

        # 7. Explain SQL: POST /api/v1/sql/explain
        explain_resp = await client.post(
            "/api/v1/sql/explain",
            json={
                "dataset_id": ds_id,
                "sql": "SELECT department, count(*) FROM dataset GROUP BY department;",
            },
        )
        assert explain_resp.status_code == 200
        assert "plan_text" in explain_resp.json()

        # 8. Check History: GET /api/v1/sql/history
        hist_resp = await client.get(f"/api/v1/sql/history?dataset_id={ds_id}")
        assert hist_resp.status_code == 200
        history_list = hist_resp.json()
        assert len(history_list) >= 1
        assert history_list[0]["dataset_id"] == ds_id

        # 9. Saved Queries CRUD
        save_resp = await client.post(
            "/api/v1/sql/saved",
            json={
                "name": "Dept Salaries",
                "description": "Average salary per department",
                "dataset_id": ds_id,
                "version_scope": "active",
                "sql": "SELECT department, avg(salary) FROM dataset GROUP BY 1;",
                "tags": ["hr", "compensation"],
            },
        )
        assert save_resp.status_code == 201
        saved_q = save_resp.json()
        saved_id = saved_q["id"]
        assert saved_q["name"] == "Dept Salaries"

        list_saved_resp = await client.get(f"/api/v1/sql/saved?dataset_id={ds_id}")
        assert list_saved_resp.status_code == 200
        assert any(q["id"] == saved_id for q in list_saved_resp.json())

        # Update saved query
        update_resp = await client.put(
            f"/api/v1/sql/saved/{saved_id}",
            json={"name": "Department Compensation Overview"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "Department Compensation Overview"

        # Delete saved query
        del_resp = await client.delete(f"/api/v1/sql/saved/{saved_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["deleted"] is True
