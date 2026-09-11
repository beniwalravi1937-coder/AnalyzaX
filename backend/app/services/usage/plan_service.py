"""
Plan Application Service for Phase 20.
Coordinates workspace plan assignment, effective plan resolution,
plan change audits, and plan comparison matrices.
"""

from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional, Union

from backend.app.engines.usage.catalog import Features, get_default_plans
from backend.app.engines.usage.models import (
    Plan,
    PlanComparisonItem,
    PlanComparisonResponse,
    PlanEntitlement,
    PlanStatus,
    PlanTier,
    WorkspacePlan,
)
from backend.app.engines.usage.repository import UsageRepository, usage_repo

logger = logging.getLogger("analyzax")


class PlanService:
    """Coordinates plan catalog and workspace plan assignments."""

    def __init__(
        self,
        repository: Optional[UsageRepository] = None,
        repo: Optional[UsageRepository] = None,
    ):
        self._repo = repository or repo or usage_repo

    def list_plans(self, active_only: bool = True) -> List[Plan]:
        """Lists available plans from catalog."""
        return self._repo.list_plans(active_only=active_only)

    def get_plan(self, plan_id: str) -> Optional[Plan]:
        """Retrieves a plan by its unique ID."""
        return self._repo.get_plan(plan_id)

    def get_plan_by_code(self, plan_code: str) -> Optional[Plan]:
        """Retrieves a plan by code (e.g. 'free', 'pro', 'team', 'enterprise')."""
        return self._repo.get_plan_by_code(plan_code)

    def get_workspace_plan(self, workspace_id: str) -> Plan:
        """
        Resolves the effective active Plan for a workspace.
        If no plan is assigned, automatically provisions the default FREE plan.
        """
        wp = self._repo.get_workspace_plan(workspace_id)
        if wp and wp.status == PlanStatus.ACTIVE:
            plan = self._repo.get_plan(wp.plan_id)
            if plan and plan.status == PlanStatus.ACTIVE:
                return plan

        # Auto-provision default plan: ENTERPRISE for ws_default (system seed), FREE for others
        if workspace_id == "ws_default":
            plan = self._repo.get_plan_by_code("ENTERPRISE") or self._repo.get_default_plan()
        else:
            plan = self._repo.get_default_plan()
        new_wp = WorkspacePlan(
            workspace_id=workspace_id,
            plan_id=plan.plan_id,
            plan_code=plan.plan_code,
            plan_version=plan.version,
            status=PlanStatus.ACTIVE,
            effective_from=datetime.now(timezone.utc).isoformat(),
            assigned_by="system",
        )
        self._repo.assign_workspace_plan(new_wp)
        logger.info("Auto-assigned default plan '%s' to workspace '%s'", plan.plan_code, workspace_id)
        return plan

    def get_workspace_assignment(self, workspace_id: str) -> WorkspacePlan:
        """Returns the raw WorkspacePlan record, provisioning if absent."""
        wp = self._repo.get_workspace_plan(workspace_id)
        if not wp or wp.status != PlanStatus.ACTIVE:
            self.get_workspace_plan(workspace_id)
            wp = self._repo.get_workspace_plan(workspace_id)
        return wp

    def assign_plan(
        self,
        workspace_id: str,
        plan_tier: Union[PlanTier, str],
        assigned_by: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> WorkspacePlan:
        """
        Assigns or changes a workspace plan.
        Preserves all historical usage and data; downgrades never delete resources.
        """
        code = plan_tier.value if isinstance(plan_tier, PlanTier) else str(plan_tier).upper()
        target_plan = self.get_plan_by_code(code)
        if not target_plan:
            raise ValueError(f"Unknown plan code: '{code}'")

        if target_plan.status != PlanStatus.ACTIVE:
            raise ValueError(f"Plan '{code}' is not active")

        existing_wp = self._repo.get_workspace_plan(workspace_id)
        current_plan_id = existing_wp.plan_id if existing_wp else None

        wp = WorkspacePlan(
            workspace_id=workspace_id,
            plan_id=target_plan.plan_id,
            plan_code=target_plan.plan_code,
            plan_version=target_plan.version,
            status=PlanStatus.ACTIVE,
            effective_from=datetime.now(timezone.utc).isoformat(),
            assigned_by=assigned_by,
        )
        assigned = self._repo.assign_workspace_plan(wp)

        logger.info(
            "Workspace '%s' plan changed from '%s' to '%s' (Assigned by: %s, Reason: %s)",
            workspace_id,
            current_plan_id,
            target_plan.plan_code,
            assigned_by,
            reason,
        )
        return assigned

    assign_workspace_plan = assign_plan

    def get_plan_entitlements(self, plan_id: str) -> List[PlanEntitlement]:
        """Retrieves all entitlement definitions for a plan."""
        return self._repo.get_plan_entitlements(plan_id)

    def get_feature_entitlement(self, workspace_id: str, feature_key: str) -> Optional[PlanEntitlement]:
        """Resolves specific feature entitlement for a workspace."""
        plan = self.get_workspace_plan(workspace_id)
        return self._repo.get_plan_entitlement(plan.plan_id, feature_key)

    get_entitlement = get_feature_entitlement

    def get_all_entitlements(self, workspace_id: str) -> Dict[str, PlanEntitlement]:
        """Resolves all feature entitlements for a workspace as a map."""
        plan = self.get_workspace_plan(workspace_id)
        entitlements = self._repo.get_plan_entitlements(plan.plan_id)
        result: Dict[str, PlanEntitlement] = {}
        for e in entitlements:
            result[e.feature_key] = e
            result[e.feature_key.lower()] = e
            result[e.feature_key.upper()] = e
        return result

    def get_plan_comparison_matrix(self) -> PlanComparisonResponse:
        """Builds a structured feature comparison matrix across all tiers."""
        plans = self.list_plans(active_only=True)
        plans_by_tier: Dict[PlanTier, Plan] = {p.tier: p for p in plans}

        free_plan = plans_by_tier.get(PlanTier.FREE)
        pro_plan = plans_by_tier.get(PlanTier.PRO)
        team_plan = plans_by_tier.get(PlanTier.TEAM)
        enterprise_plan = plans_by_tier.get(PlanTier.ENTERPRISE)

        def _fmt_ent(p: Optional[Plan], f_key: str) -> str:
            if not p:
                return "N/A"
            ent = self._repo.get_plan_entitlement(p.plan_id, f_key)
            if not ent or not ent.enabled:
                return "Not Included"
            if ent.value is None or ent.value is True:
                return "Unlimited" if ent.limit_type != "BOOLEAN" else "Included"
            if ent.unit:
                return f"{ent.value:,} {ent.unit}" if isinstance(ent.value, (int, float)) else f"{ent.value} {ent.unit}"
            return str(ent.value)

        feature_defs = [
            (Features.AI_ANALYST, "AI Analyst Inquiries", "AI"),
            (Features.MAX_DATASET_SIZE_MB, "Max Dataset File Size", "Storage"),
            (Features.STORAGE_LIMIT_BYTES, "Total Storage Capacity", "Storage"),
            (Features.DATASET_UPLOAD, "Monthly Dataset Uploads", "Storage"),
            (Features.MAX_PROJECTS, "Active Projects", "Workspace"),
            (Features.MAX_WORKSPACE_MEMBERS, "Team Members", "Collaboration"),
            (Features.SQL_ANALYTICS, "SQL Query Executions", "Analytics"),
            (Features.SQL_MAX_RESULT_ROWS, "Max SQL Result Rows", "Analytics"),
            (Features.MACHINE_LEARNING, "Machine Learning Training", "Analytics"),
            (Features.FORECASTING, "Time-Series Forecasting", "Analytics"),
            (Features.ADVANCED_STATISTICS, "Statistical Analyses", "Analytics"),
            (Features.EXPORTS, "Monthly Exports & Reports", "Exports"),
            (Features.PUBLIC_LINKS, "Public Shareable Links", "Collaboration"),
        ]

        comparisons: List[PlanComparisonItem] = []
        for f_key, display, cat in feature_defs:
            comparisons.append(
                PlanComparisonItem(
                    feature_key=f_key,
                    display_name=display,
                    category=cat,
                    free_value=_fmt_ent(free_plan, f_key),
                    pro_value=_fmt_ent(pro_plan, f_key),
                    team_value=_fmt_ent(team_plan, f_key),
                    enterprise_value=_fmt_ent(enterprise_plan, f_key),
                )
            )

        return PlanComparisonResponse(plans=plans, comparisons=comparisons)

    get_plan_comparison = get_plan_comparison_matrix


# Type alias for return tuple
from typing import Tuple as Tuple_WorkspacePlan_Plan

# Global singleton
plan_service = PlanService()
