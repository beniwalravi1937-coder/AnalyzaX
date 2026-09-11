"""
Transformation Engine
Orchestrates multi-step transformation pipelines, preview generation, and schema validation.
"""

import hashlib
import json
from typing import Any, Dict, List, Tuple
import polars as pl

from backend.app.engines.transformations.models import (
    TransformationPlan,
    TransformationStep,
    TransformationPreview,
    StepSummary,
    DryRunResult,
)
from backend.app.engines.transformations.registry import TransformationRegistry


class TransformationEngine:
    """
    Pure analytical transformation engine powered by Polars.
    Executes discrete operations sequentially with full impact tracking and immutability.
    """

    @classmethod
    def compute_schema_hash(cls, schema: Dict[str, Any]) -> str:
        """Computes deterministic SHA-256 hash of dataset column names and data types."""
        canonical_str = json.dumps(
            {k: str(v) for k, v in sorted(schema.items())},
            sort_keys=True
        )
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    @classmethod
    def compute_data_hash(cls, df: pl.DataFrame) -> str:
        """Computes SHA-256 digest of columnar data snapshot."""
        # Sample rows if very large, or hash schema + shape + column sums/null counts
        hasher = hashlib.sha256()
        hasher.update(str(df.shape).encode("utf-8"))
        for col in sorted(df.columns):
            hasher.update(col.encode("utf-8"))
            hasher.update(str(df[col].null_count()).encode("utf-8"))
            # Hash head and tail sample representation
            sample_bytes = str(df[col].head(50).to_list()).encode("utf-8")
            hasher.update(sample_bytes)
        return hasher.hexdigest()

    @classmethod
    def compute_pipeline_hash(cls, steps: List[TransformationStep]) -> str:
        """Computes SHA-256 hash of the transformation pipeline configuration."""
        canonical = [
            {
                "type": step.type.value,
                "parameters": step.parameters,
                "enabled": step.enabled,
            }
            for step in steps
        ]
        return hashlib.sha256(json.dumps(canonical, sort_keys=True).encode("utf-8")).hexdigest()

    @classmethod
    def validate_plan(
        cls,
        df: pl.DataFrame,
        plan: TransformationPlan,
    ) -> List[str]:
        """
        Validates the entire plan sequentially against evolving schema.
        Returns a list of validation errors (empty if completely valid).
        """
        errors: List[str] = []
        current_schema = dict(df.schema)

        for idx, step in enumerate(plan.steps):
            if not step.enabled:
                continue

            if not TransformationRegistry.is_supported(step.type):
                errors.append(f"Step {idx + 1} ({step.step_id}): Unsupported transformation type '{step.type}'")
                continue

            transformer = TransformationRegistry.get(step.type)
            step_errors = transformer.validate(current_schema, step.parameters)
            for err in step_errors:
                errors.append(f"Step {idx + 1} ({step.step_id} - {step.type.value}): {err}")

            # Simulate schema changes if step is valid so far
            if not step_errors:
                try:
                    # Run on small dummy head to track schema changes
                    sample = df.head(5)
                    transformed_sample, _ = transformer.apply(sample, step.parameters)
                    current_schema = dict(transformed_sample.schema)
                except Exception as e:
                    errors.append(f"Step {idx + 1} execution error during dry-run: {str(e)}")

        return errors

    @classmethod
    def execute_plan(
        cls,
        df: pl.DataFrame,
        plan: TransformationPlan,
    ) -> Tuple[pl.DataFrame, List[StepSummary]]:
        """
        Executes all enabled transformation steps against the DataFrame.
        Returns the transformed DataFrame and detailed step summaries.
        """
        current_df = df
        summaries: List[StepSummary] = []

        for step in plan.steps:
            if not step.enabled:
                continue

            transformer = TransformationRegistry.get(step.type)
            rows_before = len(current_df)
            cols_before = len(current_df.columns)

            transformed_df, metrics = transformer.apply(current_df, step.parameters)
            rows_after = len(transformed_df)
            cols_after = len(transformed_df.columns)

            rows_diff = rows_before - rows_after
            schema_change = None
            if cols_before != cols_after:
                schema_change = f"Columns: {cols_before} -> {cols_after}"

            summaries.append(
                StepSummary(
                    step_id=step.step_id,
                    type=step.type.value,
                    description=step.description,
                    rows_affected=rows_diff if rows_diff > 0 else metrics.get("modified_rows", metrics.get("values_clipped", 0)),
                    columns_affected=abs(cols_after - cols_before),
                    schema_change=schema_change,
                )
            )

            current_df = transformed_df

        return current_df, summaries

    @classmethod
    def preview_plan(
        cls,
        df: pl.DataFrame,
        plan: TransformationPlan,
        preview_rows: int = 10,
    ) -> TransformationPreview:
        """
        Generates before/after comparison samples without persisting changes.
        """
        validation_errors = cls.validate_plan(df, plan)

        columns_before = list(df.columns)
        rows_before = len(df)
        sample_before = df.head(preview_rows).to_dicts()

        if validation_errors:
            return TransformationPreview(
                plan_id=plan.plan_id,
                source_version_id=plan.source_version_id,
                sample_before=sample_before,
                sample_after=[],
                columns_before=columns_before,
                columns_after=columns_before,
                rows_before=rows_before,
                rows_after=rows_before,
                rows_affected=0,
                step_summaries=[],
                validation_errors=validation_errors,
            )

        transformed_df, summaries = cls.execute_plan(df, plan)
        rows_after = len(transformed_df)
        columns_after = list(transformed_df.columns)
        sample_after = transformed_df.head(preview_rows).to_dicts()

        return TransformationPreview(
            plan_id=plan.plan_id,
            source_version_id=plan.source_version_id,
            sample_before=sample_before,
            sample_after=sample_after,
            columns_before=columns_before,
            columns_after=columns_after,
            rows_before=rows_before,
            rows_after=rows_after,
            rows_affected=abs(rows_before - rows_after),
            step_summaries=summaries,
            validation_errors=[],
        )

    @classmethod
    def dry_run(
        cls,
        df: pl.DataFrame,
        plan: TransformationPlan,
    ) -> DryRunResult:
        """
        Performs full dry-run validation and schema diff prediction.
        """
        errors = cls.validate_plan(df, plan)
        if errors:
            return DryRunResult(
                valid=False,
                validation_errors=errors,
                source_version_id=plan.source_version_id,
                estimated_rows=len(df),
                estimated_columns=len(df.columns),
            )

        transformed_df, summaries = cls.execute_plan(df, plan)

        # Build schema diff
        orig_cols = set(df.columns)
        new_cols = set(transformed_df.columns)
        added_cols = list(new_cols - orig_cols)
        removed_cols = list(orig_cols - new_cols)

        return DryRunResult(
            valid=True,
            validation_errors=[],
            source_version_id=plan.source_version_id,
            estimated_rows=len(transformed_df),
            estimated_columns=len(transformed_df.columns),
            schema_diff={
                "added_columns": added_cols,
                "removed_columns": removed_cols,
                "total_steps": len(plan.steps),
            },
            quality_impact_prediction={
                "estimated_rows_modified": sum(s.rows_affected for s in summaries),
            },
        )
