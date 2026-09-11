from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.health import get_health, get_liveness, get_readiness
from backend.app.api.v1.observability import get_prometheus_metrics
from backend.app.api.v1.router import api_v1_router
from backend.app.core.config import settings
from backend.app.core.errors import register_exception_handlers
from backend.app.core.logging import logger
from backend.app.core.middleware.correlation import CorrelationMiddleware
from backend.app.core.middleware.metrics_middleware import MetricsMiddleware
from backend.app.core.middleware.security import RateLimitMiddleware, SecurityHeadersMiddleware
from backend.app.core.migrations.runner import migration_runner
from backend.app.engines.jobs.shutdown import register_signal_handlers
from backend.app.engines.jobs.worker import worker_pool
from backend.app.services.dataset_service import dataset_service
from backend.app.services.duckdb_service import duckdb_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode (v{settings.RELEASE_VERSION})...")

    # Install OS termination signal handlers
    register_signal_handlers()

    # 1. Run versioned migrations
    try:
        applied = migration_runner.migrate()
        if applied:
            logger.info(f"Applied {len(applied)} database schema migrations.")
    except Exception as e:
        logger.error(f"Migration failure on startup: {e}", exc_info=True)

    # 2. Verify DuckDB analytical foundation
    duckdb_status = duckdb_service.check_availability()
    logger.info(f"DuckDB Engine Startup Check: {duckdb_status}")

    # 3. Re-register existing active dataset views into DuckDB
    dataset_service.re_register_all_views()

    # 4. Bootstrap workspace and run non-destructive migration of historical assets
    from backend.app.services.workspace.migration_service import migration_service
    mig_res = migration_service.run_initial_migration()
    logger.info(f"Workspace initial migration completed: {mig_res}")

    # 5. Bootstrap initial admin and migrate ownership to RBAC foundation
    from backend.app.services.auth.auth_migration_service import auth_migration_service
    auth_mig_res = auth_migration_service.bootstrap_admin_and_migrate()
    logger.info(f"Auth initial migration completed: {auth_mig_res}")

    # 6. Start background job worker pool
    worker_pool.start()

    yield

    logger.info("Initiating application shutdown sequence...")
    # Drain and stop workers
    worker_pool.stop()
    # Close DuckDB
    duckdb_service.close()
    logger.info(f"{settings.APP_NAME} shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    description="AnalyzaX — AI-Powered End-to-End Data Analytics Platform",
    version=settings.RELEASE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 1. Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware)

# 2. Hardened Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# 3. Request Metrics Telemetry Middleware
app.add_middleware(MetricsMiddleware)

# 4. Distributed Correlation & Request ID Middleware
app.add_middleware(CorrelationMiddleware)

# 5. Explicit CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 6. GZip Compression Middleware (compresses responses > 1KB)
from starlette.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1024)

# Register centralized exception handlers
register_exception_handlers(app)

# Mount API v1 router
app.include_router(api_v1_router)

# Mount direct root health and telemetry probes (for orchestrators and scrapers)
app.add_api_route("/health", get_health, methods=["GET"], tags=["health"])
app.add_api_route("/health/live", get_liveness, methods=["GET"], tags=["health"])
app.add_api_route("/health/ready", get_readiness, methods=["GET"], tags=["health"])
app.add_api_route("/metrics", get_prometheus_metrics, methods=["GET"], tags=["observability"])


@app.get("/", tags=["root"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "environment": settings.APP_ENV,
        "version": settings.RELEASE_VERSION,
        "health_check": "/health",
        "docs": "/docs",
    }
