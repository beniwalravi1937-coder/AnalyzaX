"""
AnalyzaX — Phase 22: Health, Liveness & Readiness Endpoints.
Guarantees reliable orchestrator monitoring without cascading failure loops.
"""

import os
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Response, status

from backend.app.core.config import settings
from backend.app.core.database import check_database_status
from backend.app.core.metrics import metrics_collector
from backend.app.schemas.health import (
    DependencyStatus,
    HealthResponse,
    LivenessResponse,
    ReadinessResponse,
)
from backend.app.services.duckdb_service import duckdb_service

router = APIRouter(tags=["health"])

_START_TIME = time.time()


@router.get("/health/live", response_model=LivenessResponse)
async def get_liveness() -> LivenessResponse:
    """
    Process Liveness Probe (Kubernetes / Docker / Orchestrator).
    Answers: 'Is the Python ASGI process alive and running?'
    STRICT RULE: Never calls external databases or network services,
    guaranteeing that external outages do not cause cascading container restarts.
    """
    return LivenessResponse(
        status="alive",
        service="analyzax-backend",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/health/ready", response_model=ReadinessResponse)
async def get_readiness(response: Response) -> ReadinessResponse:
    """
    Instance Readiness Probe.
    Answers: 'Can this specific instance safely receive customer traffic?'
    Checks critical internal resources (DuckDB, local storage).
    Evaluates optional external services (Postgres, OpenRouter) without failing readiness
    unless running in strict production with required dependencies.
    """
    deps: list[DependencyStatus] = []
    is_ready = True

    # 1. DuckDB Engine (Critical)
    t0 = time.perf_counter()
    duck_status = duckdb_service.check_availability()
    duck_lat = round((time.perf_counter() - t0) * 1000, 2)
    duck_ok = duck_status.get("status") == "available"
    deps.append(
        DependencyStatus(
            name="duckdb",
            type="critical",
            status="healthy" if duck_ok else "unavailable",
            latency_ms=duck_lat,
            message=duck_status.get("message"),
        )
    )
    if not duck_ok:
        is_ready = False

    # 2. Durable Storage Root (Critical)
    storage_root = os.path.abspath(settings.DATA_STORAGE_ROOT)
    t0 = time.perf_counter()
    storage_writable = os.access(storage_root, os.W_OK) if os.path.exists(storage_root) else False
    storage_lat = round((time.perf_counter() - t0) * 1000, 2)
    deps.append(
        DependencyStatus(
            name="storage",
            type="critical",
            status="healthy" if storage_writable else "degraded",
            latency_ms=storage_lat,
            message=f"Root: {storage_root}",
        )
    )
    if not storage_writable:
        is_ready = False

    # 3. PostgreSQL Database (Critical if production with strict requirement, otherwise degraded/optional)
    t0 = time.perf_counter()
    db_status = await check_database_status()
    db_lat = round((time.perf_counter() - t0) * 1000, 2)
    db_connected = db_status.get("status") == "connected"
    is_prod = settings.APP_ENV.lower() in ("production", "prod")

    deps.append(
        DependencyStatus(
            name="postgresql",
            type="critical" if is_prod else "optional",
            status="healthy" if db_connected else db_status.get("status", "unavailable"),
            latency_ms=db_lat,
            message=db_status.get("message"),
        )
    )
    # If in strict production and database is configured but down, mark not ready
    if is_prod and settings.DATABASE_URL and not db_connected:
        is_ready = False

    # 4. AI Provider (Optional)
    deps.append(
        DependencyStatus(
            name="ai_provider",
            type="optional",
            status="healthy" if settings.AI_PROVIDER != "disabled" else "not_configured",
            message=f"Provider: {settings.AI_PROVIDER}",
        )
    )

    # 5. Billing Provider (Optional)
    deps.append(
        DependencyStatus(
            name="billing_provider",
            type="optional",
            status="healthy" if settings.BILLING_ENABLED else "not_configured",
            message=f"Provider: {settings.BILLING_PROVIDER}",
        )
    )

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ready" if is_ready else "unready",
        service="analyzax-backend",
        environment=settings.APP_ENV,
        is_ready=is_ready,
        dependencies=deps,
    )


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """
    Comprehensive System Health & Telemetry Endpoint.
    Returns engine versions, storage status, environment, uptime, and database status.
    """
    duckdb_info = duckdb_service.check_availability()
    db_info = await check_database_status()
    storage_root = os.path.abspath(settings.DATA_STORAGE_ROOT)
    storage_ok = os.access(storage_root, os.W_OK) if os.path.exists(storage_root) else False

    uptime = round(time.time() - _START_TIME, 1)

    return HealthResponse(
        status="ok",
        service="analyzax-backend",
        version=settings.RELEASE_VERSION,
        release_version=settings.RELEASE_VERSION,
        commit_sha=settings.RELEASE_COMMIT_SHA,
        environment=settings.APP_ENV,
        uptime_seconds=uptime,
        database=db_info.get("status", "not_configured"),
        duckdb=duckdb_info.get("status", "unavailable"),
        duckdb_version=duckdb_info.get("version"),
        storage="available" if storage_ok else "unavailable",
    )
