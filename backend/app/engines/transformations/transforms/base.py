"""
Base Transformer Interface
Abstract base class defining the contract for all modular transformation operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple
import polars as pl
from backend.app.engines.transformations.models import TransformationType


class BaseTransformer(ABC):
    """
    Abstract base transformer.
    Every transformer must implement schema validation and Polars dataframe mutation.
    """

    transformation_type: TransformationType

    @abstractmethod
    def validate(self, schema: Dict[str, pl.DataType], parameters: Dict[str, Any]) -> List[str]:
        """
        Validates whether parameters are legal for the given dataset schema.
        Returns a list of validation error messages (empty if valid).
        """
        pass

    @abstractmethod
    def apply(
        self,
        df: pl.DataFrame,
        parameters: Dict[str, Any],
    ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        """
        Executes the transformation against a Polars DataFrame.
        Returns the transformed DataFrame and impact metrics dictionary.
        """
        pass
