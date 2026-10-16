"""
AnalyzaX — Phase 25 Test Suite: Google Gemini Provider.
Validates GeminiProvider initialization, completions, structured output generation,
error recovery, timeout handling, and security redaction of secrets.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import BaseModel

from backend.app.engines.ai_analyst.exceptions import AIAnalystException
from backend.app.engines.ai_analyst.providers.factory import get_llm_provider
from backend.app.engines.ai_analyst.providers.gemini import GeminiProvider


class DummyStructuredModel(BaseModel):
    summary: str
    confidence: float


class TestGeminiProvider:
    def test_provider_initialization(self):
        provider = GeminiProvider(api_key="test_key_abc", model_id="gemini-2.5-flash")
        assert provider.provider_id == "gemini"
        assert provider.model_id == "gemini-2.5-flash"
        assert provider.capabilities.supports_structured_output is True
        assert provider.capabilities.max_context_tokens >= 1_000_000

    @pytest.mark.asyncio
    async def test_generate_success(self):
        provider = GeminiProvider(api_key="test_key_123")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "Gemini analytical insight on dataset distributions."}]
                    }
                }
            ]
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            result = await provider.generate(prompt="Analyze correlation between math and reading.")
            assert "Gemini analytical insight" in result

    @pytest.mark.asyncio
    async def test_structured_generate_success(self):
        provider = GeminiProvider(api_key="test_key_123")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": '{"summary": "Strong positive correlation detected", "confidence": 0.95}'}]
                    }
                }
            ]
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            model = await provider.structured_generate(
                prompt="Summarize findings",
                response_model=DummyStructuredModel,
            )
            assert model.summary == "Strong positive correlation detected"
            assert model.confidence == 0.95

    @pytest.mark.asyncio
    async def test_generate_redacts_api_key_on_error(self):
        secret_key = "secret_key_to_redact_xyz"
        provider = GeminiProvider(api_key=secret_key)
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = f"API error for key {secret_key}: Permission denied."

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(AIAnalystException) as exc_info:
                await provider.generate(prompt="Hello")
            assert secret_key not in str(exc_info.value)
            assert "[REDACTED]" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_health_check(self):
        provider = GeminiProvider(api_key="test_key_123")
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            healthy = await provider.health_check()
            assert healthy is True

    def test_factory_returns_gemini_provider(self, monkeypatch):
        monkeypatch.setattr("backend.app.core.config.settings.AI_PROVIDER", "gemini")
        monkeypatch.setattr("backend.app.core.config.settings.GEMINI_API_KEY", "dummy_gemini_key")
        provider = get_llm_provider()
        assert isinstance(provider, GeminiProvider)
