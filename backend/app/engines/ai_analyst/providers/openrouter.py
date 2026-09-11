"""
AI Analyst Engine — OpenRouter Provider Implementation (Phase 13)
Server-side integration with OpenRouter OpenAI-compatible API.
API keys are never logged or returned to clients.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel, ValidationError

from backend.app.engines.ai_analyst.exceptions import AIAnalystException, AIErrorCode
from backend.app.engines.ai_analyst.providers.base import LLMCapabilities, LLMProvider

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class OpenRouterProvider(LLMProvider):
    """OpenRouter gateway client implementing LLMProvider."""

    def __init__(
        self,
        api_key: str,
        model_id: str = "meta-llama/llama-3.3-70b-instruct:free",
        base_url: str = "https://openrouter.ai/api/v1",
        timeout_seconds: int = 60,
        max_retries: int = 2,
    ):
        super().__init__(
            provider_id="openrouter",
            model_id=model_id,
            capabilities=LLMCapabilities(
                supports_tool_calling=True,
                supports_structured_output=True,
                supports_streaming=True,
                max_context_tokens=16000,
                supports_json_mode=True,
            ),
        )
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://analyzax.ai",
            "X-Title": "AnalyzaX AI Analyst",
            "Content-Type": "application/json",
        }

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        stop_sequences: Optional[List[str]] = None,
    ) -> str:
        if not self.api_key:
            raise AIAnalystException(
                AIErrorCode.AI_PROVIDER_UNAVAILABLE,
                "OpenRouter API key is not configured. Set AI_API_KEY in environment.",
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stop_sequences:
            payload["stop"] = stop_sequences

        attempts = 0
        last_error = None
        while attempts <= self.max_retries:
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self._get_headers(),
                        json=payload,
                    )
                    if response.status_code >= 500:
                        last_error = f"OpenRouter HTTP {response.status_code}: {response.text[:200]}"
                        attempts += 1
                        continue
                    if response.status_code != 200:
                        raise AIAnalystException(
                            AIErrorCode.AI_PROVIDER_UNAVAILABLE,
                            f"OpenRouter returned status {response.status_code}: {response.text[:200]}",
                        )

                    data = response.json()
                    choices = data.get("choices", [])
                    if not choices:
                        raise AIAnalystException(
                            AIErrorCode.AI_INVALID_RESPONSE,
                            "OpenRouter returned empty choices array.",
                        )
                    return choices[0].get("message", {}).get("content", "")
            except httpx.TimeoutException:
                attempts += 1
                last_error = "OpenRouter request timed out."
            except httpx.RequestError as exc:
                attempts += 1
                last_error = f"OpenRouter connection error: {str(exc)}"

        raise AIAnalystException(
            AIErrorCode.AI_PROVIDER_TIMEOUT if "timed out" in str(last_error) else AIErrorCode.AI_PROVIDER_UNAVAILABLE,
            f"OpenRouter failed after {self.max_retries + 1} attempts: {last_error}",
        )

    async def structured_generate(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        schema = response_model.model_json_schema()
        schema_instruction = (
            f"\nYou must output strictly valid JSON matching this schema:\n"
            f"{json.dumps(schema, indent=2)}\n"
            f"Do not include any commentary or code fences outside the JSON string."
        )

        full_prompt = f"{prompt}\n{schema_instruction}"
        raw_output = await self.generate(
            prompt=full_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
        )

        # Parse JSON from raw output
        cleaned = raw_output.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            parsed_json = json.loads(cleaned)
            return response_model.model_validate(parsed_json)
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.warning("Failed to parse structured LLM response: %s. Raw: %s", exc, raw_output[:300])
            raise AIAnalystException(
                AIErrorCode.AI_INVALID_RESPONSE,
                f"LLM response failed schema validation: {str(exc)}",
                details={"raw_output": raw_output[:500]},
            )

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.base_url}/models",
                    headers=self._get_headers(),
                )
                return resp.status_code == 200
        except Exception:
            return False
