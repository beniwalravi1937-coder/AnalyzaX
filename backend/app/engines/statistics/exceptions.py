"""
AnalyzaX — Phase 10: Statistical Engine Domain Exceptions
Defines structured errors for statistical computations and input validations.
"""

from enum import Enum
from typing import Any, Dict, Optional


class StatisticsErrorCode(str, Enum):
    DATASET_NOT_FOUND = "DATASET_NOT_FOUND"
    DATASET_VERSION_NOT_FOUND = "DATASET_VERSION_NOT_FOUND"
    COLUMN_NOT_FOUND = "COLUMN_NOT_FOUND"
    INVALID_COLUMN_TYPE = "INVALID_COLUMN_TYPE"
    INVALID_ANALYSIS_TYPE = "INVALID_ANALYSIS_TYPE"
    INVALID_METHOD = "INVALID_METHOD"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    INVALID_ALPHA = "INVALID_ALPHA"
    INVALID_CONFIDENCE_LEVEL = "INVALID_CONFIDENCE_LEVEL"
    INVALID_ALTERNATIVE = "INVALID_ALTERNATIVE"
    INSUFFICIENT_SAMPLE_SIZE = "INSUFFICIENT_SAMPLE_SIZE"
    INSUFFICIENT_GROUPS = "INSUFFICIENT_GROUPS"
    EMPTY_GROUP = "EMPTY_GROUP"
    ZERO_VARIANCE = "ZERO_VARIANCE"
    MISSING_REQUIRED_INPUT = "MISSING_REQUIRED_INPUT"
    UNSUPPORTED_DATA_SHAPE = "UNSUPPORTED_DATA_SHAPE"
    ASSUMPTION_VIOLATION = "ASSUMPTION_VIOLATION"
    NUMERICAL_FAILURE = "NUMERICAL_FAILURE"
    STATISTICAL_ENGINE_FAILURE = "STATISTICAL_ENGINE_FAILURE"
    ANALYSIS_NOT_FOUND = "ANALYSIS_NOT_FOUND"
    ANALYSIS_CANCELLED = "ANALYSIS_CANCELLED"
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"


class StatisticsError(Exception):
    """Base exception for all statistical engine failures."""
    def __init__(self, message: str, code: str = StatisticsErrorCode.STATISTICAL_ENGINE_FAILURE.value, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class InsufficientSampleSizeError(StatisticsError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="INSUFFICIENT_SAMPLE_SIZE", details=details)


class ConstantVariableError(StatisticsError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="CONSTANT_VARIABLE_ERROR", details=details)


class ZeroVarianceError(StatisticsError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="ZERO_VARIANCE_ERROR", details=details)


class SingularMatrixError(StatisticsError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="SINGULAR_MATRIX_ERROR", details=details)


class InvalidMethodError(StatisticsError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="INVALID_STATISTICAL_METHOD", details=details)


class MissingColumnError(StatisticsError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="MISSING_COLUMN_ERROR", details=details)
