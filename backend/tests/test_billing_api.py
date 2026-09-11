"""
API Integration & Golden Path Tests for Phase 21: Billing & Subscriptions.
Mounted at /api/v1/billing.
"""

import json
import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.engines.auth.models import RoleName, User, UserRegisterRequest
from backend.app.engines.billing import SandboxBillingProvider, get_billing_provider
from backend.app.engines.usage.models import PlanTier
from backend.app.services.auth.auth_service import auth_service
from backend.app.services.auth.authorization_service import authorization_service
from backend.app.services.usage import plan_service
from backend.app.services.workspace.workspace_service import workspace_service

client = TestClient(app)


class TestBillingApi:
    @pytest.fixture
    def auth_env(self):
        # Register a unique test owner user
        unique = uuid.uuid4().hex[:8]
        email = f"billing_owner_{unique}@example.com"
        password = "SecurePassword123!"
        req = UserRegisterRequest(
            email=email,
            password=password,
            display_name=f"Billing Owner {unique}",
        )
        safe_user, session, raw_token, ws_id, proj_id = auth_service.register_user(req)
        plan_service.assign_plan(ws_id, PlanTier.FREE)

        headers = {
            "Authorization": f"Bearer {raw_token}",
            "X-Workspace-Id": ws_id,
        }

        return {
            "user": safe_user,
            "session": session,
            "workspace_id": ws_id,
            "headers": headers,
        }

    def test_get_billing_config(self):
        resp = client.get("/api/v1/billing/config")
        assert resp.status_code == 200
        data = resp.json()
        assert data["enabled"] is True
        assert data["provider"] in ["sandbox", "stripe"]
        assert data["currency"] == "USD"

    def test_get_prices_catalog(self):
        resp = client.get("/api/v1/billing/prices")
        assert resp.status_code == 200
        prices = resp.json()
        assert isinstance(prices, list)
        assert len(prices) >= 4
        plans = {p["plan_code"] for p in prices}
        assert "PRO" in plans and "TEAM" in plans

    def test_get_overview_initial_free(self, auth_env):
        headers = auth_env["headers"]
        resp = client.get("/api/v1/billing/overview", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["workspace_id"] == auth_env["workspace_id"]
        assert data["plan_code"] == "FREE"
        assert len(data["prices"]) >= 4

    def test_golden_path_checkout_upgrade_and_invoices(self, auth_env):
        """
        Golden Path:
        1. Workspace starts on FREE plan.
        2. Initiate checkout session for PRO tier.
        3. Complete checkout via sandbox helper.
        4. Webhook updates subscription to ACTIVE and workspace plan to PRO.
        5. Verify billing overview reflects PRO plan and active subscription.
        6. Verify invoice history contains paid invoice.
        7. Schedule cancellation at period end -> remains PRO until period end.
        8. Resume subscription -> cancels scheduled termination.
        9. Run reconciliation audit -> clean bill of health.
        """
        headers = auth_env["headers"]
        ws_id = auth_env["workspace_id"]

        # Step 1: Verify Initial FREE state
        init_res = client.get("/api/v1/billing/overview", headers=headers)
        assert init_res.status_code == 200
        assert init_res.json()["plan_code"] == "FREE"

        # Step 2: Initiate Checkout Session
        checkout_res = client.post(
            "/api/v1/billing/checkout",
            json={"plan_code": "PRO", "interval": "month"},
            headers=headers,
        )
        assert checkout_res.status_code == 200
        checkout_data = checkout_res.json()
        assert checkout_data["plan_code"] == "PRO"
        assert checkout_data["amount_minor_units"] == 2900
        assert "checkout_url" in checkout_data

        # Step 3: Complete Sandbox Checkout
        complete_res = client.post(
            "/api/v1/billing/checkout/complete-sandbox",
            json={"plan_code": "PRO", "interval": "month"},
            headers=headers,
        )
        assert complete_res.status_code == 200
        assert complete_res.json()["status"] == "success"

        # Step 4: Verify Subscription and Workspace Plan updated to PRO
        sub_res = client.get("/api/v1/billing/subscription", headers=headers)
        assert sub_res.status_code == 200
        sub_data = sub_res.json()
        assert sub_data["plan_code"] == "PRO"
        assert sub_data["status"] == "active"

        # Verify plan service has PRO
        wp = plan_service.get_workspace_assignment(ws_id)
        assert wp.plan_code == "PRO"

        # Step 5: Verify Invoices Table has Paid Invoice
        inv_res = client.get("/api/v1/billing/invoices", headers=headers)
        assert inv_res.status_code == 200
        inv_data = inv_res.json()
        assert inv_data["total"] >= 1
        assert inv_data["invoices"][0]["status"] == "paid"
        assert inv_data["invoices"][0]["total_minor"] == 2900

        # Step 6: Cancel at Period End
        cancel_res = client.post(
            "/api/v1/billing/subscription/cancel",
            json={"cancel_at_period_end": True, "reason": "Testing period end cancel"},
            headers=headers,
        )
        assert cancel_res.status_code == 200
        assert cancel_res.json()["cancel_at_period_end"] is True

        # Entitlement still active until period end!
        wp_after_cancel = plan_service.get_workspace_assignment(ws_id)
        assert wp_after_cancel.plan_code == "PRO"

        # Step 7: Resume Subscription
        resume_res = client.post("/api/v1/billing/subscription/resume", headers=headers)
        assert resume_res.status_code == 200
        assert resume_res.json()["cancel_at_period_end"] is False

        # Step 8: Reconcile Ledger
        recon_res = client.post("/api/v1/billing/reconcile", headers=headers)
        assert recon_res.status_code == 200
        assert recon_res.json()["is_healthy"] is True

    def test_webhook_endpoint_security(self):
        """Validates webhook endpoint rejects unauthorized/unsigned calls."""
        # Unsigned request -> 400
        resp = client.post(
            "/api/v1/billing/webhooks/sandbox",
            content=b'{"id":"evt_unsigned"}',
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400

        # Signed request -> 200
        provider = get_billing_provider()
        if isinstance(provider, SandboxBillingProvider):
            body = json.dumps({"id": f"evt_api_test_{uuid.uuid4().hex[:8]}", "type": "ping"}).encode("utf-8")
            sig = provider.generate_signature(body)
            valid_resp = client.post(
                "/api/v1/billing/webhooks/sandbox",
                content=body,
                headers={"stripe-signature": sig, "Content-Type": "application/json"},
            )
            assert valid_resp.status_code == 200
            assert valid_resp.json()["received"] is True
