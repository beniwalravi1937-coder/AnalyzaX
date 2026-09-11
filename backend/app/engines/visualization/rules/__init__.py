"""
Visualization recommendation rules module.
"""

from backend.app.engines.visualization.rules.base import (
    BaseRecommendationRule,
    ColumnContext,
    EvaluationContext,
)
from backend.app.engines.visualization.rules.categorical import (
    CategoricalComparisonRule,
    CategoricalBivariateRule,
)
from backend.app.engines.visualization.rules.composition import CompositionRule
from backend.app.engines.visualization.rules.numerical import (
    NumericDistributionRule,
    NumericRelationshipRule,
)
from backend.app.engines.visualization.rules.quality import QualityGuardrailFilter
from backend.app.engines.visualization.rules.temporal import TemporalTrendRule

__all__ = [
    "BaseRecommendationRule",
    "CategoricalBivariateRule",
    "CategoricalComparisonRule",
    "ColumnContext",
    "CompositionRule",
    "EvaluationContext",
    "NumericDistributionRule",
    "NumericRelationshipRule",
    "QualityGuardrailFilter",
    "TemporalTrendRule",
]
