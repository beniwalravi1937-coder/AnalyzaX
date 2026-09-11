"""
Cleaning & Transformation API Schemas
Pydantic schemas for request/response validation across cleaning endpoints.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.engines.transformations.models import (
    CleaningRecommendation,
    DatasetVersion,
    DryRunResult,
    QualityComparison,
    StepSummary,
    TransformationAudit,
    TransformationPlan,
    TransformationPreview,
    TransformationStep,
)


class PlanUpdateRequest(BaseModel):
    steps: List[TransformationStep] = Field(default_factory=list)
    source_version_id: Optional[str] = None


class PreviewRequest(BaseModel):
    steps: List[TransformationStep] = Field(default_factory=list)
    source_version_id: Optional[str] = None
    preview_rows: int = Field(default=10, ge=1, le=100)


class DryRunRequest(BaseModel):
    steps: List[TransformationStep] = Field(default_factory=list)
    source_version_id: Optional[str] = None


class ApplyPlanRequest(BaseModel):
    plan_id: Optional[str] = None
    steps: Optional[List[TransformationStep]] = None
    source_version_id: Optional[str] = None
    version_label: Optional[str] = None


class ApplyPlanResponse(BaseModel):
    new_version: DatasetVersion
    comparison: QualityComparison
    audit: TransformationAudit


class VersionActivateResponse(BaseModel):
    active_version: DatasetVersion
    message: str


class VersionComparisonResponse(BaseModel):
    comparison: QualityComparison


class LineageResponse(BaseModel):
    dataset_id: str
    active_version_id: Optional[str]
    nodes: List[Dict[str, Any]]
    links: List[Dict[str, Any]]
