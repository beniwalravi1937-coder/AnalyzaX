import threading
from contextlib import contextmanager
from typing import Any, Generator, Optional

import duckdb

from backend.app.core.config import settings
from backend.app.core.errors import DuckDBInitializationError
from backend.app.core.logging import logger


class DuckDBService:
    """
    Service abstraction for DuckDB analytical engine.
    Manages connection lifecycle, memory limits, and thread-safe execution.
    """

    _instance: Optional["DuckDBService"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "DuckDBService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DuckDBService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        self._db_path = settings.DUCKDB_DATABASE_PATH
        self._memory_limit = settings.DUCKDB_MEMORY_LIMIT
        self._threads = settings.DUCKDB_THREADS
        self._primary_connection: Optional[duckdb.DuckDBPyConnection] = None
        self._connection_lock = threading.Lock()
        self._initialize_engine()
        self._initialized = True

    def _initialize_engine(self) -> None:
        try:
            # Create the initial verification connection
            conn = duckdb.connect(database=self._db_path)
            conn.execute(f"SET memory_limit = '{self._memory_limit}';")
            conn.execute(f"SET threads = {self._threads};")
            # Verify basic arithmetic & execution
            result = conn.execute("SELECT 1 AS ready;").fetchone()
            if not result or result[0] != 1:
                raise RuntimeError("DuckDB verification query returned unexpected result")
            self._primary_connection = conn
            logger.info("DuckDB analytical engine successfully initialized")
        except Exception as e:
            logger.error(f"Failed to initialize DuckDB engine: {e}")
            raise DuckDBInitializationError(str(e)) from e

    @contextmanager
    def get_connection(self) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """
        Thread-safe context manager providing an isolated cursor for concurrent analytical queries.
        Cursor creation is thread-safe; query execution on independent cursors proceeds concurrently.
        """
        if not self._primary_connection:
            self._initialize_engine()

        with self._connection_lock:
            if not self._primary_connection:
                raise DuckDBInitializationError("DuckDB engine is not initialized")
            cursor = self._primary_connection.cursor()

        try:
            yield cursor
        finally:
            try:
                cursor.close()
            except Exception:
                pass

    @contextmanager
    def get_exclusive_connection(self) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """Exclusive lock connection for DDL, table registration, or view updates."""
        if not self._primary_connection:
            self._initialize_engine()

        with self._connection_lock:
            if not self._primary_connection:
                raise DuckDBInitializationError("DuckDB engine is not initialized")
            cursor = self._primary_connection.cursor()
            try:
                yield cursor
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass

    def check_availability(self) -> dict[str, Any]:
        """
        Health check verifying DuckDB engine is ready for analytical queries.
        """
        try:
            with self.get_connection() as conn:
                version = conn.execute("SELECT version();").fetchone()[0]
                test_exec = conn.execute("SELECT 42 AS test_value;").fetchone()[0]
                if test_exec == 42:
                    return {
                        "status": "available",
                        "version": str(version),
                        "message": "DuckDB engine responsive and operational",
                    }
                return {
                    "status": "unavailable",
                    "message": "Engine check failed verification assertion",
                }
        except Exception as e:
            logger.warning(f"DuckDB health check failed: {e}")
            return {
                "status": "unavailable",
                "message": str(e),
            }

    def close(self) -> None:
        with self._connection_lock:
            if self._primary_connection:
                try:
                    self._primary_connection.close()
                except Exception as e:
                    logger.debug(f"Error closing DuckDB: {e}")
                self._primary_connection = None
                logger.info("DuckDB analytical engine closed")


duckdb_service = DuckDBService()
