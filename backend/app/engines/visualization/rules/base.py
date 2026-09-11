"""
Base interfaces and context for visualization recommendation rules.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from backend.app.engines.visualization.models import (
    ChartType,
    VisualizationIntent,
    VisualizationRecommendation,
)


class ColumnContext(BaseModel):
    name: str
    physical_type: str
    semantic_type: str = "unknown"
    cardinality: int = 0
    unique_percentage: float = 0.0
    null_count: int = 0
    null_percentage: float = 0.0
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    is_constant: bool = False
    is_identifier: bool = False


class EvaluationContext(BaseModel):
    columns: Dict[str, ColumnContext]
    row_count: int
    selected_fields: Optional[List[str]] = None
    intent: Optional[VisualizationIntent] = None
    quality_issues: List[Dict[str, Any]] = []

    def get_numeric_columns(self) -> List[str]:
        return [
            name for name, col in self.columns.items()
            if col.semantic_type == "numeric" or col.physical_type in ("int64", "int32", "float64", "float32", "double", "integer", "numeric", "decimal")
            and not col.is_identifier and not col.is_constant
        ]

    def get_categorical_columns(self) -> List[str]:
        return [
            name for name, col in self.columns.items()
            if col.semantic_type in ("categorical", "category", "text", "string") or col.physical_type in ("string", "object", "varchar", "bool", "boolean")
            and not col.is_identifier and not col.is_constant
        ]

    def get_temporal_columns(self) -> List[str]:
        return [
            name for name, col in self.columns.items()
            if col.semantic_type in ("datetime", "date", "temporal", "timestamp") or "date" in col.physical_type.lower() or "time" in col.physical_type.lower()
        ]


class BaseRecommendationRule(ABC):
    """
    Deterministic rule interface.
    Evaluates dataset context and emits typed recommendations with transparent reasons.
    """

    @abstractmethod
    def evaluate(self, ctx: EvaluationContext) -> List[VisualizationRecommendation]:
        pass
