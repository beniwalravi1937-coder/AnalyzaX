"""
Integration Tests for Phase 21: Billing Webhook Ingestion & Idempotency.
Validates cryptographic verification, duplicate suppression, and safe error handling.
"""

import json
import tempfile
import pytest

from backend.app.engines.billing.models import WebhookEventStatus
from backend.app.engines.billing.repository import BillingRepository
from backend.app.engines.billing.sandbox_provider import SandboxBillingProvider
from backend.app.engines.usage.repository import UsageRepository
from backend.app.services.billing.sync_service import BillingSyncService
from backend.app.services.billing.webhook_service import BillingWebhookService
from backend.app.services.usage.plan_service import PlanService


class TestBillingWebhooks:
    @pytest.fixture
    def setup(self):
        tmp_dir = tempfile.mkdtemp()
        secret = "whsec_test_secret_for_webhooks_123"
        repo = BillingRepository(storage_dir=tmp_dir)
        provider = SandboxBillingProvider(webhook_secret=secret)
        usage_repo = UsageRepository(storage_dir=tmp_dir)
        plans = PlanService(repo=usage_repo)
        sync_svc = BillingSyncService(repo=repo, provider=provider, plans=plans)
        webhook_svc = BillingWebhookService(repo=repo, provider=provider, sync_svc=sync_svc)

        return {
            "repo": repo,
            "provider": provider,
            "webhook_service": webhook_svc,
            "secret": secret,
            "plans": plans,
        }

    def test_invalid_signature_rejected(self, setup):
        svc = setup["webhook_service"]
        payload = b'{"id":"evt_123","type":"checkout.session.completed"}'
        headers = {"stripe-signature": "t=123,v1=invalid_fake_hash"}

        success, msg, evt_id = svc.process_webhook("sandbox", payload, headers)
        assert success is False
        assert msg == "invalid_signature"

    def test_valid_webhook_processed(self, setup):
        svc = setup["webhook_service"]
        provider = setup["provider"]
        plans = setup["plans"]

        ws_id = "ws_webhook_test"
        plans.assign_plan(ws_id, "FREE")

        evt_data = provider.simulate_checkout_completed(
            session_id="cs_valid",
            workspace_id=ws_id,
            customer_id="cus_valid",
            plan_code="PRO",
            price_id="bprice_pro_monthly",
            amount_minor=2900,
        )
        body = json.dumps(evt_data).encode("utf-8")
        sig = provider.generate_signature(body)
        headers = {"stripe-signature": sig}

        success, msg, evt_id = svc.process_webhook("sandbox", body, headers)
        assert success is True
        assert msg == "processed"

        # Verify plan updated to PRO
        wp = plans.get_workspace_assignment(ws_id)
        assert wp.plan_code == "PRO"

    def test_duplicate_webhook_delivery_idempotency(self, setup):
        """Re-delivery of the exact same event ID must be safely ignored without side effects."""
        svc = setup["webhook_service"]
        provider = setup["provider"]

        evt_data = {
            "id": "evt_duplicate_test_123",
            "type": "invoice.payment_succeeded",
            "created": 1700000000,
            "data": {
                "object": {
                    "id": "inv_dup",
                    "amount_paid": 2900,
                    "currency": "usd",
                    "metadata": {"workspace_id": "ws_dup"},
                }
            },
        }
        body = json.dumps(evt_data).encode("utf-8")
        sig = provider.generate_signature(body)
        headers = {"stripe-signature": sig}

        # First delivery
        s1, m1, _ = svc.process_webhook("sandbox", body, headers)
        assert s1 is True
        assert m1 == "processed"

        # Second delivery (duplicate)
        s2, m2, _ = svc.process_webhook("sandbox", body, headers)
        assert s2 is True
        assert m2 == "duplicate_ignored"

        # Check repository attempt count
        rec = setup["repo"].get_webhook_event("sandbox", "evt_duplicate_test_123")
        assert rec is not None
        assert rec.status == WebhookEventStatus.PROCESSED
        assert rec.attempt_count == 2
