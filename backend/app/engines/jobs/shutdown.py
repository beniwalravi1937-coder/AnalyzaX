"""
AnalyzaX — Phase 22: Graceful Process Shutdown Handler.
Handles OS signals (SIGTERM, SIGINT) to safely drain background tasks,
flush metrics, and close open database and engine connections.
"""

import signal
import sys
from typing import Callable, List

from backend.app.core.logging import logger
from backend.app.engines.jobs.worker import worker_pool
from backend.app.services.duckdb_service import duckdb_service

_shutdown_hooks: List[Callable[[], None]] = []


def register_shutdown_hook(hook: Callable[[], None]) -> None:
    """Registers a callback executed during graceful termination."""
    _shutdown_hooks.append(hook)


def trigger_graceful_shutdown(signum: int = signal.SIGTERM, frame: any = None) -> None:
    """Executes registered shutdown procedures in order."""
    sig_name = signal.Signals(signum).name if hasattr(signal, "Signals") else str(signum)
    logger.info(f"Received termination signal [{sig_name}]. Commencing graceful shutdown...")

    # 1. Stop Worker Pool and drain jobs
    try:
        worker_pool.stop(timeout_seconds=3.0)
    except Exception as e:
        logger.warning(f"Error stopping worker pool: {e}")

    # 2. Run custom registered hooks
    for hook in _shutdown_hooks:
        try:
            hook()
        except Exception as e:
            logger.warning(f"Error in shutdown hook: {e}")

    # 3. Close DuckDB Connections
    try:
        duckdb_service.close()
    except Exception as e:
        logger.warning(f"Error closing DuckDB: {e}")

    logger.info("Graceful shutdown complete.")


def register_signal_handlers() -> None:
    """Installs SIGTERM and SIGINT listeners where supported."""
    try:
        signal.signal(signal.SIGTERM, trigger_graceful_shutdown)
        signal.signal(signal.SIGINT, trigger_graceful_shutdown)
    except Exception as e:
        logger.debug(f"Signal registration note: {e}")
