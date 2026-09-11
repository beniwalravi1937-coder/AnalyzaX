"""
Cleaning & Transformation API Router
Provides endpoints for recommendations, plan building, previews, dry runs, and execution.
"""

from typing import List
from fastapi import APIRouter, HTTPException, Query

from backend.app.core.logging import logger
from backend.app.engines.transformations.models import (
    CleaningRecommendation,
    TransformationPlan,
    TransformationPreview,
    DryRunResult,
    PlanStatus,
)
from backend.app.schemas.cleaning import (
    ApplyPlanRequest,
    ApplyPlanResponse,
    DryRunRequest,
    PlanUpdateRequest,
    PreviewRequest,
)
from backend.app.services.cleaning import (
    plan_service,
    recommendation_service,
    version_service,
)
from backend.app.services.dataset_service import dataset_service

router = APIRouter(prefix="/cleaning", tags=["Cleaning & Transformations"])


@router.get(
    "/recommendations/{dataset_id}",
    response_model=List[CleaningRecommendation],
    summary="Get prioritized cleaning recommendations derived from quality audits",
)
async def get_cleaning_recommendations(
    dataset_id: str,
    force_refresh: bool = Query(default=False, description="Force re-evaluation of quality issues"),
):
    dataset = dataset_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    try:
        recommendations = recommendation_service.generate_recommendations(
            dataset_id=dataset_id,
            force_refresh=force_refresh,
        )
        return recommendations
    except Exception as e:
        logger.error(f"Failed to generate recommendations for {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")


@router.get(
    "/plan/{dataset_id}",
    response_model=TransformationPlan,
    summary="Get current draft transformation plan for a dataset",
)
async def get_transformation_plan(dataset_id: str):
    dataset = dataset_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    try:
        plan = plan_service.get_or_create_plan_for_dataset(dataset_id)
        return plan
    except Exception as e:
        logger.error(f"Failed to retrieve plan for {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve plan: {str(e)}")


@router.post(
    "/plan/{dataset_id}",
    response_model=TransformationPlan,
    summary="Update and persist draft transformation plan",
)
async def update_transformation_plan(dataset_id: str, req: PlanUpdateRequest):
    dataset = dataset_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    try:
        plan = plan_service.get_or_create_plan_for_dataset(
            dataset_id=dataset_id,
            source_version_id=req.source_version_id,
        )
        plan.steps = req.steps
        if req.source_version_id:
            plan.source_version_id = req.source_version_id
        plan.status = PlanStatus.DRAFT
        saved = plan_service.save_plan(plan)
        return saved
    except Exception as e:
        logger.error(f"Failed to update plan for {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save plan: {str(e)}")


@router.post(
    "/preview/{dataset_id}",
    response_model=TransformationPreview,
    summary="Preview transformation plan before/after samples without persisting",
)
async def preview_transformation_plan(dataset_id: str, req: PreviewRequest):
    dataset = dataset_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    try:
        source_version = req.source_version_id or version_service.get_active_version(dataset_id).version_id
        plan = TransformationPlan(
            plan_id="preview_plan",
            dataset_id=dataset_id,
            source_version_id=source_version,
            steps=req.steps,
            status=PlanStatus.PREVIEW_READY,
        )
        preview = plan_service.preview_plan(dataset_id, plan, preview_rows=req.preview_rows)
        return preview
    except Exception as e:
        logger.error(f"Failed to preview transformation plan for {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {str(e)}")


@router.post(
    "/dry-run/{dataset_id}",
    response_model=DryRunResult,
    summary="Validate entire plan and predict schema impact without applying",
)
async def dry_run_transformation_plan(dataset_id: str, req: DryRunRequest):
    dataset = dataset_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    try:
        source_version = req.source_version_id or version_service.get_active_version(dataset_id).version_id
        plan = TransformationPlan(
            plan_id="dry_run_plan",
            dataset_id=dataset_id,
            source_version_id=source_version,
            steps=req.steps,
            status=PlanStatus.VALIDATING,
        )
        result = plan_service.dry_run_plan(dataset_id, plan)
        return result
    except Exception as e:
        logger.error(f"Failed dry-run validation for {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Dry run failed: {str(e)}")


@router.post(
    "/apply/{dataset_id}",
    response_model=ApplyPlanResponse,
    summary="Atomically execute plan, persist new version, and compute quality delta",
)
async def apply_transformation_plan(dataset_id: str, req: ApplyPlanRequest):
    dataset = dataset_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    try:
        source_version = req.source_version_id or version_service.get_active_version(dataset_id).version_id

        if req.steps is not None:
            plan = TransformationPlan(
                plan_id=req.plan_id or f"plan_{dataset_id}",
                dataset_id=dataset_id,
                source_version_id=source_version,
                steps=req.steps,
                status=PlanStatus.APPROVED,
            )
        elif req.plan_id:
            loaded_plan = plan_service.get_plan(req.plan_id)
            if not loaded_plan:
                raise HTTPException(status_code=404, detail=f"Plan '{req.plan_id}' not found.")
            plan = loaded_plan
        else:
            plan = plan_service.get_or_create_plan_for_dataset(dataset_id, source_version_id=source_version)

        if not plan.steps:
            raise HTTPException(status_code=400, detail="Cannot apply an empty transformation plan.")

        new_version, comparison, audit = plan_service.apply_plan(
            dataset_id=dataset_id,
            plan=plan,
            label=req.version_label,
        )

        return ApplyPlanResponse(
            new_version=new_version,
            comparison=comparison,
            audit=audit,
        )
    except ValueError as ve:
        logger.warning(f"Plan validation failed for {dataset_id}: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to apply transformation plan for {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to apply plan: {str(e)}")
