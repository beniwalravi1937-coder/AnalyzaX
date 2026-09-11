"""
AI Analyst Engine — Exceptions and Error Codes (Phase 13)
Conforms to AGENTS.md error envelope and project standard error codes.
"""

from enum import Enum
from typing import Any, Dict, Optional


class AIErrorCode(str, Enum):
    AI_PROVIDER_UNAVAILABLE = "AI_PROVIDER_UNAVAILABLE"
    AI_PROVIDER_TIMEOUT = "AI_PROVIDER_TIMEOUT"
    AI_MODEL_UNAVAILABLE = "AI_MODEL_UNAVAILABLE"
    AI_INVALID_RESPONSE = "AI_INVALID_RESPONSE"
    AI_TOOL_CALL_INVALID = "AI_TOOL_CALL_INVALID"
    AI_TOOL_NOT_FOUND = "AI_TOOL_NOT_FOUND"
    AI_TOOL_PERMISSION_DENIED = "AI_TOOL_PERMISSION_DENIED"
    AI_TOOL_LIMIT_EXCEEDED = "AI_TOOL_LIMIT_EXCEEDED"
    AI_CONTEXT_LIMIT_EXCEEDED = "AI_CONTEXT_LIMIT_EXCEEDED"
    AI_ANALYSIS_TIMEOUT = "AI_ANALYSIS_TIMEOUT"
    AI_MAX_TOOL_CALLS_EXCEEDED = "AI_MAX_TOOL_CALLS_EXCEEDED"
    AI_SQL_GENERATION_FAILED = "AI_SQL_GENERATION_FAILED"
    AI_SQL_VALIDATION_FAILED = "AI_SQL_VALIDATION_FAILED"
    AI_ANALYSIS_FAILED = "AI_ANALYSIS_FAILED"
    AI_RESPONSE_VALIDATION_FAILED = "AI_RESPONSE_VALIDATION_FAILED"
    AI_SESSION_NOT_FOUND = "AI_SESSION_NOT_FOUND"
    AI_DATASET_CONTEXT_INVALID = "AI_DATASET_CONTEXT_INVALID"
    AI_VERSION_CONTEXT_INVALID = "AI_VERSION_CONTEXT_INVALID"
    AI_CLEANING_CONFIRMATION_REQUIRED = "AI_CLEANING_CONFIRMATION_REQUIRED"
    AI_PROMPT_INJECTION_DETECTED = "AI_PROMPT_INJECTION_DETECTED"
    AI_SECRET_ACCESS_DENIED = "AI_SECRET_ACCESS_DENIED"


class AIAnalystException(Exception):
    """Base exception for all AI Analyst errors."""

    def __init__(
        self,
        error_code: AIErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
        }
