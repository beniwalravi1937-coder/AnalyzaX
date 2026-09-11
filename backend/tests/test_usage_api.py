"""
Integration & Golden Path API Tests for Usage Metering, Quotas & Plans (Phase 20).
Mounted at /api/v1/usage and /api/v1/plans.
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.usage import plan_service, usage_service
from backend.app.engines.usage.metrics import UsageMetrics
from backend.app.engines.usage.models import PlanTier

client = TestClient(app)


class TestUsageAndPlansApi:
    @pytest.fixture
    def test_workspace_id(self):
        ws_id = f"ws_api_test_{uuid.uuid4().hex[:8]}"
        plan_service.assign_plan(ws_id, PlanTier.FREE)
        return ws_id

    def test_get_plans_catalog(self):
        resp = client.get("/api/v1/plans")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 4
        codes = [p["plan_code"] for p in data]
        assert "FREE" in codes and "PRO" in codes

    def test_get_current_plan(self, test_workspace_id):
        resp = client.get(f"/api/v1/plans/current?workspace_id={test_workspace_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["workspace_id"] == test_workspace_id
        assert data["plan_code"] == "FREE"
        assert "entitlements" in data
        assert "AI_ANALYST" in data["entitlements"]

    def test_get_usage_summary_initial(self, test_workspace_id):
        resp = client.get(f"/api/v1/usage/summary?workspace_id={test_workspace_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["workspace_id"] == test_workspace_id
        assert data["plan_code"] == "FREE"
        assert "quotas" in data
        assert "resources" in data
        assert len(data["quotas"]) > 0

    def test_golden_path_usage_quota_and_upgrade(self, test_workspace_id):
        """
        Comprehensive Golden Path:
        1. Workspace on FREE plan
        2. Record usage up to the limit for AI Analyst (100)
        3. Verify usage summary reflects 100% consumption
        4. Attempt operation beyond quota -> verify structured 429 QUOTA_EXCEEDED
        5. Upgrade workspace plan to PRO via API
        6. Verify new plan and expanded quota (1000)
        7. Verify additional usage is now allowed
        8. Audit usage history
        """
        # Step 1: Initial state
        summary_res = client.get(f"/api/v1/usage/summary?workspace_id={test_workspace_id}")
        assert summary_res.status_code == 200

        # Step 2: Record 100 messages to hit limit
        usage_service.record_usage(
            workspace_id=test_workspace_id,
            metric_key=UsageMetrics.AI_ANALYST_MESSAGES.key,
            quantity=100.0,
            operation_type="ai_chat",
        )

        # Step 3: Summary check
        summary_res = client.get(f"/api/v1/usage/summary?workspace_id={test_workspace_id}")
        assert summary_res.status_code == 200
        quotas = {q["metric_key"]: q for q in summary_res.json()["quotas"]}
        assert quotas[UsageMetrics.AI_ANALYST_MESSAGES.key]["used"] == 100.0
        assert quotas[UsageMetrics.AI_ANALYST_MESSAGES.key]["percentage"] == 100.0
        assert quotas[UsageMetrics.AI_ANALYST_MESSAGES.key]["is_exceeded"] is True

        # Step 4: AI Analyst call should fail with 429 QuotaExceeded
        ai_resp = client.post(
            "/api/v1/ai-analyst/chat",
            json={
                "workspace_id": test_workspace_id,
                "message": "Hello AI Analyst, what are the key trends?",
            },
        )
        assert ai_resp.status_code == 429
        err_body = ai_resp.json()
        error_obj = err_body.get("error", err_body.get("detail", {}))
        assert error_obj.get("code") == "QUOTA_EXCEEDED" or error_obj.get("details", {}).get("metric") == UsageMetrics.AI_ANALYST_MESSAGES.key

        # Step 5: Upgrade workspace plan to PRO
        plan_resp = client.post(
            f"/api/v1/workspaces/{test_workspace_id}/plan",
            json={"plan_tier": "PRO", "reason": "Upgraded for more AI capacity"},
        )
        assert plan_resp.status_code == 200
        assert plan_resp.json()["plan_code"] == "PRO"

        # Step 6: Verify new plan in usage summary
        new_summary = client.get(f"/api/v1/usage/summary?workspace_id={test_workspace_id}").json()
        assert new_summary["plan_code"] == "PRO"
        new_quotas = {q["metric_key"]: q for q in new_summary["quotas"]}
        assert new_quotas[UsageMetrics.AI_ANALYST_MESSAGES.key]["limit"] == 1000.0
        assert new_quotas[UsageMetrics.AI_ANALYST_MESSAGES.key]["remaining"] == 900.0

        # Step 7: Record additional usage under PRO
        usage_service.record_usage(
            workspace_id=test_workspace_id,
            metric_key=UsageMetrics.AI_ANALYST_MESSAGES.key,
            quantity=5.0,
            operation_type="ai_chat",
        )
        assert usage_service.get_current_usage(test_workspace_id, UsageMetrics.AI_ANALYST_MESSAGES.key) == 105.0

        # Step 8: Query history
        hist_resp = client.get(f"/api/v1/usage/history?workspace_id={test_workspace_id}")
        assert hist_resp.status_code == 200
        hist_data = hist_resp.json()
        assert hist_data["total"] >= 2
        assert len(hist_data["events"]) >= 2
