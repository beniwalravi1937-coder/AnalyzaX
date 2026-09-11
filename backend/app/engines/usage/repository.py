"""
Thread-safe Usage & Plan Repository for Phase 20.
Maintains atomic JSON persistence under data/usage/ with fast in-memory indexing,
append-only event store, and concurrency-safe reservation locks.
"""

from datetime import datetime, timezone
import json
import os
import shutil
import threading
from typing import Any, Dict, List, Optional, Tuple

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.usage.catalog import get_default_entitlements, get_default_plans
from backend.app.engines.usage.models import (
    Plan,
    PlanEntitlement,
    PlanStatus,
    ReservationStatus,
    UsageAggregation,
    UsageEvent,
    UsageReservation,
    WorkspacePlan,
)


class UsageRepository:
    """
    Thread-safe repository coordinating atomic JSON persistence,
    idempotent usage event logging, and concurrency-safe quota balances.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self._lock = threading.RLock()
        base_dir = storage_dir or getattr(settings, "DATA_USAGE_DIR", "./data/usage")
        self._storage_dir = os.path.abspath(base_dir)

        self._plans_file = os.path.join(self._storage_dir, "plans.json")
        self._entitlements_file = os.path.join(self._storage_dir, "entitlements.json")
        self._workspace_plans_file = os.path.join(self._storage_dir, "workspace_plans.json")
        self._events_file = os.path.join(self._storage_dir, "usage_events.json")
        self._reservations_file = os.path.join(self._storage_dir, "reservations.json")
        self._aggregations_file = os.path.join(self._storage_dir, "aggregations.json")

        self._plans_by_id: Dict[str, Plan] = {}
        self._plans_by_code: Dict[str, Plan] = {}
        self._entitlements_by_plan: Dict[str, List[PlanEntitlement]] = {}
        self._workspace_plans: Dict[str, WorkspacePlan] = {}  # workspace_id -> current WorkspacePlan
        self._events: List[UsageEvent] = []
        self._events_by_idempotency: Dict[str, UsageEvent] = {}  # f"{workspace_id}:{key}" -> event
        self._reservations_by_id: Dict[str, UsageReservation] = {}
        self._aggregations: Dict[str, float] = {}  # f"{workspace_id}:{period_key}:{metric_key}" -> float

        self._ensure_dirs()
        self._load_all()
        self._bootstrap_catalog_if_empty()

    def _ensure_dirs(self) -> None:
        os.makedirs(self._storage_dir, exist_ok=True)

    def _load_json(self, file_path: str, default: Any) -> Any:
        if not os.path.exists(file_path):
            return default
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to read %s, using default: %s", file_path, e)
            return default

    def _atomic_save(self, file_path: str, data: Any) -> None:
        temp_path = f"{file_path}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            shutil.move(temp_path, file_path)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            logger.error("Failed atomic save to %s: %s", file_path, e)
            raise

    def _load_all(self) -> None:
        with self._lock:
            # 1. Plans
            raw_plans = self._load_json(self._plans_file, [])
            for p in raw_plans:
                plan = Plan(**p)
                self._plans_by_id[plan.plan_id] = plan
                self._plans_by_code[plan.plan_code.lower()] = plan
                self._plans_by_code[plan.plan_code.upper()] = plan

            # 2. Entitlements
            raw_ent = self._load_json(self._entitlements_file, [])
            for e in raw_ent:
                ent = PlanEntitlement(**e)
                self._entitlements_by_plan.setdefault(ent.plan_id, []).append(ent)

            # 3. Workspace Plans
            raw_wp = self._load_json(self._workspace_plans_file, [])
            for wp in raw_wp:
                wplan = WorkspacePlan(**wp)
                self._workspace_plans[wplan.workspace_id] = wplan

            # 4. Usage Events
            raw_events = self._load_json(self._events_file, [])
            for rev in raw_events:
                evt = UsageEvent(**rev)
                self._events.append(evt)
                if evt.idempotency_key:
                    dedup_key = f"{evt.workspace_id}:{evt.idempotency_key}"
                    self._events_by_idempotency[dedup_key] = evt

            # 5. Reservations
            raw_res = self._load_json(self._reservations_file, [])
            for r in raw_res:
                res = UsageReservation(**r)
                self._reservations_by_id[res.reservation_id] = res

            # 6. Aggregations
            raw_aggs = self._load_json(self._aggregations_file, {})
            self._aggregations = raw_aggs

    def _bootstrap_catalog_if_empty(self) -> None:
        with self._lock:
            if not self._plans_by_id:
                logger.info("Bootstrapping default product plans catalog...")
                default_plans = get_default_plans()
                for p in default_plans:
                    self._plans_by_id[p.plan_id] = p
                    self._plans_by_code[p.plan_code.lower()] = p
                    self._plans_by_code[p.plan_code.upper()] = p

                default_entitlements = get_default_entitlements()
                for ent in default_entitlements:
                    self._entitlements_by_plan.setdefault(ent.plan_id, []).append(ent)

                self._persist_plans()
                self._persist_entitlements()
                logger.info("Successfully bootstrapped %d plans and %d entitlements", len(default_plans), len(default_entitlements))

    def _persist_plans(self) -> None:
        data = [p.model_dump() for p in self._plans_by_id.values()]
        self._atomic_save(self._plans_file, data)

    def _persist_entitlements(self) -> None:
        data = [e.model_dump() for ents in self._entitlements_by_plan.values() for e in ents]
        self._atomic_save(self._entitlements_file, data)

    def _persist_workspace_plans(self) -> None:
        data = [wp.model_dump() for wp in self._workspace_plans.values()]
        self._atomic_save(self._workspace_plans_file, data)

    def _persist_events(self) -> None:
        data = [e.model_dump() for e in self._events]
        self._atomic_save(self._events_file, data)

    def _persist_reservations(self) -> None:
        data = [r.model_dump() for r in self._reservations_by_id.values()]
        self._atomic_save(self._reservations_file, data)

    def _persist_aggregations(self) -> None:
        self._atomic_save(self._aggregations_file, self._aggregations)

    # ─────────────────────────────────────────────────────────
    # Plan Catalog Queries
    # ─────────────────────────────────────────────────────────

    def list_plans(self, active_only: bool = True) -> List[Plan]:
        with self._lock:
            plans = list(self._plans_by_id.values())
            if active_only:
                plans = [p for p in plans if p.status == PlanStatus.ACTIVE]
            return plans

    def get_plan(self, plan_id: str) -> Optional[Plan]:
        with self._lock:
            return self._plans_by_id.get(plan_id)

    def get_plan_by_code(self, plan_code: str) -> Optional[Plan]:
        with self._lock:
            return self._plans_by_code.get(plan_code.lower()) or self._plans_by_code.get(plan_code.upper())

    def get_default_plan(self) -> Plan:
        with self._lock:
            for p in self._plans_by_id.values():
                if p.is_default and p.status == PlanStatus.ACTIVE:
                    return p
            # Fallback to 'free', 'FREE' or first active
            if "FREE" in self._plans_by_code:
                return self._plans_by_code["FREE"]
            if "free" in self._plans_by_code:
                return self._plans_by_code["free"]
            active = [p for p in self._plans_by_id.values() if p.status == PlanStatus.ACTIVE]
            if active:
                return active[0]
            raise RuntimeError("No active plans available in system catalog")

    def save_plan(self, plan: Plan) -> Plan:
        with self._lock:
            plan.updated_at = datetime.now(timezone.utc).isoformat()
            self._plans_by_id[plan.plan_id] = plan
            self._plans_by_code[plan.plan_code.lower()] = plan
            self._plans_by_code[plan.plan_code.upper()] = plan
            self._persist_plans()
            return plan

    # ─────────────────────────────────────────────────────────
    # Entitlements
    # ─────────────────────────────────────────────────────────

    def get_plan_entitlements(self, plan_id: str) -> List[PlanEntitlement]:
        with self._lock:
            return list(self._entitlements_by_plan.get(plan_id, []))

    def get_plan_entitlement(self, plan_id: str, feature_key: str) -> Optional[PlanEntitlement]:
        with self._lock:
            for ent in self._entitlements_by_plan.get(plan_id, []):
                if ent.feature_key == feature_key or ent.feature_key.lower() == feature_key.lower():
                    return ent
            return None

    def save_entitlement(self, entitlement: PlanEntitlement) -> PlanEntitlement:
        with self._lock:
            entitlement.updated_at = datetime.now(timezone.utc).isoformat()
            ents = self._entitlements_by_plan.setdefault(entitlement.plan_id, [])
            replaced = False
            for idx, existing in enumerate(ents):
                if existing.feature_key == entitlement.feature_key:
                    ents[idx] = entitlement
                    replaced = True
                    break
            if not replaced:
                ents.append(entitlement)
            self._persist_entitlements()
            return entitlement

    # ─────────────────────────────────────────────────────────
    # Workspace Plan Assignment
    # ─────────────────────────────────────────────────────────

    def get_workspace_plan(self, workspace_id: str) -> Optional[WorkspacePlan]:
        with self._lock:
            return self._workspace_plans.get(workspace_id)

    def assign_workspace_plan(self, wp: WorkspacePlan) -> WorkspacePlan:
        with self._lock:
            wp.updated_at = datetime.now(timezone.utc).isoformat()
            self._workspace_plans[wp.workspace_id] = wp
            self._persist_workspace_plans()
            return wp

    # ─────────────────────────────────────────────────────────
    # Usage Events & Aggregations
    # ─────────────────────────────────────────────────────────

    def record_usage_event(self, event: UsageEvent) -> Tuple[UsageEvent, bool]:
        """
        Appends a usage event with strict idempotency.
        Returns (event, was_created). If idempotency_key already exists,
        the existing event is returned with was_created=False.
        """
        with self._lock:
            if event.idempotency_key:
                dedup_key = f"{event.workspace_id}:{event.idempotency_key}"
                existing = self._events_by_idempotency.get(dedup_key)
                if existing:
                    return existing, False
                self._events_by_idempotency[dedup_key] = event

            self._events.append(event)
            self._persist_events()

            # Increment in-memory rolled up aggregate
            # Derive period key from event timestamp (e.g. YYYY-MM)
            period_key = event.occurred_at[:7]
            agg_key = f"{event.workspace_id}:{period_key}:{event.metric_key}"
            current_agg = self._aggregations.get(agg_key, 0.0)
            self._aggregations[agg_key] = current_agg + event.quantity
            self._persist_aggregations()

            return event, True

    def list_usage_events(
        self,
        workspace_id: str,
        metric_key: Optional[str] = None,
        period_key: Optional[str] = None,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> Tuple[List[UsageEvent], int, Optional[str], bool]:
        with self._lock:
            filtered = [
                e for e in self._events
                if e.workspace_id == workspace_id
                and (not metric_key or e.metric_key == metric_key)
                and (not period_key or e.occurred_at.startswith(period_key))
            ]
            # Sort newest first
            filtered.sort(key=lambda x: x.occurred_at, reverse=True)
            total = len(filtered)

            start_idx = 0
            if cursor:
                for idx, ev in enumerate(filtered):
                    if ev.usage_event_id == cursor:
                        start_idx = idx + 1
                        break

            items = filtered[start_idx : start_idx + limit]
            has_more = (start_idx + limit) < total
            next_cursor = items[-1].usage_event_id if (has_more and items) else None
            return items, total, next_cursor, has_more

    def get_aggregate_quantity(self, workspace_id: str, period_key: str, metric_key: str) -> float:
        with self._lock:
            agg_key = f"{workspace_id}:{period_key}:{metric_key}"
            return self._aggregations.get(agg_key, 0.0)

    # ─────────────────────────────────────────────────────────
    # Concurrency-Safe Reservations
    # ─────────────────────────────────────────────────────────

    def create_reservation(self, reservation: UsageReservation) -> UsageReservation:
        with self._lock:
            self._reservations_by_id[reservation.reservation_id] = reservation
            self._persist_reservations()
            return reservation

    def get_reservation(self, reservation_id: str) -> Optional[UsageReservation]:
        with self._lock:
            return self._reservations_by_id.get(reservation_id)

    def finalize_reservation(self, reservation_id: str) -> Optional[UsageReservation]:
        with self._lock:
            res = self._reservations_by_id.get(reservation_id)
            if res and res.status == ReservationStatus.RESERVED:
                res.status = ReservationStatus.CONSUMED
                res.finalized_at = datetime.now(timezone.utc).isoformat()
                self._persist_reservations()
                return res
            return None

    def release_reservation(self, reservation_id: str) -> Optional[UsageReservation]:
        with self._lock:
            res = self._reservations_by_id.get(reservation_id)
            if res and res.status == ReservationStatus.RESERVED:
                res.status = ReservationStatus.RELEASED
                res.finalized_at = datetime.now(timezone.utc).isoformat()
                self._persist_reservations()
                return res
            return None

    def get_active_reserved_quantity(self, workspace_id: str, metric_key: str) -> float:
        """Returns sum of currently active, non-expired reservations for a metric."""
        with self._lock:
            now_iso = datetime.now(timezone.utc).isoformat()
            total = 0.0
            for r in self._reservations_by_id.values():
                if (
                    r.workspace_id == workspace_id
                    and r.metric_key == metric_key
                    and r.status == ReservationStatus.RESERVED
                    and r.expires_at > now_iso
                ):
                    total += r.quantity
            return total

    def cleanup_expired_reservations(self) -> int:
        with self._lock:
            now_iso = datetime.now(timezone.utc).isoformat()
            expired_count = 0
            for r in self._reservations_by_id.values():
                if r.status == ReservationStatus.RESERVED and r.expires_at <= now_iso:
                    r.status = ReservationStatus.EXPIRED
                    r.finalized_at = now_iso
                    expired_count += 1
            if expired_count > 0:
                self._persist_reservations()
            return expired_count


# Global singleton instance
usage_repo = UsageRepository()
