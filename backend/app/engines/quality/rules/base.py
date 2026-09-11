"""
Base Quality Rule Interface
Every quality rule implements this abstract base class.
"""

from abc import ABC, abstractmethod
import hashlib
from typing import Any, List
import duckdb
from backend.app.engines.quality.models import Dimension, QualityIssue
from backend.app.schemas.profile import DatasetProfileResponse


class BaseQualityRule(ABC):
    """
    Abstract base class for all deterministic data quality rules.
    Rules must be stateless, side-effect free, and read-only.
    """

    rule_id: str
    name: str
    dimension: Dimension

    @abstractmethod
    def evaluate(
        self,
        conn: duckdb.DuckDBPyConnection,
        table_name: str,
        profile: DatasetProfileResponse,
    ) -> List[QualityIssue]:
        """
        Executes the quality rule against the DuckDB table and Phase 4 profile.
        Returns a list of QualityIssue models (empty list if no issues found).
        """
        pass

    def generate_issue_id(self, dataset_id: str, rule_id: str, col: str = "") -> str:
        """Generates a deterministic unique ID for an issue based on parameters."""
        raw = f"{dataset_id}:{rule_id}:{col}"
        digest = hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]
        return f"{rule_id.lower()}_{digest}"
