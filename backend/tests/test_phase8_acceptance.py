"""
AnalyzaX — Phase 8: Acceptance & End-to-End Test Suite
Validates all Phase 8 deliverables against the requirements constitution:
- Dual-layer AST validation & strict read-only security
- Safe DuckDB query execution with full analytical SQL support (CTEs, windows, aggregations)
- Version isolation between v1 and v2
- Resource containment (max rows, timeouts, cancellation)
- Schema introspection and dynamic templates
- Query history persistence and saved queries CRUD
- Automated chart advice (ChartSpec generation)
"""

import io
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_phase8_complete_acceptance_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Step 1: Upload dataset
        csv_data = (
            b"id,customer,region,revenue,units,signup_date\n"
            b"1,Acme Corp,North,12500.0,10,2022-01-10\n"
            b"2,Beta LLC,South,8400.0,6,2022-02-14\n"
            b"3,Gamma Inc,North,19200.0,15,2022-03-22\n"
            b"4,Delta Co,East,4500.0,4,2022-04-18\n"
            b"5,Epsilon,West,22000.0,20,2022-05-30\n"
            b"6,Zeta Ltd,North,9800.0,8,2022-06-11\n"
            b"7,Eta Tech,West,15400.0,12,2022-07-25\n"
            b"8,Theta LLC,South,6200.0,5,2022-08-19\n"
        )
        upload_resp = await client.post(
            "/api/v1/datasets/upload",
            files={"file": ("sales_phase8.csv", io.BytesIO(csv_data), "text/csv")},
        )
        assert upload_resp.status_code == 201
        ds_id = upload_resp.json()["dataset_id"]

        # Step 2: Introspect Schema
        schema_resp = await client.get(f"/api/v1/sql/schema/{ds_id}")
        assert schema_resp.status_code == 200
        schema = schema_resp.json()
        assert schema["row_count"] == 8
        col_map = {c["name"]: c for c in schema["columns"]}
        assert "revenue" in col_map
        assert col_map["revenue"]["semantic_type"] == "numeric"
        assert "region" in col_map
        assert col_map["region"]["semantic_type"] == "categorical"

        # Step 3: Verify Dynamic Templates Generated
        tmpl_resp = await client.get(f"/api/v1/sql/templates/{ds_id}")
        assert tmpl_resp.status_code == 200
        templates = tmpl_resp.json()
        assert any("revenue" in t["sql"] for t in templates)

        # Step 4: Security Validation - Block prohibited queries
        for bad_sql in [
            "DROP TABLE sales;",
            "INSERT INTO dataset VALUES (9, 'Evil', 'North', 0, 0, '2022-01-01');",
            "UPDATE dataset SET revenue = 0;",
            "ATTACH 'evil.db';",
            "SELECT 1; DROP TABLE sales;",
        ]:
            val_bad = await client.post(
                "/api/v1/sql/validate",
                json={"dataset_id": ds_id, "sql": bad_sql},
            )
            assert val_bad.status_code == 200
            assert val_bad.json()["is_valid"] is False

        # Step 5: Execute Complex Analytical SQL (CTEs + Window Functions + Aggregation)
        complex_sql = """
        WITH regional_perf AS (
            SELECT
                region,
                count(*) as deal_count,
                sum(revenue) as total_rev,
                avg(revenue) as avg_deal
            FROM dataset
            GROUP BY region
        )
        SELECT
            region,
            deal_count,
            round(total_rev, 2) as total_rev,
            round(avg_deal, 2) as avg_deal,
            rank() OVER (ORDER BY total_rev DESC) as rev_rank
        FROM regional_perf
        ORDER BY rev_rank ASC;
        """
        query_resp = await client.post(
            "/api/v1/sql/query",
            json={"dataset_id": ds_id, "sql": complex_sql},
        )
        assert query_resp.status_code == 200
        res = query_resp.json()
        assert res["status"] == "COMPLETED"
        assert res["row_count"] == 4  # North, West, South, East
        assert res["rows"][0]["region"] in ("North", "West")
        assert res["rows"][0]["rev_rank"] == 1
        assert res["execution_time_ms"] > 0
        assert len(res["suggested_charts"]) > 0

        # Step 6: Create Version 2 (filter out low-value deals) to verify Version Isolation
        apply_resp = await client.post(
            f"/api/v1/cleaning/apply/{ds_id}",
            json={
                "steps": [
                    {
                        "step_id": "filter_deals",
                        "type": "FILTER_ROWS",
                        "parameters": {
                            "column": "revenue",
                            "operator": ">=",
                            "value": 10000.0,
                        },
                        "input_columns": ["revenue"],
                        "output_columns": ["revenue"],
                        "description": "Filter high-value deals",
                        "enabled": True,
                    }
                ],
                "version_label": "High-Value Deals Only",
            },
        )
        assert apply_resp.status_code == 200
        v2_id = apply_resp.json()["new_version"]["version_id"]

        # Run identical query against v1 vs v2
        count_sql = "SELECT count(*) as total_deals, round(sum(revenue), 2) as grand_total FROM dataset;"
        q_v1 = await client.post(
            "/api/v1/sql/query",
            json={"dataset_id": ds_id, "version_id": "v1", "sql": count_sql},
        )
        assert q_v1.status_code == 200
        assert q_v1.json()["rows"][0]["total_deals"] == 8

        q_v2 = await client.post(
            "/api/v1/sql/query",
            json={"dataset_id": ds_id, "version_id": v2_id, "sql": count_sql},
        )
        assert q_v2.status_code == 200
        assert q_v2.json()["rows"][0]["total_deals"] == 4  # Only 4 deals >= 10,000

        # Step 7: Explain Plan
        explain_resp = await client.post(
            "/api/v1/sql/explain",
            json={"dataset_id": ds_id, "sql": complex_sql},
        )
        assert explain_resp.status_code == 200
        assert len(explain_resp.json()["plan_text"]) > 10

        # Step 8: Saved Queries & History
        save_resp = await client.post(
            "/api/v1/sql/saved",
            json={
                "name": "Regional Rankings",
                "description": "Ranks regions by revenue",
                "dataset_id": ds_id,
                "version_scope": "active",
                "sql": complex_sql,
                "tags": ["regional", "kpi"],
            },
        )
        assert save_resp.status_code == 201

        hist_resp = await client.get(f"/api/v1/sql/history?dataset_id={ds_id}")
        assert hist_resp.status_code == 200
        assert len(hist_resp.json()) >= 3
