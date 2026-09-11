"""
REST API Router for Phase 14 Dashboard, Insight Workspace, and Analytical Storytelling.
Mounted under /api/v1/dashboards.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.engines.dashboard.models import (
    ComponentCreateRequest,
    ComponentUpdateRequest,
    Dashboard,
    DashboardActionValidateRequest,
    DashboardActionValidateResponse,
    DashboardComponent,
    DashboardCreateRequest,
    DashboardDataResponse,
    DashboardDuplicateRequest,
    DashboardFilterValidateRequest,
    DashboardFilterValidateResponse,
    DashboardUpdateRequest,
    DashboardVersion,
)
from backend.app.services.dashboard_service import dashboard_service

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


@router.get(
    "",
    response_model=List[Dashboard],
    summary="List dashboards",
    description="Lists all saved dashboards with optional dataset filtering and name search.",
)
def list_dashboards(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    search: Optional[str] = Query(None, description="Search term in name/description"),
) -> List[Dashboard]:
    return dashboard_service.list_dashboards(dataset_id=dataset_id, search=search)


@router.post(
    "",
    response_model=Dashboard,
    status_code=status.HTTP_201_CREATED,
    summary="Create dashboard",
    description="Creates a new dashboard entity with optional starter layout templates.",
)
def create_dashboard(request: DashboardCreateRequest) -> Dashboard:
    return dashboard_service.create_dashboard(request)


@router.get(
    "/{dashboard_id}",
    response_model=Dashboard,
    summary="Get dashboard",
    description="Retrieves a single dashboard by ID.",
)
def get_dashboard(dashboard_id: str) -> Dashboard:
    return dashboard_service.get_dashboard(dashboard_id)


@router.put(
    "/{dashboard_id}",
    response_model=Dashboard,
    summary="Update dashboard",
    description="Updates dashboard state with optimistic concurrency control.",
)
def update_dashboard(
    dashboard_id: str,
    request: DashboardUpdateRequest,
) -> Dashboard:
    return dashboard_service.update_dashboard(dashboard_id, request)


@router.delete(
    "/{dashboard_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete dashboard",
    description="Deletes a dashboard by ID.",
)
def delete_dashboard(dashboard_id: str) -> Dict[str, Any]:
    deleted = dashboard_service.delete_dashboard(dashboard_id)
    return {"dashboard_id": dashboard_id, "deleted": deleted}


@router.post(
    "/{dashboard_id}/duplicate",
    response_model=Dashboard,
    status_code=status.HTTP_201_CREATED,
    summary="Duplicate dashboard",
    description="Duplicates a dashboard including layout, components, and provenance.",
)
def duplicate_dashboard(
    dashboard_id: str,
    request: DashboardDuplicateRequest,
) -> Dashboard:
    return dashboard_service.duplicate_dashboard(dashboard_id, request)


# ─────────────────────────────────────────────────────────────
# Versions & History
# ─────────────────────────────────────────────────────────────

@router.get(
    "/{dashboard_id}/versions",
    response_model=List[DashboardVersion],
    summary="List dashboard versions",
    description="Retrieves audit history and past version snapshots for a dashboard.",
)
def list_versions(dashboard_id: str) -> List[DashboardVersion]:
    return dashboard_service.list_versions(dashboard_id)


@router.get(
    "/{dashboard_id}/versions/{version_number}",
    response_model=DashboardVersion,
    summary="Get dashboard version snapshot",
    description="Retrieves a specific historic dashboard version snapshot.",
)
def get_version(dashboard_id: str, version_number: int) -> DashboardVersion:
    return dashboard_service.get_version(dashboard_id, version_number)


@router.post(
    "/{dashboard_id}/versions/{version_number}/restore",
    response_model=Dashboard,
    summary="Restore dashboard version",
    description="Restores a past dashboard version by appending a new version snapshot.",
)
def restore_version(dashboard_id: str, version_number: int) -> Dashboard:
    return dashboard_service.restore_version(dashboard_id, version_number)


# ─────────────────────────────────────────────────────────────
# Components Management
# ─────────────────────────────────────────────────────────────

@router.post(
    "/{dashboard_id}/components",
    response_model=DashboardComponent,
    status_code=status.HTTP_201_CREATED,
    summary="Add component",
    description="Adds an analytical or presentation component to the dashboard.",
)
def add_component(
    dashboard_id: str,
    request: ComponentCreateRequest,
) -> DashboardComponent:
    return dashboard_service.add_component(dashboard_id, request)


@router.put(
    "/{dashboard_id}/components/{component_id}",
    response_model=DashboardComponent,
    summary="Update component",
    description="Updates an existing dashboard component.",
)
def update_component(
    dashboard_id: str,
    component_id: str,
    request: ComponentUpdateRequest,
) -> DashboardComponent:
    return dashboard_service.update_component(dashboard_id, component_id, request)


@router.delete(
    "/{dashboard_id}/components/{component_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete component",
    description="Deletes a component from the dashboard.",
)
def delete_component(dashboard_id: str, component_id: str) -> Dict[str, Any]:
    deleted = dashboard_service.delete_component(dashboard_id, component_id)
    return {"dashboard_id": dashboard_id, "component_id": component_id, "deleted": deleted}


@router.post(
    "/{dashboard_id}/components/{component_id}/duplicate",
    response_model=DashboardComponent,
    status_code=status.HTTP_201_CREATED,
    summary="Duplicate component",
    description="Duplicates a component within the dashboard with an offset position.",
)
def duplicate_component(
    dashboard_id: str,
    component_id: str,
) -> DashboardComponent:
    return dashboard_service.duplicate_component(dashboard_id, component_id)


# ─────────────────────────────────────────────────────────────
# Data Hydration & Refresh
# ─────────────────────────────────────────────────────────────

@router.get(
    "/{dashboard_id}/data",
    response_model=DashboardDataResponse,
    summary="Get dashboard data",
    description="Hydrates bounded analytical data for all dashboard components.",
)
def get_dashboard_data(dashboard_id: str) -> DashboardDataResponse:
    return dashboard_service.get_dashboard_data(dashboard_id)


@router.post(
    "/{dashboard_id}/refresh",
    response_model=DashboardDataResponse,
    summary="Refresh dashboard data",
    description="Triggers a refresh of presentation and analytical data for components.",
)
def refresh_dashboard(
    dashboard_id: str,
    component_ids: Optional[List[str]] = None,
) -> DashboardDataResponse:
    return dashboard_service.refresh_dashboard(dashboard_id, component_ids)


# ─────────────────────────────────────────────────────────────
# Validation & Export
# ─────────────────────────────────────────────────────────────

@router.post(
    "/{dashboard_id}/filters/validate",
    response_model=DashboardFilterValidateResponse,
    summary="Validate dashboard filter",
    description="Validates a proposed filter against dataset columns and operators.",
)
def validate_filter(
    dashboard_id: str,
    request: DashboardFilterValidateRequest,
) -> DashboardFilterValidateResponse:
    return dashboard_service.validate_filter(request)


@router.post(
    "/{dashboard_id}/actions/validate",
    response_model=DashboardActionValidateResponse,
    summary="Validate dashboard action",
    description="Validates an AI Analyst or UI mutating action before application.",
)
def validate_action(
    dashboard_id: str,
    request: DashboardActionValidateRequest,
) -> DashboardActionValidateResponse:
    return dashboard_service.validate_action(request)


@router.get(
    "/{dashboard_id}/export",
    summary="Export dashboard",
    description="Exports dashboard configuration in JSON format.",
)
def export_dashboard(
    dashboard_id: str,
    format: str = Query("json", description="Export format: 'json'"),
) -> Dict[str, Any]:
    return dashboard_service.export_dashboard(dashboard_id, export_format=format)
