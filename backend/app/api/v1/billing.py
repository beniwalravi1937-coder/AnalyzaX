"""
Billing & Subscriptions REST API (Phase 21).
Mounted at /api/v1/billing.
Enforces RBAC permissions, cross-workspace IDOR protection,
monetary integer minor units, and secure webhook intake.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request, status

from backend.app.api.deps import (
    get_current_user,
    get_current_user_optional,
    require_permission,
)
from backend.app.core.config import settings
from backend.app.engines.auth.models import User
from backend.app.engines.auth.permissions import Permissions
from backend.app.engines.billing import (
    BillingCustomer,
    BillingOverviewResponse,
    BillingPrice,
    BillingReconciliationReport,
    CancelSubscriptionRequest,
    ChangeSubscriptionRequest,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    Invoice,
    InvoiceListResponse,
    Payment,
    PortalSessionResponse,
    Subscription,
)
from backend.app.services.billing import (
    catalog_service,
    checkout_service,
    customer_service,
    invoice_service,
    portal_service,
    reconciliation_service,
    subscription_service,
    webhook_service,
)
from backend.app.services.workspace.workspace_service import workspace_service

router = APIRouter(prefix="/billing", tags=["billing"])


def _resolve_target_workspace(
    workspace_id: Optional[str] = None,
    x_workspace_id: Optional[str] = None,
) -> str:
    ws_id = workspace_id or x_workspace_id
    if not ws_id:
        def_ws = workspace_service.get_or_create_default_workspace()
        ws_id = def_ws.workspace_id
    return ws_id


# ─────────────────────────────────────────────────────────────
# Public / Discovery Endpoints
# ─────────────────────────────────────────────────────────────

@router.get(
    "/config",
    summary="Get Billing Configuration",
    description="Returns public billing system capabilities and active provider information.",
)
def get_billing_config() -> Dict[str, Any]:
    return {
        "enabled": getattr(settings, "BILLING_ENABLED", True),
        "provider": getattr(settings, "BILLING_PROVIDER", "sandbox"),
        "currency": getattr(settings, "BILLING_CURRENCY", "USD"),
        "portal_supported": True,
        "grace_period_days": getattr(settings, "BILLING_GRACE_PERIOD_DAYS", 7),
    }


@router.get(
    "/prices",
    response_model=List[BillingPrice],
    summary="List Pricing Catalog",
    description="Returns all active commercial product plan prices.",
)
def list_prices() -> List[BillingPrice]:
    return catalog_service.list_prices(active_only=True)


# ─────────────────────────────────────────────────────────────
# Workspace-Scoped Billing Endpoints
# ─────────────────────────────────────────────────────────────

@router.get(
    "/overview",
    response_model=BillingOverviewResponse,
    summary="Get Workspace Billing Overview",
    description="Returns full unified billing overview including active subscription, customer, pricing, and invoices.",
)
def get_billing_overview(
    request: Request,
    workspace_id: Optional[str] = Query(None),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    current_user: User = Depends(get_current_user),
) -> BillingOverviewResponse:
    ws_id = _resolve_target_workspace(workspace_id, x_workspace_id)
    # Check permissions
    from backend.app.services.auth.authorization_service import authorization_service
    can_manage = authorization_service.can(current_user.user_id, Permissions.BILLING_MANAGE, workspace_id=ws_id)
    can_view = authorization_service.can(current_user.user_id, Permissions.BILLING_READ, workspace_id=ws_id)
    if not can_view and not can_manage:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view billing details for this workspace.",
        )

    return subscription_service.get_billing_overview(ws_id, can_manage=can_manage)


@router.get(
    "/customer",
    response_model=Optional[BillingCustomer],
    summary="Get Billing Customer",
)
def get_billing_customer(
    workspace_id: Optional[str] = Query(None),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(require_permission(Permissions.BILLING_READ)),
) -> Optional[BillingCustomer]:
    ws_id = _resolve_target_workspace(workspace_id, x_workspace_id)
    return customer_service.get_customer(ws_id)


@router.get(
    "/subscription",
    response_model=Optional[Subscription],
    summary="Get Workspace Subscription",
)
def get_subscription(
    workspace_id: Optional[str] = Query(None),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(require_permission(Permissions.BILLING_READ)),
) -> Optional[Subscription]:
    ws_id = _resolve_target_workspace(workspace_id, x_workspace_id)
    return subscription_service.get_subscription(ws_id)


# ─────────────────────────────────────────────────────────────
# Checkout & Mutation Endpoints
# ─────────────────────────────────────────────────────────────

@router.post(
    "/checkout",
    response_model=CheckoutSessionResponse,
    summary="Create Checkout Session",
    description="Initiates hosted checkout session on billing provider. Validates plan tier and price authoritatively.",
)
def create_checkout_session(
    payload: CheckoutSessionRequest,
    workspace_id: Optional[str] = Query(None),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(require_permission(Permissions.BILLING_CHECKOUT)),
) -> CheckoutSessionResponse:
    ws_id = _resolve_target_workspace(workspace_id, x_workspace_id)
    try:
        return checkout_service.create_checkout_session(
            workspace_id=ws_id,
            plan_code=payload.plan_code,
            interval=payload.interval,
            user_email=user.email,
            user_name=user.display_name,
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
            actor_id=user.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/checkout/complete-sandbox",
    summary="Complete Sandbox Checkout",
    description="Development/test endpoint: simulates completing checkout and triggers verified webhook processing.",
)
def complete_sandbox_checkout(
    payload: Dict[str, Any] = Body(...),
    workspace_id: Optional[str] = Query(None),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(require_permission(Permissions.BILLING_CHECKOUT)),
) -> Dict[str, Any]:
    ws_id = _resolve_target_workspace(workspace_id, x_workspace_id)
    plan_code = payload.get("plan_code", "PRO").upper()
    interval = payload.get("interval", "month")
    session_id = payload.get("session_id", "cs_sbx_mock")

    from backend.app.engines.billing import SandboxBillingProvider, get_billing_provider
    provider = get_billing_provider()
    if not isinstance(provider, SandboxBillingProvider):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sandbox checkout helper is only supported in sandbox mode.",
        )

    # Ensure customer
    cust = customer_service.get_or_create_customer(ws_id, email=user.email, name=user.display_name)
    from backend.app.engines.billing.models import BillingInterval
    price = catalog_service.resolve_price(plan_code, BillingInterval(interval))

    event_payload = provider.simulate_checkout_completed(
        session_id=session_id,
        workspace_id=ws_id,
        customer_id=cust.external_customer_id,
        plan_code=plan_code,
        price_id=price.billing_price_id,
        amount_minor=price.amount_minor_units,
        interval=interval,
    )

    # Sign webhook and process
    import json
    body_bytes = json.dumps(event_payload).encode("utf-8")
    sig = provider.generate_signature(body_bytes)
    success, msg, evt_id = webhook_service.process_webhook(
        provider_name="sandbox",
        payload_bytes=body_bytes,
        headers={"stripe-signature": sig},
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg)

    # Return updated subscription
    sub = subscription_service.get_subscription(ws_id)
    return {
        "status": "success",
        "message": f"Successfully activated {plan_code} plan for workspace {ws_id}",
        "subscription": sub.model_dump() if sub else None,
    }


@router.post(
    "/subscription/change",
    response_model=Subscription,
    summary="Change Subscription Tier",
    description="Upgrades or downgrades active subscription tier on provider.",
)
def change_subscription(
    payload: ChangeSubscriptionRequest,
    workspace_id: Optional[str] = Query(None),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(require_permission(Permissions.SUBSCRIPTION_CHANGE)),
) -> Subscription:
    ws_id = _resolve_target_workspace(workspace_id, x_workspace_id)
    try:
        return subscription_service.change_subscription(
            workspace_id=ws_id,
            new_plan_code=payload.new_plan_code,
            new_interval=payload.new_interval,
            proration_behavior=payload.proration_behavior,
            actor_id=user.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/subscription/cancel",
    response_model=Subscription,
    summary="Cancel Subscription",
    description="Cancels active subscription (either at period end or immediately).",
)
def cancel_subscription(
    payload: CancelSubscriptionRequest,
    workspace_id: Optional[str] = Query(None),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(require_permission(Permissions.SUBSCRIPTION_CANCEL)),
) -> Subscription:
    ws_id = _resolve_target_workspace(workspace_id, x_workspace_id)
    try:
        return subscription_service.cancel_subscription(
            workspace_id=ws_id,
            cancel_at_period_end=payload.cancel_at_period_end,
            reason=payload.reason,
            actor_id=user.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/subscription/resume",
    response_model=Subscription,
    summary="Resume Canceled Subscription",
    description="Resumes a subscription that was set to cancel at period end.",
)
def resume_subscription(
    workspace_id: Optional[str] = Query(None),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(require_permission(Permissions.SUBSCRIPTION_CHANGE)),
) -> Subscription:
    ws_id = _resolve_target_workspace(workspace_id, x_workspace_id)
    try:
        return subscription_service.resume_subscription(ws_id, actor_id=user.user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Invoices & History Endpoints
# ─────────────────────────────────────────────────────────────

@router.get(
    "/invoices",
    response_model=InvoiceListResponse,
    summary="List Workspace Invoices",
)
def list_invoices(
    workspace_id: Optional[str] = Query(None),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_permission(Permissions.INVOICE_READ)),
) -> InvoiceListResponse:
    ws_id = _resolve_target_workspace(workspace_id, x_workspace_id)
    return invoice_service.list_invoices(ws_id, limit=limit, offset=offset)


@router.get(
    "/payments",
    response_model=List[Payment],
    summary="List Workspace Payments",
)
def list_payments(
    workspace_id: Optional[str] = Query(None),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(require_permission(Permissions.INVOICE_READ)),
) -> List[Payment]:
    ws_id = _resolve_target_workspace(workspace_id, x_workspace_id)
    return invoice_service.list_payments(ws_id)


@router.post(
    "/portal",
    response_model=PortalSessionResponse,
    summary="Create Billing Portal Session",
    description="Generates short-lived session URL to hosted billing portal for self-serve payment updates.",
)
def create_portal_session(
    return_url: Optional[str] = Query(None),
    workspace_id: Optional[str] = Query(None),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(require_permission(Permissions.BILLING_MANAGE)),
) -> PortalSessionResponse:
    ws_id = _resolve_target_workspace(workspace_id, x_workspace_id)
    try:
        return portal_service.create_portal_session(ws_id, return_url=return_url)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Webhooks & Reconciliation
# ─────────────────────────────────────────────────────────────

@router.post(
    "/webhooks/{provider}",
    summary="Ingest Payment Gateway Webhook",
    description="Cryptographically verifies raw signature and idempotently processes event transitions.",
)
async def handle_webhook(
    provider: str,
    request: Request,
) -> Dict[str, Any]:
    payload_bytes = await request.body()
    headers = dict(request.headers)

    success, msg, event_id = webhook_service.process_webhook(
        provider_name=provider,
        payload_bytes=payload_bytes,
        headers=headers,
    )

    if not success:
        if msg == "invalid_signature":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return {"received": True, "status": msg, "event_id": event_id}


@router.post(
    "/reconcile",
    response_model=BillingReconciliationReport,
    summary="Run Billing Reconciliation",
    description="Audits consistency between internal database and payment gateway state.",
)
def reconcile_billing(
    workspace_id: Optional[str] = Query(None),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(require_permission(Permissions.BILLING_MANAGE)),
) -> BillingReconciliationReport:
    ws_id = workspace_id or x_workspace_id
    if ws_id:
        return reconciliation_service.reconcile_workspace(ws_id)
    return reconciliation_service.reconcile_all()
