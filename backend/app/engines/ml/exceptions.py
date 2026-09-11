"""
AnalyzaX — Phase 11: Machine Learning Exception Hierarchy & Error Codes.
Provides structured, safe error reporting without leaking raw traces or internals.
"""

from enum import Enum
from typing import Any, Dict, Optional


class MLErrorCode(str, Enum):
    ML_DATASET_NOT_FOUND = "ML_DATASET_NOT_FOUND"
    ML_DATASET_VERSION_NOT_FOUND = "ML_DATASET_VERSION_NOT_FOUND"
    ML_INVALID_TARGET = "ML_INVALID_TARGET"
    ML_INVALID_FEATURES = "ML_INVALID_FEATURES"
    ML_UNSUPPORTED_TASK = "ML_UNSUPPORTED_TASK"
    ML_UNSUPPORTED_MODEL = "ML_UNSUPPORTED_MODEL"
    ML_INSUFFICIENT_DATA = "ML_INSUFFICIENT_DATA"
    ML_CLASS_IMBALANCE = "ML_CLASS_IMBALANCE"
    ML_SCHEMA_MISMATCH = "ML_SCHEMA_MISMATCH"
    ML_LEAKAGE_WARNING = "ML_LEAKAGE_WARNING"
    ML_PREPROCESSING_ERROR = "ML_PREPROCESSING_ERROR"
    ML_SPLIT_ERROR = "ML_SPLIT_ERROR"
    ML_TRAINING_ERROR = "ML_TRAINING_ERROR"
    ML_EVALUATION_ERROR = "ML_EVALUATION_ERROR"
    ML_ARTIFACT_ERROR = "ML_ARTIFACT_ERROR"
    ML_MODEL_NOT_FOUND = "ML_MODEL_NOT_FOUND"
    ML_INFERENCE_ERROR = "ML_INFERENCE_ERROR"
    ML_RESOURCE_LIMIT_EXCEEDED = "ML_RESOURCE_LIMIT_EXCEEDED"
    ML_TIMEOUT = "ML_TIMEOUT"
    ML_CANCELLED = "ML_CANCELLED"
    ML_SECURITY_VIOLATION = "ML_SECURITY_VIOLATION"


class MLException(Exception):
    """Base exception for all domain ML errors."""

    def __init__(
        self,
        message: str,
        error_code: MLErrorCode = MLErrorCode.ML_TRAINING_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
        }
