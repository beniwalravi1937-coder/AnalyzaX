"""
Transformation Registry
Central registry mapping TransformationType to concrete transformer instances.
"""

from typing import Dict, Type
from backend.app.engines.transformations.models import TransformationType
from backend.app.engines.transformations.transforms.base import BaseTransformer
from backend.app.engines.transformations.transforms.missing import (
    FillMissingTransformer,
    DropMissingTransformer,
)
from backend.app.engines.transformations.transforms.duplicates import DropDuplicatesTransformer
from backend.app.engines.transformations.transforms.text import (
    TrimWhitespaceTransformer,
    TextCaseTransformer,
    ReplaceTextTransformer,
)
from backend.app.engines.transformations.transforms.categories import NormalizeCategoriesTransformer
from backend.app.engines.transformations.transforms.types import CastTypeTransformer
from backend.app.engines.transformations.transforms.dates import (
    ParseDateTransformer,
    ExtractDatePartsTransformer,
)
from backend.app.engines.transformations.transforms.filters import FilterRowsTransformer
from backend.app.engines.transformations.transforms.columns import (
    DropColumnsTransformer,
    RenameColumnTransformer,
    ReorderColumnsTransformer,
)
from backend.app.engines.transformations.transforms.arithmetic import DerivedColumnTransformer
from backend.app.engines.transformations.transforms.encoding import (
    OneHotEncodeTransformer,
    LabelEncodeTransformer,
)
from backend.app.engines.transformations.transforms.scaling import (
    ScaleNumericTransformer,
    HandleOutliersTransformer,
)


class TransformationRegistry:
    """
    Registry for all registered transformers.
    """

    _REGISTRY: Dict[TransformationType, BaseTransformer] = {
        TransformationType.FILL_MISSING: FillMissingTransformer(),
        TransformationType.DROP_MISSING: DropMissingTransformer(),
        TransformationType.DROP_DUPLICATES: DropDuplicatesTransformer(),
        TransformationType.TRIM_WHITESPACE: TrimWhitespaceTransformer(),
        TransformationType.TEXT_CASE: TextCaseTransformer(),
        TransformationType.REPLACE_TEXT: ReplaceTextTransformer(),
        TransformationType.NORMALIZE_CATEGORIES: NormalizeCategoriesTransformer(),
        TransformationType.CAST_TYPE: CastTypeTransformer(),
        TransformationType.PARSE_DATE: ParseDateTransformer(),
        TransformationType.EXTRACT_DATE_PARTS: ExtractDatePartsTransformer(),
        TransformationType.FILTER_ROWS: FilterRowsTransformer(),
        TransformationType.DROP_COLUMNS: DropColumnsTransformer(),
        TransformationType.RENAME_COLUMN: RenameColumnTransformer(),
        TransformationType.REORDER_COLUMNS: ReorderColumnsTransformer(),
        TransformationType.DERIVED_COLUMN: DerivedColumnTransformer(),
        TransformationType.ONE_HOT_ENCODE: OneHotEncodeTransformer(),
        TransformationType.LABEL_ENCODE: LabelEncodeTransformer(),
        TransformationType.SCALE_NUMERIC: ScaleNumericTransformer(),
        TransformationType.HANDLE_OUTLIERS: HandleOutliersTransformer(),
    }

    @classmethod
    def get(cls, transformation_type: TransformationType) -> BaseTransformer:
        """Retrieves transformer instance for the given type, raising ValueError if unsupported."""
        if transformation_type not in cls._REGISTRY:
            raise ValueError(f"No transformer registered for type: {transformation_type}")
        return cls._REGISTRY[transformation_type]

    @classmethod
    def is_supported(cls, transformation_type: TransformationType) -> bool:
        """Checks if a transformation type is registered."""
        return transformation_type in cls._REGISTRY

    @classmethod
    def get_all_types(cls) -> list[TransformationType]:
        """Returns all registered transformation types."""
        return list(cls._REGISTRY.keys())
