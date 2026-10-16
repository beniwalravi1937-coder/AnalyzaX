"""
AI Analyst Engine — Provider Factory (Phase 13)
Factory function returning the configured LLMProvider based on settings.
"""

from backend.app.core.config import settings
from backend.app.engines.ai_analyst.providers.base import LLMProvider
from backend.app.engines.ai_analyst.providers.gemini import GeminiProvider
from backend.app.engines.ai_analyst.providers.mock_provider import MockLLMProvider
from backend.app.engines.ai_analyst.providers.openrouter import OpenRouterProvider


def get_llm_provider() -> LLMProvider:
    """Returns provider instance based on application configuration."""
    provider_name = (settings.AI_PROVIDER or "mock").lower()

    if (provider_name == "gemini" or not provider_name or provider_name == "default") and (settings.GEMINI_API_KEY or settings.AI_API_KEY):
        return GeminiProvider(
            api_key=settings.GEMINI_API_KEY or settings.AI_API_KEY,
            model_id=settings.GEMINI_MODEL or "gemini-2.5-flash",
            timeout_seconds=settings.AI_TIMEOUT_SECONDS,
            max_retries=settings.AI_MAX_RETRIES,
        )

    if provider_name == "openrouter" and settings.AI_API_KEY:
        return OpenRouterProvider(
            api_key=settings.AI_API_KEY,
            model_id=settings.AI_MODEL,
            base_url=settings.AI_BASE_URL,
            timeout_seconds=settings.AI_TIMEOUT_SECONDS,
            max_retries=settings.AI_MAX_RETRIES,
        )
    return MockLLMProvider()

