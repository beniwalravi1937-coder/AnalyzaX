"""
Transformation Plan Application Service
Coordinates creation, persistence, previewing, dry-running, and atomic application
of data transformation pipelines.
"""

import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.transformations.engine import TransformationEngine
from backend.app.engines.transformations.models import (
    DatasetVersion,
    DryRunResult,
    PlanStatus,
    QualityComparison,
    TransformationAudit,
    TransformationPlan,
    TransformationPreview,
)
from backend.app.services.cleaning.comparison_service import ComparisonService
from backend.app.services.cleaning.version_service import VersionService
from backend.app.services.profiling_service import profiling_service
from backend.app.services.quality_service import quality_service


class PlanService:
    """
    Manages the lifecycle of Transformation Plans:
    persistence, preview execution, dry runs, and atomic application to create new versions.
    """

    def __init__(self) -> None:
        self._plans_dir = os.path.abspath(settings.DATA_PLANS_DIR)
        self._version_service = VersionService()
        self._comparison_service = ComparisonService()
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        os.makedirs(self._plans_dir, exist_ok=True)

    def _get_plan_path(self, plan_id: str) -> str:
        return os.path.join(self._plans_dir, f"{plan_id}.json")

    def save_plan(self, plan: TransformationPlan) -> TransformationPlan:
        """Persists plan to disk."""
        plan.updated_at = datetime.now(timezone.utc).isoformat()
        path = self._get_plan_path(plan.plan_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(plan.model_dump(), f, indent=2, default=str)
        return plan

    def get_plan(self, plan_id: str) -> Optional[TransformationPlan]:
        """Loads plan by ID."""
        path = self._get_plan_path(plan_id)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return TransformationPlan(**json.load(f))
            except Exception as e:
                logger.warning(f"Failed to read plan {plan_id}: {e}")
        return None

    def get_or_create_plan_for_dataset(self, dataset_id: str, source_version_id: Optional[str] = None) -> TransformationPlan:
        """
        Retrieves existing draft plan or creates an empty new one.
        """
        if not source_version_id:
            active_version = self._version_service.get_active_version(dataset_id)
            source_version_id = active_version.version_id

        # Scan for existing draft for this dataset
        for filename in os.listdir(self._plans_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self._plans_dir, filename), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data.get("dataset_id") == dataset_id and data.get("status") == PlanStatus.DRAFT.value:
                            return TransformationPlan(**data)
                except Exception:
                    pass

        # Create new
        new_plan = TransformationPlan(
            plan_id=f"plan_{uuid.uuid4().hex[:10]}",
            dataset_id=dataset_id,
            source_version_id=source_version_id,
            steps=[],
            status=PlanStatus.DRAFT,
        )
        return self.save_plan(new_plan)

    def preview_plan(
        self,
        dataset_id: str,
        plan: TransformationPlan,
        preview_rows: int = 10,
    ) -> TransformationPreview:
        """
        Generates before/after preview sample for a transformation plan.
        """
        df = self._version_service.get_version_dataframe(dataset_id, plan.source_version_id)
        return TransformationEngine.preview_plan(df, plan, preview_rows=preview_rows)

    def dry_run_plan(
        self,
        dataset_id: str,
        plan: TransformationPlan,
    ) -> DryRunResult:
        """
        Performs non-destructive dry-run validation.
        """
        df = self._version_service.get_version_dataframe(dataset_id, plan.source_version_id)
        return TransformationEngine.dry_run(df, plan)

    def apply_plan(
        self,
        dataset_id: str,
        plan: TransformationPlan,
        label: Optional[str] = None,
    ) -> Tuple[DatasetVersion, QualityComparison, TransformationAudit]:
        """
        Atomically executes the transformation plan, persists a new version v{N},
        re-evaluates quality, and returns the quality comparison.
        """
        start_time = time.perf_counter()

        df = self._version_service.get_version_dataframe(dataset_id, plan.source_version_id)
        rows_before = len(df)

        # Validate
        errors = TransformationEngine.validate_plan(df, plan)
        if errors:
            raise ValueError(f"Transformation plan validation failed: {'; '.join(errors)}")

        # Execute
        transformed_df, step_summaries = TransformationEngine.execute_plan(df, plan)
        rows_after = len(transformed_df)
        rows_affected = sum(s.rows_affected for s in step_summaries)

        # Pipeline hash
        pipeline_hash = TransformationEngine.compute_pipeline_hash(plan.steps)

        # Determine label
        version_label = label or f"Cleaned ({len(plan.steps)} steps applied)"

        # Create new version
        new_version = self._version_service.create_version(
            dataset_id=dataset_id,
            df=transformed_df,
            parent_version_id=plan.source_version_id,
            label=version_label,
            pipeline_hash=pipeline_hash,
            operation_count=len(plan.steps),
        )

        # Auto re-profile and quality evaluation for the new version
        comparison = self._comparison_service.compare_versions(
            dataset_id=dataset_id,
            before_version_id=plan.source_version_id,
            after_version_id=new_version.version_id,
        )

        # Refresh dataset-level cached profile and quality report to reflect the new active version
        try:
            profiling_service.profile_dataset(dataset_id, force_refresh=True)
            quality_service.assess_dataset_quality(dataset_id, force_refresh=True)
        except Exception as e:
            logger.warning(f"Background refresh of profile/quality for dataset {dataset_id} completed with warning: {e}")

        # Mark plan completed
        plan.status = PlanStatus.COMPLETED
        self.save_plan(plan)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        audit = TransformationAudit(
            audit_id=f"audit_{uuid.uuid4().hex[:10]}",
            dataset_id=dataset_id,
            source_version_id=plan.source_version_id,
            new_version_id=new_version.version_id,
            plan_id=plan.plan_id,
            steps_applied=len(plan.steps),
            rows_before=rows_before,
            rows_after=rows_after,
            rows_affected=rows_affected,
            execution_time_ms=elapsed_ms,
        )

        logger.info(
            f"Successfully applied plan {plan.plan_id} on dataset {dataset_id}: "
            f"{new_version.version_id} created in {elapsed_ms}ms"
        )

        return new_version, comparison, audit
