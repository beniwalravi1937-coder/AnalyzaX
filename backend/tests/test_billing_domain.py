"""
Unit Tests for Phase 21: Billing Domain Models & Integer Minor-Unit Arithmetic.
Validates exact monetary precision, state transitions, and catalog constraints.
"""

import pytest
from pydantic import ValidationError

from backend.app.engines.billing.models import (
    BillingCustomer,
    BillingInterval,
    BillingPrice,
    Invoice,
    InvoiceStatus,
    Payment,
    PaymentStatus,
    Subscription,
    SubscriptionStatus,
    WebhookEventRecord,
    WebhookEventStatus,
)


class TestBillingModelsAndPrecision:
    def test_price_integer_minor_units(self):
        """Monetary values must be stored in exact integer minor units (cents)."""
        price = BillingPrice(
            plan_code="PRO",
            external_price_id="price_pro_monthly",
            currency="USD",
            amount_minor_units=2900,  # $29.00
            interval=BillingInterval.MONTH,
        )
        assert price.amount_minor_units == 2900
        assert price.amount_display == "$29.00"
        assert price.plan_code == "PRO"

    def test_price_rejects_negative_amount(self):
        """Negative price amounts must be rejected by pydantic validator."""
        with pytest.raises(ValidationError):
            BillingPrice(
                plan_code="PRO",
                external_price_id="price_pro",
                currency="USD",
                amount_minor_units=-500,
                interval=BillingInterval.MONTH,
            )

    def test_annual_price_and_large_minor_units(self):
        """Validates large monetary amounts without floating point overflow."""
        enterprise = BillingPrice(
            plan_code="ENTERPRISE",
            external_price_id="price_ent_annual",
            currency="USD",
            amount_minor_units=499000,  # $4,990.00
            interval=BillingInterval.YEAR,
        )
        assert enterprise.amount_minor_units == 499000
        assert enterprise.amount_display == "$4990.00"

    def test_invoice_minor_units_display(self):
        inv = Invoice(
            workspace_id="ws_test",
            billing_customer_id="bcust_test",
            external_invoice_id="inv_123",
            status=InvoiceStatus.PAID,
            currency="USD",
            subtotal_minor=2900,
            tax_minor=0,
            total_minor=2900,
            amount_paid_minor=2900,
            amount_due_minor=0,
            period_start="2026-09-01T00:00:00Z",
            period_end="2026-10-01T00:00:00Z",
        )
        assert inv.total_minor == 2900
        assert inv.total_display == "$29.00"

    def test_payment_display(self):
        pay = Payment(
            workspace_id="ws_test",
            billing_customer_id="bcust_test",
            external_payment_id="pay_123",
            amount_minor_units=9900,
            currency="USD",
            status=PaymentStatus.SUCCEEDED,
        )
        assert pay.amount_minor_units == 9900
        assert pay.amount_display == "$99.00"

    def test_subscription_is_active_entitlement(self):
        """Subscription entitlement active check."""
        active_sub = Subscription(
            workspace_id="ws_test",
            billing_customer_id="bcust_test",
            external_subscription_id="sub_1",
            plan_code="PRO",
            billing_price_id="bprice_pro",
            status=SubscriptionStatus.ACTIVE,
            current_period_start="2026-09-01T00:00:00Z",
            current_period_end="2026-10-01T00:00:00Z",
        )
        assert active_sub.is_active_entitlement is True

        canceled_sub = Subscription(
            workspace_id="ws_test",
            billing_customer_id="bcust_test",
            external_subscription_id="sub_2",
            plan_code="PRO",
            billing_price_id="bprice_pro",
            status=SubscriptionStatus.CANCELED,
            current_period_start="2026-08-01T00:00:00Z",
            current_period_end="2026-09-01T00:00:00Z",
        )
        assert canceled_sub.is_active_entitlement is False
