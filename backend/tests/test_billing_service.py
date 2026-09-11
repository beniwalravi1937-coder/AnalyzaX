"""
Integration Tests for Phase 21: Billing Application Services.
Validates customer mapping, entitlement synchronization, downgrade safety, and reconciliation.
"""

import tempfile
import pytest

from backend.app.engines.billing.models import (
    BillingInterval,
    BillingPrice,
    Subscription,
    SubscriptionStatus,
)
from backend.app.engines.billing.repository import BillingRepository
from backend.app.engines.billing.sandbox_provider import SandboxBillingProvider
from backend.app.engines.usage.models import PlanTier
from backend.app.engines.usage.repository import UsageRepository
from backend.app.services.billing.catalog_service import BillingCatalogService
from backend.app.services.billing.checkout_service import BillingCheckoutService
from backend.app.services.billing.customer_service import BillingCustomerService
from backend.app.services.billing.reconciliation_service import BillingReconciliationService
from backend.app.services.billing.subscription_service import BillingSubscriptionService
from backend.app.services.billing.sync_service import BillingSyncService
from backend.app.services.usage.plan_service import PlanService


class TestBillingServices:
    @pytest.fixture
    def env(self):
        tmp_dir = tempfile.mkdtemp()
        repo = BillingRepository(storage_dir=tmp_dir)
        provider = SandboxBillingProvider(webhook_secret="whsec_test_secret")
        usage_repo = UsageRepository(storage_dir=tmp_dir)
        plans = PlanService(repo=usage_repo)

        catalog_svc = BillingCatalogService(repo=repo)
        cust_svc = BillingCustomerService(repo=repo, provider=provider)
        sync_svc = BillingSyncService(repo=repo, provider=provider, plans=plans)
        sub_svc = BillingSubscriptionService(
            repo=repo, provider=provider, catalog_svc=catalog_svc, sync_svc=sync_svc, plans=plans
        )
        checkout_svc = BillingCheckoutService(
            catalog_svc=catalog_svc, cust_svc=cust_svc, repo=repo, provider=provider
        )
        recon_svc = BillingReconciliationService(repo=repo, provider=provider)

        return {
            "repo": repo,
            "provider": provider,
            "plans": plans,
            "catalog": catalog_svc,
            "customers": cust_svc,
            "sync": sync_svc,
            "subscriptions": sub_svc,
            "checkout": checkout_svc,
            "reconciliation": recon_svc,
        }

    def test_customer_workspace_mapping_uniqueness(self, env):
        cust_svc = env["customers"]
        c1 = cust_svc.get_or_create_customer("ws_alpha", email="alpha@test.com")
        assert c1.workspace_id == "ws_alpha"

        # Calling again returns the same customer without duplicate creation
        c2 = cust_svc.get_or_create_customer("ws_alpha", email="alpha_new@test.com")
        assert c1.billing_customer_id == c2.billing_customer_id
        assert c1.external_customer_id == c2.external_customer_id

    def test_checkout_does_not_activate_paid_plan(self, env):
        """CRITICAL: Creating a checkout session must NOT grant entitlements."""
        checkout_svc = env["checkout"]
        plans = env["plans"]

        ws_id = "ws_test_checkout"
        plans.assign_plan(ws_id, PlanTier.FREE)

        # Create checkout session for PRO
        session = checkout_svc.create_checkout_session(
            workspace_id=ws_id,
            plan_code="PRO",
            interval=BillingInterval.MONTH,
            user_email="user@test.com",
        )
        assert session.plan_code == "PRO"

        # Verify plan is STILL FREE
        wp = plans.get_workspace_assignment(ws_id)
        assert wp.plan_code == "FREE"

    def test_sync_activates_entitlements(self, env):
        """Authoritative subscription sync immediately drives WorkspacePlan and entitlements."""
        sync_svc = env["sync"]
        plans = env["plans"]
        provider = env["provider"]

        ws_id = "ws_test_sync"
        plans.assign_plan(ws_id, PlanTier.FREE)

        # Simulate subscription created on provider
        sub = provider.create_customer(ws_id, "user@test.com")
        price = env["catalog"].resolve_price("PRO", BillingInterval.MONTH)
        checkout_event = provider.simulate_checkout_completed(
            session_id="cs_123",
            workspace_id=ws_id,
            customer_id=sub.external_customer_id,
            plan_code="PRO",
            price_id=price.billing_price_id,
            amount_minor=price.amount_minor_units,
        )

        sub_id = checkout_event["data"]["object"]["subscription"]
        synced = sync_svc.sync_subscription(ws_id, sub_id)
        assert synced.plan_code == "PRO"
        assert synced.status == SubscriptionStatus.ACTIVE

        # Verify WorkspacePlan is now PRO
        wp = plans.get_workspace_assignment(ws_id)
        assert wp.plan_code == "PRO"

    def test_downgrade_safety_no_data_deleted(self, env):
        """Downgrading plan must transition WorkspacePlan to FREE without deleting resources."""
        sub_svc = env["subscriptions"]
        sync_svc = env["sync"]
        plans = env["plans"]
        provider = env["provider"]

        ws_id = "ws_downgrade"
        plans.assign_plan(ws_id, PlanTier.PRO)

        # Create active PRO subscription
        price = env["catalog"].resolve_price("PRO", BillingInterval.MONTH)
        evt = provider.simulate_checkout_completed(
            session_id="cs_down",
            workspace_id=ws_id,
            customer_id="cus_down",
            plan_code="PRO",
            price_id=price.billing_price_id,
            amount_minor=price.amount_minor_units,
        )
        sub_id = evt["data"]["object"]["subscription"]
        sync_svc.sync_subscription(ws_id, sub_id)

        # Cancel immediately
        sub_svc.cancel_subscription(ws_id, cancel_at_period_end=False)

        # Verify plan falls back to FREE
        wp = plans.get_workspace_assignment(ws_id)
        assert wp.plan_code == "FREE"

    def test_reconciliation_detects_mismatch(self, env):
        recon_svc = env["reconciliation"]
        repo = env["repo"]

        # Insert internal subscription that doesn't exist on provider
        ghost_sub = Subscription(
            workspace_id="ws_ghost",
            billing_customer_id="cus_ghost",
            provider="sandbox",
            external_subscription_id="sub_ghost_nonexistent",
            plan_code="PRO",
            billing_price_id="bprice_pro",
            status=SubscriptionStatus.ACTIVE,
            current_period_start="2026-09-01T00:00:00Z",
            current_period_end="2026-10-01T00:00:00Z",
        )
        repo.save_subscription(ghost_sub)

        report = recon_svc.reconcile_workspace("ws_ghost")
        assert report.is_healthy is False
        assert report.mismatches_found == 1
        assert report.discrepancies[0]["issue"] == "MISSING_PROVIDER_SUBSCRIPTION"
