"""
AI Analyst Engine — LLM Provider Abstraction (Phase 13)
Clean provider interface ensuring zero hard-coding of external gateways.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMCapabilities(BaseModel):
    supports_tool_calling: bool = True
    supports_structured_output: bool = True
    supports_streaming: bool = False
    max_context_tokens: int = 16000
    supports_json_mode: bool = True


class LLMProvider(ABC):
    """Abstract base class for all LLM providers in AnalyzaX."""

    def __init__(self, provider_id: str, model_id: str, capabilities: Optional[LLMCapabilities] = None):
        self.provider_id = provider_id
        self.model_id = model_id
        self.capabilities = capabilities or LLMCapabilities()

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        stop_sequences: Optional[List[str]] = None,
    ) -> str:
        """Generate text completion from LLM."""
        pass

    @abstractmethod
    async def structured_generate(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        """Generate a response strictly conforming to a Pydantic model schema."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider connectivity."""
        pass
