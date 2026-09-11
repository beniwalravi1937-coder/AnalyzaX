"""
Unit Tests for Phase 21: Billing Provider Abstraction & Sandbox Implementation.
Validates HMAC-SHA256 signature verification, checkout generation, and subscription simulation.
"""

import time
import pytest

from backend.app.engines.billing.models import (
    BillingInterval,
    BillingPrice,
    SubscriptionStatus,
)
from backend.app.engines.billing.sandbox_provider import SandboxBillingProvider


class TestSandboxBillingProvider:
    @pytest.fixture
    def provider(self):
        return SandboxBillingProvider(webhook_secret="whsec_test_secret_key_12345")

    def test_customer_lifecycle(self, provider):
        cust = provider.create_customer(workspace_id="ws_1", email="owner@test.com", name="Owner")
        assert cust.workspace_id == "ws_1"
        assert cust.external_customer_id.startswith("cus_sbx_")

        retrieved = provider.get_customer(cust.external_customer_id)
        assert retrieved is not None
        assert retrieved.email == "owner@test.com"

        updated = provider.update_customer(cust.external_customer_id, email="new@test.com")
        assert updated.email == "new@test.com"

    def test_checkout_session_creation(self, provider):
        price = BillingPrice(
            plan_code="PRO",
            external_price_id="price_pro_monthly",
            currency="USD",
            amount_minor_units=2900,
            interval=BillingInterval.MONTH,
        )
        session = provider.create_checkout_session(
            workspace_id="ws_1",
            customer_id="cus_test_123",
            price=price,
            success_url="http://localhost:3000/success",
            cancel_url="http://localhost:3000/cancel",
        )
        assert session.session_id.startswith("cs_sbx_")
        assert "http://localhost:3000/checkout/sandbox/" in session.checkout_url
        assert session.external_customer_id == "cus_test_123"

    def test_portal_session_creation(self, provider):
        portal = provider.create_billing_portal_session(
            external_customer_id="cus_test_123",
            return_url="http://localhost:3000/settings/billing",
        )
        assert portal.session_id.startswith("pts_sbx_")
        assert "portal_session=" in portal.portal_url

    def test_webhook_signature_verification_success(self, provider):
        payload = b'{"id":"evt_123","type":"checkout.session.completed"}'
        sig = provider.generate_signature(payload)
        headers = {"stripe-signature": sig}

        assert provider.verify_webhook(payload, headers) is True

    def test_webhook_signature_tampered_payload_rejected(self, provider):
        payload = b'{"id":"evt_123","type":"checkout.session.completed"}'
        tampered_payload = b'{"id":"evt_123","type":"malicious_admin_upgrade"}'
        sig = provider.generate_signature(payload)
        headers = {"stripe-signature": sig}

        assert provider.verify_webhook(tampered_payload, headers) is False

    def test_webhook_signature_expired_timestamp_rejected(self, provider):
        payload = b'{"id":"evt_123"}'
        # 400 seconds ago (tolerance is 300s)
        old_ts = int(time.time()) - 400
        sig = provider.generate_signature(payload, timestamp=old_ts)
        headers = {"stripe-signature": sig}

        assert provider.verify_webhook(payload, headers) is False
