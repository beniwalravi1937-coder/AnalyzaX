"""
AnalyzaX — Phase 12: Forecasting Error Codes and Exceptions.
Standardized error codes preventing internal stack trace leaks to clients.
"""

from enum import Enum
from typing import Any, Dict, Optional


class ForecastErrorCode(str, Enum):
    # Dataset and input errors
    FORECAST_DATASET_NOT_FOUND = "FORECAST_DATASET_NOT_FOUND"
    FORECAST_VERSION_NOT_FOUND = "FORECAST_VERSION_NOT_FOUND"
    FORECAST_INVALID_TIME_COLUMN = "FORECAST_INVALID_TIME_COLUMN"
    FORECAST_INVALID_TARGET = "FORECAST_INVALID_TARGET"
    FORECAST_INVALID_FREQUENCY = "FORECAST_INVALID_FREQUENCY"
    FORECAST_DUPLICATE_TIMESTAMPS = "FORECAST_DUPLICATE_TIMESTAMPS"
    FORECAST_MISSING_TIMESTAMPS = "FORECAST_MISSING_TIMESTAMPS"
    FORECAST_IRREGULAR_SERIES = "FORECAST_IRREGULAR_SERIES"
    FORECAST_INSUFFICIENT_HISTORY = "FORECAST_INSUFFICIENT_HISTORY"
    FORECAST_INSUFFICIENT_SEASONAL_HISTORY = "FORECAST_INSUFFICIENT_SEASONAL_HISTORY"
    FORECAST_INVALID_HORIZON = "FORECAST_INVALID_HORIZON"
    FORECAST_INVALID_MODEL = "FORECAST_INVALID_MODEL"
    FORECAST_INVALID_PARAMETERS = "FORECAST_INVALID_PARAMETERS"

    # Execution errors
    FORECAST_SPLIT_ERROR = "FORECAST_SPLIT_ERROR"
    FORECAST_BACKTEST_ERROR = "FORECAST_BACKTEST_ERROR"
    FORECAST_TRAINING_ERROR = "FORECAST_TRAINING_ERROR"
    FORECAST_EVALUATION_ERROR = "FORECAST_EVALUATION_ERROR"
    FORECAST_ARTIFACT_ERROR = "FORECAST_ARTIFACT_ERROR"
    FORECAST_INFERENCE_ERROR = "FORECAST_INFERENCE_ERROR"
    FORECAST_SCHEMA_MISMATCH = "FORECAST_SCHEMA_MISMATCH"

    # Governance and lifecycle errors
    FORECAST_RESOURCE_LIMIT_EXCEEDED = "FORECAST_RESOURCE_LIMIT_EXCEEDED"
    FORECAST_TIMEOUT = "FORECAST_TIMEOUT"
    FORECAST_CANCELLED = "FORECAST_CANCELLED"
    FORECAST_INTERNAL_ERROR = "FORECAST_INTERNAL_ERROR"


class ForecastException(Exception):
    """Normalized domain exception for time-series forecasting."""

    def __init__(
        self,
        code: ForecastErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.code.value,
            "message": self.message,
            "details": self.details,
        }
