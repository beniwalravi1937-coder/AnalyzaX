"""
AnalyzaX — Phase 22: Production PostgreSQL Connection Management.
Implements bounded connection pooling, query timeouts, pre-ping health validation,
and integration with telemetry metrics.
"""

import asyncio
import time
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.sql import text

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.metrics import metrics_collector

# Initialize Async SQLAlchemy engine with production connection bounds
engine = None
async_session_factory = None

if settings.DATABASE_URL:
    try:
        connect_args = {}
        if "asyncpg" in settings.DATABASE_URL:
            # Command timeout in seconds
            connect_args["command_timeout"] = max(1.0, settings.DB_STATEMENT_TIMEOUT_MS / 1000.0)

        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            future=True,
            pool_pre_ping=True,
            pool_size=getattr(settings, "DB_POOL_SIZE", 10),
            max_overflow=getattr(settings, "DB_MAX_OVERFLOW", 20),
            pool_timeout=getattr(settings, "DB_POOL_TIMEOUT", 30),
            pool_recycle=getattr(settings, "DB_POOL_RECYCLE", 1800),
            connect_args=connect_args,
        )
        async_session_factory = async_sessionmaker(
            engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )
        logger.info(
            f"PostgreSQL connection pool initialized (pool_size={settings.DB_POOL_SIZE}, max_overflow={settings.DB_MAX_OVERFLOW})"
        )
    except Exception as e:
        logger.warning(f"SQLAlchemy engine setup warning: {e}")
        engine = None
        async_session_factory = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injecting an active, bounded async database session."""
    if not async_session_factory:
        raise RuntimeError("Database session factory is not initialized")
    async with async_session_factory() as session:
        t0 = time.perf_counter()
        try:
            yield session
        except Exception:
            metrics_collector.record_db_query(
                duration_ms=(time.perf_counter() - t0) * 1000, error=True
            )
            raise
        else:
            metrics_collector.record_db_query(
                duration_ms=(time.perf_counter() - t0) * 1000, error=False
            )
        finally:
            await session.close()


async def check_database_status() -> dict:
    """
    Validates PostgreSQL connectivity with bounded timeout (1.5s).
    Returns status: 'connected', 'configured', or 'not_configured'.
    """
    if not settings.DATABASE_URL:
        return {"status": "not_configured", "message": "DATABASE_URL is not set"}

    if not engine:
        return {"status": "configured", "message": "Engine configuration present"}

    try:
        async def _ping():
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

        t0 = time.perf_counter()
        await asyncio.wait_for(_ping(), timeout=1.5)
        lat = round((time.perf_counter() - t0) * 1000, 2)
        metrics_collector.record_db_query(duration_ms=lat, error=False)
        return {
            "status": "connected",
            "latency_ms": lat,
            "message": "Successfully connected to PostgreSQL",
        }
    except Exception as e:
        logger.debug(f"Database connection check note: {e}")
        return {
            "status": "configured",
            "message": "Configured, but live database server not currently reachable",
        }
