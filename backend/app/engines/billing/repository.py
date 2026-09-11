"""
Thread-safe Repository for Phase 21: Billing, Subscriptions, Payments & Revenue.
Provides atomic JSON persistence in DATA_BILLING_DIR with strict unique constraints,
O(1) in-memory indices, and default price catalog bootstrapping.
"""

from datetime import datetime, timezone
import json
import logging
import os
import threading
from typing import Any, Dict, List, Optional, Tuple

from backend.app.core.config import settings
from backend.app.engines.billing.models import (
    BillingAuditLog,
    BillingCustomer,
    BillingInterval,
    BillingPrice,
    Invoice,
    Payment,
    Subscription,
    WebhookEventRecord,
    WebhookEventStatus,
)

logger = logging.getLogger("analyzax.billing.repository")


class BillingRepository:
    """
    Thread-safe repository for all normalized billing entities.
    Enforces uniqueness constraints on:
    - workspace_id <-> billing_customer
    - (provider, external_customer_id)
    - (provider, external_subscription_id)
    - (provider, external_event_id) for idempotent webhooks
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self._dir = storage_dir or getattr(settings, "DATA_BILLING_DIR", "./data/billing")
        os.makedirs(self._dir, exist_ok=True)
        self._lock = threading.RLock()

        # In-memory indices
        self._customers_by_workspace: Dict[str, BillingCustomer] = {}
        self._customers_by_ext_id: Dict[str, BillingCustomer] = {}
        self._prices_by_id: Dict[str, BillingPrice] = {}
        self._prices_by_key: Dict[Tuple[str, str], BillingPrice] = {}  # (plan_code, interval) -> price
        self._subscriptions_by_workspace: Dict[str, Subscription] = {}
        self._subscriptions_by_ext_id: Dict[str, Subscription] = {}
        self._invoices_by_workspace: Dict[str, List[Invoice]] = {}
        self._invoices_by_ext_id: Dict[str, Invoice] = {}
        self._payments: List[Payment] = []
        self._webhook_events: Dict[str, WebhookEventRecord] = {}  # "provider:external_id" -> record
        self._audit_logs: List[BillingAuditLog] = []

        self._load_all()
        self._bootstrap_default_prices_if_empty()

    # ─────────────────────────────────────────────────────────────
    # Persistence Helpers
    # ─────────────────────────────────────────────────────────────

    def _file_path(self, filename: str) -> str:
        return os.path.join(self._dir, filename)

    def _atomic_write(self, filename: str, data: Any):
        path = self._file_path(filename)
        temp_path = f"{path}.tmp.{threading.get_ident()}"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, path)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            logger.error("Failed atomic write for %s: %s", filename, e)
            raise

    def _load_json(self, filename: str) -> Any:
        path = self._file_path(filename)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed loading %s: %s", filename, e)
            return None

    def _load_all(self):
        with self._lock:
            # Customers
            raw_cust = self._load_json("customers.json") or []
            for item in raw_cust:
                c = BillingCustomer(**item)
                self._customers_by_workspace[c.workspace_id] = c
                self._customers_by_ext_id[f"{c.provider}:{c.external_customer_id}"] = c

            # Prices
            raw_prices = self._load_json("prices.json") or []
            for item in raw_prices:
                p = BillingPrice(**item)
                self._prices_by_id[p.billing_price_id] = p
                self._prices_by_key[(p.plan_code.upper(), p.interval.value)] = p

            # Subscriptions
            raw_subs = self._load_json("subscriptions.json") or []
            for item in raw_subs:
                s = Subscription(**item)
                self._subscriptions_by_workspace[s.workspace_id] = s
                self._subscriptions_by_ext_id[f"{s.provider}:{s.external_subscription_id}"] = s

            # Invoices
            raw_inv = self._load_json("invoices.json") or []
            for item in raw_inv:
                inv = Invoice(**item)
                self._invoices_by_workspace.setdefault(inv.workspace_id, []).append(inv)
                self._invoices_by_ext_id[f"{inv.provider}:{inv.external_invoice_id}"] = inv

            # Payments
            raw_pay = self._load_json("payments.json") or []
            self._payments = [Payment(**item) for item in raw_pay]

            # Webhook Events
            raw_evts = self._load_json("webhook_events.json") or []
            for item in raw_evts:
                evt = WebhookEventRecord(**item)
                key = f"{evt.provider}:{evt.external_event_id}"
                self._webhook_events[key] = evt

            # Audit logs
            raw_audit = self._load_json("audit_logs.json") or []
            self._audit_logs = [BillingAuditLog(**item) for item in raw_audit]

    def _bootstrap_default_prices_if_empty(self):
        with self._lock:
            if self._prices_by_id:
                return

            now = datetime.now(timezone.utc).isoformat()
            default_prices = [
                # PRO
                BillingPrice(
                    billing_price_id="bprice_pro_monthly",
                    plan_code="PRO",
                    provider="sandbox",
                    external_price_id="price_pro_monthly_sandbox",
                    currency="USD",
                    amount_minor_units=2900,  # $29.00
                    interval=BillingInterval.MONTH,
                    interval_count=1,
                    active=True,
                    metadata={"display_name": "Pro Monthly", "savings_percent": 0},
                    created_at=now,
                    updated_at=now,
                ),
                BillingPrice(
                    billing_price_id="bprice_pro_annual",
                    plan_code="PRO",
                    provider="sandbox",
                    external_price_id="price_pro_annual_sandbox",
                    currency="USD",
                    amount_minor_units=29000,  # $290.00 (2 months free)
                    interval=BillingInterval.YEAR,
                    interval_count=1,
                    active=True,
                    metadata={"display_name": "Pro Annual", "savings_percent": 16},
                    created_at=now,
                    updated_at=now,
                ),
                # TEAM
                BillingPrice(
                    billing_price_id="bprice_team_monthly",
                    plan_code="TEAM",
                    provider="sandbox",
                    external_price_id="price_team_monthly_sandbox",
                    currency="USD",
                    amount_minor_units=9900,  # $99.00
                    interval=BillingInterval.MONTH,
                    interval_count=1,
                    active=True,
                    metadata={"display_name": "Team Monthly", "savings_percent": 0},
                    created_at=now,
                    updated_at=now,
                ),
                BillingPrice(
                    billing_price_id="bprice_team_annual",
                    plan_code="TEAM",
                    provider="sandbox",
                    external_price_id="price_team_annual_sandbox",
                    currency="USD",
                    amount_minor_units=99000,  # $990.00 (2 months free)
                    interval=BillingInterval.YEAR,
                    interval_count=1,
                    active=True,
                    metadata={"display_name": "Team Annual", "savings_percent": 16},
                    created_at=now,
                    updated_at=now,
                ),
                # ENTERPRISE
                BillingPrice(
                    billing_price_id="bprice_enterprise_annual",
                    plan_code="ENTERPRISE",
                    provider="sandbox",
                    external_price_id="price_enterprise_annual_sandbox",
                    currency="USD",
                    amount_minor_units=499000,  # $4,990.00
                    interval=BillingInterval.YEAR,
                    interval_count=1,
                    active=True,
                    metadata={"display_name": "Enterprise Annual", "savings_percent": 20},
                    created_at=now,
                    updated_at=now,
                ),
            ]

            for p in default_prices:
                self._prices_by_id[p.billing_price_id] = p
                self._prices_by_key[(p.plan_code.upper(), p.interval.value)] = p

            self._save_prices()

    # ─────────────────────────────────────────────────────────────
    # Customer Operations
    # ─────────────────────────────────────────────────────────────

    def save_customer(self, customer: BillingCustomer) -> BillingCustomer:
        with self._lock:
            self._customers_by_workspace[customer.workspace_id] = customer
            self._customers_by_ext_id[f"{customer.provider}:{customer.external_customer_id}"] = customer
            self._save_customers()
            return customer

    def get_customer_by_workspace(self, workspace_id: str) -> Optional[BillingCustomer]:
        with self._lock:
            return self._customers_by_workspace.get(workspace_id)

    def get_customer_by_external_id(self, provider: str, external_customer_id: str) -> Optional[BillingCustomer]:
        with self._lock:
            return self._customers_by_ext_id.get(f"{provider}:{external_customer_id}")

    def _save_customers(self):
        data = [c.model_dump() for c in self._customers_by_workspace.values()]
        self._atomic_write("customers.json", data)

    # ─────────────────────────────────────────────────────────────
    # Price Operations
    # ─────────────────────────────────────────────────────────────

    def get_all_prices(self, active_only: bool = True) -> List[BillingPrice]:
        with self._lock:
            prices = list(self._prices_by_id.values())
            if active_only:
                prices = [p for p in prices if p.active]
            return prices

    def get_price_by_id(self, price_id: str) -> Optional[BillingPrice]:
        with self._lock:
            return self._prices_by_id.get(price_id)

    def get_price_by_plan_and_interval(self, plan_code: str, interval: BillingInterval) -> Optional[BillingPrice]:
        with self._lock:
            return self._prices_by_key.get((plan_code.upper(), interval.value))

    def get_price_by_external_id(self, external_price_id: str) -> Optional[BillingPrice]:
        with self._lock:
            for p in self._prices_by_id.values():
                if p.external_price_id == external_price_id:
                    return p
            return None

    def _save_prices(self):
        data = [p.model_dump() for p in self._prices_by_id.values()]
        self._atomic_write("prices.json", data)

    # ─────────────────────────────────────────────────────────────
    # Subscription Operations
    # ─────────────────────────────────────────────────────────────

    def save_subscription(self, subscription: Subscription) -> Subscription:
        with self._lock:
            self._subscriptions_by_workspace[subscription.workspace_id] = subscription
            self._subscriptions_by_ext_id[f"{subscription.provider}:{subscription.external_subscription_id}"] = subscription
            self._save_subscriptions()
            return subscription

    def get_subscription_by_workspace(self, workspace_id: str) -> Optional[Subscription]:
        with self._lock:
            return self._subscriptions_by_workspace.get(workspace_id)

    def get_subscription_by_external_id(self, provider: str, external_subscription_id: str) -> Optional[Subscription]:
        with self._lock:
            return self._subscriptions_by_ext_id.get(f"{provider}:{external_subscription_id}")

    def get_all_subscriptions(self) -> List[Subscription]:
        with self._lock:
            return list(self._subscriptions_by_workspace.values())

    def _save_subscriptions(self):
        data = [s.model_dump() for s in self._subscriptions_by_workspace.values()]
        self._atomic_write("subscriptions.json", data)

    # ─────────────────────────────────────────────────────────────
    # Invoice & Payment Operations
    # ─────────────────────────────────────────────────────────────

    def save_invoice(self, invoice: Invoice) -> Invoice:
        with self._lock:
            ws_invoices = self._invoices_by_workspace.setdefault(invoice.workspace_id, [])
            # Update existing or append
            for i, existing in enumerate(ws_invoices):
                if existing.invoice_id == invoice.invoice_id or (
                    existing.provider == invoice.provider and existing.external_invoice_id == invoice.external_invoice_id
                ):
                    ws_invoices[i] = invoice
                    break
            else:
                ws_invoices.append(invoice)

            self._invoices_by_ext_id[f"{invoice.provider}:{invoice.external_invoice_id}"] = invoice
            self._save_invoices()
            return invoice

    def get_invoice_by_external_id(self, provider: str, external_invoice_id: str) -> Optional[Invoice]:
        with self._lock:
            return self._invoices_by_ext_id.get(f"{provider}:{external_invoice_id}")

    def list_invoices_by_workspace(
        self,
        workspace_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Invoice], int]:
        with self._lock:
            all_inv = self._invoices_by_workspace.get(workspace_id, [])
            all_inv_sorted = sorted(all_inv, key=lambda x: x.created_at, reverse=True)
            total = len(all_inv_sorted)
            return all_inv_sorted[offset : offset + limit], total

    def _save_invoices(self):
        flat: List[Dict[str, Any]] = []
        for inv_list in self._invoices_by_workspace.values():
            flat.extend([inv.model_dump() for inv in inv_list])
        self._atomic_write("invoices.json", flat)

    def save_payment(self, payment: Payment) -> Payment:
        with self._lock:
            self._payments.append(payment)
            self._atomic_write("payments.json", [p.model_dump() for p in self._payments])
            return payment

    def list_payments_by_workspace(self, workspace_id: str) -> List[Payment]:
        with self._lock:
            return [p for p in self._payments if p.workspace_id == workspace_id]

    # ─────────────────────────────────────────────────────────────
    # Webhook Idempotency Operations
    # ─────────────────────────────────────────────────────────────

    def get_webhook_event(self, provider: str, external_event_id: str) -> Optional[WebhookEventRecord]:
        with self._lock:
            key = f"{provider}:{external_event_id}"
            return self._webhook_events.get(key)

    def record_webhook_event(
        self,
        provider: str,
        external_event_id: str,
        event_type: str,
        payload_hash: str,
        status: WebhookEventStatus = WebhookEventStatus.RECEIVED,
    ) -> WebhookEventRecord:
        with self._lock:
            key = f"{provider}:{external_event_id}"
            if key in self._webhook_events:
                record = self._webhook_events[key]
                record.attempt_count += 1
            else:
                record = WebhookEventRecord(
                    provider=provider,
                    external_event_id=external_event_id,
                    event_type=event_type,
                    payload_hash=payload_hash,
                    status=status,
                )
                self._webhook_events[key] = record

            self._save_webhook_events()
            return record

    def update_webhook_event_status(
        self,
        provider: str,
        external_event_id: str,
        status: WebhookEventStatus,
        error: Optional[str] = None,
    ) -> Optional[WebhookEventRecord]:
        with self._lock:
            key = f"{provider}:{external_event_id}"
            record = self._webhook_events.get(key)
            if record:
                record.status = status
                record.processing_error = error
                if status == WebhookEventStatus.PROCESSED:
                    record.processed_at = datetime.now(timezone.utc).isoformat()
                self._save_webhook_events()
            return record

    def _save_webhook_events(self):
        data = [r.model_dump() for r in self._webhook_events.values()]
        self._atomic_write("webhook_events.json", data)

    # ─────────────────────────────────────────────────────────────
    # Audit Logging
    # ─────────────────────────────────────────────────────────────

    def record_audit(
        self,
        workspace_id: str,
        event_type: str,
        actor_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> BillingAuditLog:
        with self._lock:
            log = BillingAuditLog(
                workspace_id=workspace_id,
                event_type=event_type,
                actor_id=actor_id,
                details=details or {},
            )
            self._audit_logs.append(log)
            # Retain up to 10,000 logs
            if len(self._audit_logs) > 10000:
                self._audit_logs = self._audit_logs[-10000:]
            self._atomic_write("audit_logs.json", [a.model_dump() for a in self._audit_logs])
            return log


# Global repository instance
billing_repository = BillingRepository()
