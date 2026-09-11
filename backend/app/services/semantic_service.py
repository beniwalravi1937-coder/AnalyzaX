"""
AnalyzaX — Phase 25: Governed Semantic & Metric Application Service.
Provides enterprise metric management, AST formula validation, safe preview calculations,
and metric versioning.
"""

import hashlib
from typing import Any, Dict, List, Optional
from backend.app.core.logging import logger
from backend.app.engines.semantic.engine import SemanticEngine
from backend.app.engines.semantic.expression import MetricExpressionParser
from backend.app.engines.semantic.models import (
    AggregationType,
    MetricCalculationResult,
    MetricDefinition,
    MetricStatus,
    MetricVersionRecord,
)
from backend.app.engines.semantic.repository import semantic_repo


class SemanticService:
    """Application Service for Metric Governance and Semantic Intelligence."""

    def create_metric(
        self,
        workspace_id: str,
        name: str,
        expression: str,
        owner_id: str,
        project_id: Optional[str] = None,
        description: str = "",
        aggregation: AggregationType = AggregationType.SUM,
        unit: Optional[str] = None,
        dimensions: Optional[List[str]] = None,
        synonyms: Optional[List[str]] = None,
    ) -> MetricDefinition:
        """Validates and persists a new governed metric definition."""
        # AST validate expression
        validation = MetricExpressionParser.validate_expression(expression)
        if not validation.is_valid:
            raise ValueError(f"Invalid metric expression: {validation.error_message}")

        metric_id = f"metric_{hashlib.sha256(name.lower().strip().encode()).hexdigest()[:8]}"
        metric = MetricDefinition(
            metric_id=metric_id,
            workspace_id=workspace_id,
            project_id=project_id,
            name=name,

            description=description,
            expression=expression,
            aggregation=aggregation,
            unit=unit,
            dimensions=dimensions or [],
            synonyms=synonyms or [],
            owner_id=owner_id,
            status=MetricStatus.ACTIVE,
        )
        return semantic_repo.save_metric(metric, changed_by=owner_id, change_summary="Initial metric creation")

    def get_metric(self, metric_id: str) -> Optional[MetricDefinition]:
        return semantic_repo.get_metric(metric_id)

    def list_metrics(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
        status: Optional[MetricStatus] = None,
    ) -> List[MetricDefinition]:
        return semantic_repo.list_metrics(workspace_id=workspace_id, project_id=project_id, status=status)

    def update_metric(
        self,
        metric_id: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        expression: Optional[str] = None,
        status: Optional[MetricStatus] = None,
        unit: Optional[str] = None,
        synonyms: Optional[List[str]] = None,
        change_summary: str = "Updated metric definition",
    ) -> MetricDefinition:
        """Updates metric attributes, validating expressions if changed, and creating version audit."""
        metric = semantic_repo.get_metric(metric_id)
        if not metric:
            raise ValueError(f"Metric '{metric_id}' not found.")

        if expression and expression != metric.expression:
            validation = MetricExpressionParser.validate_expression(expression)
            if not validation.is_valid:
                raise ValueError(f"Invalid metric expression: {validation.error_message}")
            metric.expression = expression

        if name:
            metric.name = name
        if description is not None:
            metric.description = description
        if status:
            metric.status = status
        if unit is not None:
            metric.unit = unit
        if synonyms is not None:
            metric.synonyms = synonyms

        return semantic_repo.save_metric(metric, changed_by=user_id, change_summary=change_summary)

    def delete_metric(self, metric_id: str) -> bool:
        return semantic_repo.delete_metric(metric_id)

    def get_version_history(self, metric_id: str) -> List[MetricVersionRecord]:
        return semantic_repo.get_version_history(metric_id)

    def validate_formula(self, expression: str, available_columns: Optional[List[str]] = None) -> Dict[str, Any]:
        result = MetricExpressionParser.validate_expression(expression, available_columns=available_columns)
        return result.model_dump()

    def preview_metric(
        self,
        metric_id: str,
        dataset_path: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> MetricCalculationResult:
        """Computes deterministic metric preview using DuckDB."""
        metric = semantic_repo.get_metric(metric_id)
        if not metric:
            raise ValueError(f"Metric '{metric_id}' not found.")
        return SemanticEngine.calculate_metric(metric=metric, dataset_path=dataset_path, filters=filters)


semantic_service = SemanticService()
