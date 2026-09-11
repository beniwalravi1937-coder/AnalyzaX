"""
Plans & Entitlements REST API (Phase 20)
Mounted at /api/v1/plans and workspace plan endpoints
Exposes the plan catalog, feature comparison matrix, current entitlements, and plan mutation.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel

from backend.app.api.deps import get_current_user_optional, require_permission
from backend.app.engines.auth.models import User
from backend.app.engines.auth.permissions import Permissions
from backend.app.engines.usage.models import (
    Plan,
    PlanComparisonDTO,
    PlanComparisonResponse,
    PlanTier,
    WorkspacePlan,
)
from backend.app.services.usage import plan_service
from backend.app.services.workspace.workspace_service import workspace_service

router = APIRouter(tags=["plans"])


class PlanChangeRequest(BaseModel):
    plan_tier: PlanTier
    reason: Optional[str] = "User requested plan change"


def _resolve_target_workspace(
    workspace_id: Optional[str] = None,
    x_workspace_id: Optional[str] = None,
) -> str:
    ws_id = workspace_id or x_workspace_id
    if not ws_id:
        def_ws = workspace_service.get_or_create_default_workspace()
        ws_id = def_ws.workspace_id
    return ws_id


@router.get(
    "/plans",
    response_model=List[Plan],
    summary="List Plan Catalog",
    description="Returns all active product plans.",
)
def list_plans() -> List[Plan]:
    return plan_service.list_plans(active_only=True)


@router.get(
    "/plans/matrix",
    response_model=PlanComparisonResponse,
    summary="Get Plan Comparison Matrix",
    description="Returns side-by-side feature comparison specifications across all tiers.",
)
def get_plan_comparison_matrix() -> PlanComparisonResponse:
    return plan_service.get_plan_comparison()


@router.get(
    "/plans/current",
    summary="Get Current Workspace Plan & Entitlements",
    description="Returns the active plan, tier, period, and full feature entitlement dictionary for the current workspace.",
)
def get_current_plan(
    workspace_id: Optional[str] = Query(None, description="Workspace ID"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: Optional[User] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    target_ws = _resolve_target_workspace(workspace_id, x_workspace_id)
    wp = plan_service.get_workspace_assignment(target_ws)
    entitlements = plan_service.get_all_entitlements(target_ws)
    return {
        "workspace_id": target_ws,
        "workspace_plan_id": wp.workspace_plan_id,
        "plan_id": wp.plan_id,
        "plan_code": wp.plan_code,
        "status": wp.status.value,
        "effective_from": wp.effective_from,
        "effective_until": wp.effective_until,
        "downgrade_warning": wp.metadata.get("downgrade_warning"),
        "entitlements": {k: ent.model_dump() for k, ent in entitlements.items()},
    }


@router.get(
    "/workspaces/{workspace_id}/plan",
    summary="Get Workspace Plan",
    description="Returns the current plan details for a specific workspace.",
)
def get_workspace_plan_details(
    workspace_id: str,
    user: Optional[User] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    wp = plan_service.get_workspace_assignment(workspace_id)
    entitlements = plan_service.get_all_entitlements(workspace_id)
    return {
        "workspace_id": workspace_id,
        "workspace_plan_id": wp.workspace_plan_id,
        "plan_id": wp.plan_id,
        "plan_code": wp.plan_code,
        "status": wp.status.value,
        "effective_from": wp.effective_from,
        "effective_until": wp.effective_until,
        "downgrade_warning": wp.metadata.get("downgrade_warning"),
        "entitlements": {k: ent.model_dump() for k, ent in entitlements.items()},
    }


@router.post(
    "/workspaces/{workspace_id}/plan",
    summary="Assign or Change Workspace Plan",
    description="Changes workspace plan tier (FREE, PRO, TEAM, ENTERPRISE). Auditable, protects existing data on downgrade.",
)
def change_workspace_plan(
    workspace_id: str,
    body: PlanChangeRequest,
    user: Optional[User] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    assigned_by = user.user_id if user else "system_admin"
    wp = plan_service.assign_plan(
        workspace_id=workspace_id,
        plan_tier=body.plan_tier,
        assigned_by=assigned_by,
        reason=body.reason,
    )
    return {
        "success": True,
        "workspace_id": workspace_id,
        "plan_code": wp.plan_code,
        "status": wp.status.value,
        "downgrade_warning": wp.metadata.get("downgrade_warning"),
        "message": f"Successfully updated workspace plan to {wp.plan_code}",
    }
