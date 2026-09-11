from fastapi import APIRouter

from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.cleaning import router as cleaning_router
from backend.app.api.v1.datasets import router as datasets_router
from backend.app.api.v1.eda import router as eda_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.members import router as members_router
from backend.app.api.v1.sql import router as sql_router
from backend.app.api.v1.versions import router as versions_router
from backend.app.api.v1.statistics import router as statistics_router
from backend.app.api.v1.visualizations import router as visualizations_router
from backend.app.api.v1.ml import router as ml_router
from backend.app.api.v1.forecasting import router as forecasting_router
from backend.app.api.v1.ai_analyst import router as ai_analyst_router
from backend.app.api.v1.dashboards import router as dashboards_router
from backend.app.api.v1.exports import router as exports_router
from backend.app.api.v1.workspaces import router as workspaces_router
from backend.app.api.v1.projects import router as projects_router
from backend.app.api.v1.assets import router as assets_router
from backend.app.api.v1.invitations import router as invitations_router
from backend.app.api.v1.notifications import router as notifications_router
from backend.app.api.v1.notification_preferences import router as notification_preferences_router
from backend.app.api.v1.activity import router as activity_router
from backend.app.api.v1.project_members import router as project_members_router
from backend.app.api.v1.search import router as search_router
from backend.app.api.v1.share_links import router as share_links_router
from backend.app.api.v1.shared import router as shared_router
from backend.app.api.v1.shares import router as shares_router

from backend.app.api.v1.plans import router as plans_router
from backend.app.api.v1.usage import router as usage_router
from backend.app.api.v1.billing import router as billing_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mount active v1 routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(members_router)
api_v1_router.include_router(invitations_router)
api_v1_router.include_router(project_members_router)
api_v1_router.include_router(shares_router)
api_v1_router.include_router(share_links_router)
api_v1_router.include_router(shared_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(notification_preferences_router)
api_v1_router.include_router(activity_router)
api_v1_router.include_router(datasets_router)
api_v1_router.include_router(cleaning_router)
api_v1_router.include_router(versions_router)
api_v1_router.include_router(eda_router)
api_v1_router.include_router(sql_router)
api_v1_router.include_router(visualizations_router)
api_v1_router.include_router(statistics_router)
api_v1_router.include_router(ml_router)
api_v1_router.include_router(forecasting_router)
api_v1_router.include_router(ai_analyst_router)
api_v1_router.include_router(dashboards_router)
api_v1_router.include_router(exports_router)
api_v1_router.include_router(workspaces_router)
api_v1_router.include_router(projects_router)
api_v1_router.include_router(assets_router)
api_v1_router.include_router(search_router)
api_v1_router.include_router(usage_router)
api_v1_router.include_router(plans_router)
api_v1_router.include_router(billing_router)

from backend.app.api.v1.observability import router as observability_router
api_v1_router.include_router(observability_router)

from backend.app.api.v1.storage import router as storage_router
api_v1_router.include_router(storage_router)

from backend.app.api.v1.governance import router as governance_router
api_v1_router.include_router(governance_router)

# Phase 25 — Advanced AI Product Intelligence & Semantic Governance
from backend.app.api.v1.metrics import router as metrics_router
api_v1_router.include_router(metrics_router)

from backend.app.api.v1.insights import router as insights_router
api_v1_router.include_router(insights_router)

from backend.app.api.v1.ai_copilot import router as ai_copilot_router
api_v1_router.include_router(ai_copilot_router)

