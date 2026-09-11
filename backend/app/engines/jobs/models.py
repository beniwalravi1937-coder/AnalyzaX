"""
AnalyzaX — Phase 22: Background Job & Asynchronous Worker Domain Models.
Defines job lifecycle, retry semantics, and error classification.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RETRYING = "RETRYING"


class JobType(str, Enum):
    PROFILING = "PROFILING"
    EDA = "EDA"
    SQL = "SQL"
    STATISTICS = "STATISTICS"
    ML_TRAIN = "ML_TRAIN"
    FORECAST_TRAIN = "FORECAST_TRAIN"
    EXPORT = "EXPORT"
    REPORT = "REPORT"
    AI_ANALYST = "AI_ANALYST"
    NOTIFICATION_DISPATCH = "NOTIFICATION_DISPATCH"
    BILLING_SYNC = "BILLING_SYNC"


class JobPriority(int, Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


class TransientJobError(Exception):
    """Temporary failure (e.g. network timeout, rate limit, database busy). Eligible for retry."""
    pass


class PermanentJobError(Exception):
    """Fatal failure (e.g. invalid SQL, missing column, quota exceeded). Non-retryable."""
    pass


class Job(BaseModel):
    id: str
    job_type: JobType
    workspace_id: str
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL
    payload: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    last_error: Optional[str] = None
    error_code: Optional[str] = None
    attempts: int = 0
    max_retries: int = 3
    retry_delay_seconds: float = 2.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None

    def is_retryable(self) -> bool:
        """Determines if the job can be retried following a failure."""
        return self.attempts < self.max_retries
