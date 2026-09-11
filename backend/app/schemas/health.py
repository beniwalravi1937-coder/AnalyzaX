from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LivenessResponse(BaseModel):
    status: str = Field(default="alive", description="Process liveness indicator")
    service: str = Field(default="analyzax-backend", description="Service name")
    timestamp: str


class DependencyStatus(BaseModel):
    name: str
    type: str  # "critical" | "optional"
    status: str  # "healthy" | "degraded" | "unavailable" | "not_configured"
    latency_ms: Optional[float] = None
    message: Optional[str] = None


class ReadinessResponse(BaseModel):
    status: str = Field(default="ready", description="Service readiness: ready or unready")
    service: str = Field(default="analyzax-backend")
    environment: str
    is_ready: bool
    dependencies: List[DependencyStatus] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Overall health status")
    service: str = Field(default="analyzax-backend", description="Service identifier")
    version: str = Field(default="1.0.0", description="Backend application version")
    release_version: Optional[str] = None
    commit_sha: Optional[str] = None
    environment: Optional[str] = None
    uptime_seconds: Optional[float] = None
    database: str = Field(
        default="not_configured",
        description="PostgreSQL metadata status: connected, configured, or not_configured",
    )
    duckdb: str = Field(
        default="available",
        description="DuckDB analytical engine status: available or unavailable",
    )
    duckdb_version: Optional[str] = Field(
        default=None,
        description="Installed DuckDB engine version",
    )
    storage: Optional[str] = Field(
        default="available",
        description="Durable storage status",
    )


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class StandardErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
