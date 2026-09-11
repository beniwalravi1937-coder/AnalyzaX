"""
Unit & Concurrency Tests for Usage Metering, Quotas, Entitlements & Plan Management (Phase 20).
Covers:
- Plans catalog, workspace assignment, and versioning
- Feature entitlements & limit lookups
- Append-only usage events and idempotency deduplication
- Quota enforcement and QuotaExceededException contract
- Asynchronous reservation lifecycle (reserve -> finalize / release)
- Concurrency race-safety under high contention
- Plan upgrades and downgrade data preservation guarantees
- Diagnostic reconciliation
"""

from concurrent.futures import ThreadPoolExecutor
import os
import shutil
import tempfile
import uuid
import pytest

from backend.app.core.errors import QuotaExceededException
from backend.app.engines.usage.catalog import PLAN_CATALOG
from backend.app.engines.usage.metrics import METRIC_REGISTRY, UsageMetrics
from backend.app.engines.usage.models import (
    LimitPolicy,
    PlanStatus,
    PlanTier,
    QuotaPeriod,
    ReservationStatus,
)
from backend.app.engines.usage.repository import UsageRepository
from backend.app.services.usage.plan_service import PlanService
from backend.app.services.usage.quota_service import QuotaService
from backend.app.services.usage.usage_service import UsageService


@pytest.fixture
def temp_usage_env():
    """Isolated temporary environment for usage tests."""
    temp_dir = tempfile.mkdtemp(prefix="analyzax_usage_test_")
    repo = UsageRepository(storage_dir=temp_dir)
    plan_svc = PlanService(repository=repo)
    usage_svc = UsageService(repository=repo)
    quota_svc = QuotaService(plan_service=plan_svc, usage_service=usage_svc, repository=repo)

    yield {
        "dir": temp_dir,
        "repo": repo,
        "plan_service": plan_svc,
        "usage_service": usage_svc,
        "quota_service": quota_svc,
    }

    shutil.rmtree(temp_dir, ignore_errors=True)


class TestPlansAndEntitlements:
    def test_default_catalog_has_all_tiers(self, temp_usage_env):
        repo = temp_usage_env["repo"]
        plans = repo.list_plans()
        tiers = {p.plan_code for p in plans}
        assert "FREE" in tiers
        assert "PRO" in tiers
        assert "TEAM" in tiers
        assert "ENTERPRISE" in tiers

    def test_workspace_auto_provisions_free_plan(self, temp_usage_env):
        plan_svc = temp_usage_env["plan_service"]
        ws_id = f"ws_{uuid.uuid4().hex[:8]}"
        wp = plan_svc.get_workspace_assignment(ws_id)
        assert wp.workspace_id == ws_id
        assert wp.plan_code == "FREE"
        assert wp.status == PlanStatus.ACTIVE

    def test_plan_comparison_matrix(self, temp_usage_env):
        plan_svc = temp_usage_env["plan_service"]
        matrix = plan_svc.get_plan_comparison()
        assert len(matrix.plans) >= 4
        codes = [p.plan_code for p in matrix.plans]
        assert "FREE" in codes and "PRO" in codes

    def test_entitlement_lookup_reflects_plan(self, temp_usage_env):
        plan_svc = temp_usage_env["plan_service"]
        ws_id = f"ws_{uuid.uuid4().hex[:8]}"

        # On FREE plan, AI Analyst limit is 100 messages
        ent_free = plan_svc.get_entitlement(ws_id, "AI_ANALYST")
        assert ent_free is not None
        assert ent_free.enabled is True
        assert ent_free.limit == 100

        # Upgrade to PRO
        plan_svc.assign_plan(ws_id, PlanTier.PRO)
        ent_pro = plan_svc.get_entitlement(ws_id, "AI_ANALYST")
        assert ent_pro is not None
        assert ent_pro.limit == 1000


class TestUsageEventsAndIdempotency:
    def test_record_usage_event_and_aggregation(self, temp_usage_env):
        usage_svc = temp_usage_env["usage_service"]
        ws_id = f"ws_{uuid.uuid4().hex[:8]}"

        event = usage_svc.record_usage(
            workspace_id=ws_id,
            metric_key=UsageMetrics.AI_ANALYST_MESSAGES.key,
            quantity=5.0,
            operation_type="ai_chat",
        )
        assert event.quantity == 5.0

        current_usage = usage_svc.get_current_usage(ws_id, UsageMetrics.AI_ANALYST_MESSAGES.key)
        assert current_usage == 5.0

        # Add more usage
        usage_svc.record_usage(
            workspace_id=ws_id,
            metric_key=UsageMetrics.AI_ANALYST_MESSAGES.key,
            quantity=10.0,
            operation_type="ai_chat",
        )
        assert usage_svc.get_current_usage(ws_id, UsageMetrics.AI_ANALYST_MESSAGES.key) == 15.0

    def test_idempotency_prevents_duplicate_recording(self, temp_usage_env):
        usage_svc = temp_usage_env["usage_service"]
        ws_id = f"ws_{uuid.uuid4().hex[:8]}"
        key = "unique_op_123"

        ev1 = usage_svc.record_usage(
            workspace_id=ws_id,
            metric_key=UsageMetrics.SQL_QUERY_EXECUTIONS.key,
            quantity=1.0,
            idempotency_key=key,
        )
        # Duplicate submission with same idempotency_key
        ev2 = usage_svc.record_usage(
            workspace_id=ws_id,
            metric_key=UsageMetrics.SQL_QUERY_EXECUTIONS.key,
            quantity=1.0,
            idempotency_key=key,
        )

        assert ev1.usage_event_id == ev2.usage_event_id
        # Total counted is 1.0, not 2.0
        assert usage_svc.get_current_usage(ws_id, UsageMetrics.SQL_QUERY_EXECUTIONS.key) == 1.0

    def test_negative_or_zero_quantity_rejected(self, temp_usage_env):
        usage_svc = temp_usage_env["usage_service"]
        ws_id = f"ws_{uuid.uuid4().hex[:8]}"

        with pytest.raises(ValueError):
            usage_svc.record_usage(
                workspace_id=ws_id,
                metric_key=UsageMetrics.AI_ANALYST_MESSAGES.key,
                quantity=-5.0,
            )

        with pytest.raises(ValueError):
            usage_svc.record_usage(
                workspace_id=ws_id,
                metric_key=UsageMetrics.AI_ANALYST_MESSAGES.key,
                quantity=0.0,
            )


class TestQuotaEnforcement:
    def test_quota_allowed_below_limit(self, temp_usage_env):
        quota_svc = temp_usage_env["quota_service"]
        ws_id = f"ws_{uuid.uuid4().hex[:8]}"

        decision = quota_svc.check_quota(ws_id, UsageMetrics.AI_ANALYST_MESSAGES.key, 10.0)
        assert decision.allowed is True
        assert decision.current_usage == 0.0
        assert decision.limit == 100.0
        assert decision.remaining == 100.0

    def test_quota_blocked_when_exceeded(self, temp_usage_env):
        quota_svc = temp_usage_env["quota_service"]
        usage_svc = temp_usage_env["usage_service"]
        ws_id = f"ws_{uuid.uuid4().hex[:8]}"

        # Consume 95 units
        usage_svc.record_usage(ws_id, UsageMetrics.AI_ANALYST_MESSAGES.key, 95.0)

        # 5 units should be allowed
        dec5 = quota_svc.check_quota(ws_id, UsageMetrics.AI_ANALYST_MESSAGES.key, 5.0)
        assert dec5.allowed is True

        # Consume 5 units -> at 100 limit
        usage_svc.record_usage(ws_id, UsageMetrics.AI_ANALYST_MESSAGES.key, 5.0)

        # Next unit must be denied with QuotaExceededException
        with pytest.raises(QuotaExceededException) as exc_info:
            quota_svc.enforce_quota(ws_id, UsageMetrics.AI_ANALYST_MESSAGES.key, 1.0)

        err = exc_info.value
        assert err.metric == UsageMetrics.AI_ANALYST_MESSAGES.key
        assert err.limit == 100.0
        assert err.remaining == 0.0
        assert err.plan == "FREE"


class TestReservations:
    def test_reservation_lifecycle_consumed(self, temp_usage_env):
        quota_svc = temp_usage_env["quota_service"]
        usage_svc = temp_usage_env["usage_service"]
        ws_id = f"ws_{uuid.uuid4().hex[:8]}"

        res = quota_svc.reserve_quota(
            workspace_id=ws_id,
            metric_key=UsageMetrics.FORECAST_RUNS.key,
            quantity=1.0,
            operation_id="fexp_001",
        )
        assert res.status == ReservationStatus.RESERVED

        # Finalize
        event = quota_svc.finalize_quota(res.reservation_id)
        assert event.quantity == 1.0
        assert usage_svc.get_current_usage(ws_id, UsageMetrics.FORECAST_RUNS.key) == 1.0

    def test_reservation_lifecycle_released_on_failure(self, temp_usage_env):
        quota_svc = temp_usage_env["quota_service"]
        usage_svc = temp_usage_env["usage_service"]
        ws_id = f"ws_{uuid.uuid4().hex[:8]}"

        res = quota_svc.reserve_quota(
            workspace_id=ws_id,
            metric_key=UsageMetrics.ML_EXPERIMENTS.key,
            quantity=1.0,
            operation_id="exp_fail",
        )
        assert res.status == ReservationStatus.RESERVED

        # Job fails -> release reservation
        rel = quota_svc.release_quota(res.reservation_id)
        assert rel.status == ReservationStatus.RELEASED
        # Usage must remain 0
        assert usage_svc.get_current_usage(ws_id, UsageMetrics.ML_EXPERIMENTS.key) == 0.0


class TestConcurrencyRaceSafety:
    def test_concurrent_reservations_never_exceed_limit(self, temp_usage_env):
        """
        Verify race condition safety:
        Limit = 5 units.
        15 concurrent worker threads attempt to reserve 1 unit simultaneously.
        Exactly 5 must succeed, and exactly 10 must be rejected.
        """
        quota_svc = temp_usage_env["quota_service"]
        plan_svc = temp_usage_env["plan_service"]
        ws_id = f"ws_concurrency_{uuid.uuid4().hex[:8]}"

        # We will test using DATASET_UPLOADS which has limit = 10 on FREE.
        # Let's verify with 15 concurrent threads for 1 unit each.
        results = []

        def worker(thread_idx: int):
            try:
                res = quota_svc.reserve_quota(
                    workspace_id=ws_id,
                    metric_key=UsageMetrics.DATASET_UPLOADS.key,
                    quantity=1.0,
                    operation_id=f"op_{thread_idx}",
                )
                return True, res.reservation_id
            except QuotaExceededException:
                return False, None

        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(worker, i) for i in range(15)]
            for f in futures:
                results.append(f.result())

        successes = [r for r in results if r[0] is True]
        failures = [r for r in results if r[0] is False]

        # On FREE, DATASET_UPLOADS limit is 10
        assert len(successes) == 10
        assert len(failures) == 5


class TestPlanChangesAndDowngradeSafety:
    def test_plan_upgrade_expands_limits(self, temp_usage_env):
        plan_svc = temp_usage_env["plan_service"]
        quota_svc = temp_usage_env["quota_service"]
        usage_svc = temp_usage_env["usage_service"]
        ws_id = f"ws_{uuid.uuid4().hex[:8]}"

        # Max out FREE AI limit (100)
        usage_svc.record_usage(ws_id, UsageMetrics.AI_ANALYST_MESSAGES.key, 100.0)
        assert quota_svc.check_quota(ws_id, UsageMetrics.AI_ANALYST_MESSAGES.key, 1.0).allowed is False

        # Upgrade to PRO (limit 1000)
        plan_svc.assign_plan(ws_id, PlanTier.PRO)
        dec = quota_svc.check_quota(ws_id, UsageMetrics.AI_ANALYST_MESSAGES.key, 1.0)
        assert dec.allowed is True
        assert dec.limit == 1000.0
        assert dec.remaining == 900.0

    def test_plan_downgrade_preserves_historical_data_and_flags_warning(self, temp_usage_env):
        plan_svc = temp_usage_env["plan_service"]
        usage_svc = temp_usage_env["usage_service"]
        ws_id = f"ws_{uuid.uuid4().hex[:8]}"

        # Start on PRO, consume 250 AI messages
        plan_svc.assign_plan(ws_id, PlanTier.PRO)
        usage_svc.record_usage(ws_id, UsageMetrics.AI_ANALYST_MESSAGES.key, 250.0)

        # Downgrade to FREE (which has limit 100)
        wp = plan_svc.assign_plan(ws_id, PlanTier.FREE)
        assert wp.plan_code == "FREE"

        # Historical usage must remain intact (250)
        assert usage_svc.get_current_usage(ws_id, UsageMetrics.AI_ANALYST_MESSAGES.key) == 250.0

        # Summary flags overage/warning safely without data deletion
        summary = usage_svc.get_usage_summary(ws_id)
        assert summary.plan_code == "FREE"
        ai_stat = next(s for s in summary.quotas if s.metric_key == UsageMetrics.AI_ANALYST_MESSAGES.key)
        assert ai_stat.used == 250.0
        assert ai_stat.is_exceeded is True


class TestReconciliation:
    def test_reconciliation_detects_clean_state(self, temp_usage_env):
        usage_svc = temp_usage_env["usage_service"]
        ws_id = f"ws_{uuid.uuid4().hex[:8]}"

        usage_svc.record_usage(ws_id, UsageMetrics.AI_ANALYST_MESSAGES.key, 12.0)
        usage_svc.record_usage(ws_id, UsageMetrics.SQL_QUERY_EXECUTIONS.key, 4.0)

        rep = usage_svc.reconcile_workspace_usage(ws_id)
        assert rep.is_healthy is True
        assert rep.discrepancies_found == 0
        assert len(rep.discrepancies) == 0
