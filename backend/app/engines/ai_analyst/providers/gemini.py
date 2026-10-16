"""
AnalyzaX — Phase 25: Google Gemini LLM Provider.
Server-side integration with Google Gemini Generative Language API.
Complies with AGENTS.md Constitution: zero secret leaks, data privacy, and deterministic reliability.
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


class GeminiProvider(LLMProvider):
    """Google Gemini client implementing the LLMProvider abstraction."""

    def __init__(
        self,
        api_key: str,
        model_id: str = "gemini-2.5-flash",
        timeout_seconds: int = 60,
        max_retries: int = 2,
    ):
        super().__init__(
            provider_id="gemini",
            model_id=model_id,
            capabilities=LLMCapabilities(
                supports_tool_calling=True,
                supports_structured_output=True,
                supports_streaming=True,
                max_context_tokens=1_000_000,
                supports_json_mode=True,
            ),
        )
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.endpoint_base = "https://generativelanguage.googleapis.com/v1beta/models"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        stop_sequences: Optional[List[str]] = None,
    ) -> str:
        """Generates conversational text completion from Gemini."""
        if not self.api_key:
            raise AIAnalystException(
                AIErrorCode.AI_PROVIDER_UNAVAILABLE,
                "Gemini API key is not configured. Set GEMINI_API_KEY in environment.",
            )

        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        gen_config: Dict[str, Any] = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
        if stop_sequences:
            gen_config["stopSequences"] = stop_sequences

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": gen_config,
        }

        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        url = f"{self.endpoint_base}/{self.model_id}:generateContent?key={self.api_key}"

        attempts = 0
        last_error = None
        while attempts <= self.max_retries:
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(url, json=payload)

                    if response.status_code >= 500:
                        last_error = f"Gemini server error HTTP {response.status_code}"
                        attempts += 1
                        continue

                    if response.status_code != 200:
                        err_text = response.text[:300]
                        # Redact key if present in error message
                        if self.api_key in err_text:
                            err_text = err_text.replace(self.api_key, "[REDACTED]")
                        raise AIAnalystException(
                            AIErrorCode.AI_PROVIDER_UNAVAILABLE,
                            f"Gemini returned status {response.status_code}: {err_text}",
                        )

                    data = response.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise AIAnalystException(
                            AIErrorCode.AI_INVALID_RESPONSE,
                            "Gemini returned empty candidates array.",
                        )

                    parts = candidates[0].get("content", {}).get("parts", [])
                    if not parts:
                        return ""
                    return parts[0].get("text", "")

            except httpx.TimeoutException:
                attempts += 1
                last_error = "Gemini request timed out."
            except httpx.RequestError as exc:
                attempts += 1
                last_error = f"Gemini connection error: {str(exc)}"

        raise AIAnalystException(
            AIErrorCode.AI_PROVIDER_TIMEOUT if "timed out" in str(last_error) else AIErrorCode.AI_PROVIDER_UNAVAILABLE,
            f"Gemini failed after {self.max_retries + 1} attempts: {last_error}",
        )

    async def structured_generate(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        """Generates structured response strictly adhering to a Pydantic schema."""
        if not self.api_key:
            raise AIAnalystException(
                AIErrorCode.AI_PROVIDER_UNAVAILABLE,
                "Gemini API key is not configured. Set GEMINI_API_KEY in environment.",
            )

        schema = response_model.model_json_schema()
        schema_instruction = (
            f"\nYou must output strictly valid JSON conforming to this schema:\n"
            f"{json.dumps(schema, indent=2)}\n"
            f"Do not include markdown fences or explanation outside the JSON."
        )

        full_prompt = f"{prompt}\n{schema_instruction}"
        contents = [{"role": "user", "parts": [{"text": full_prompt}]}]
        gen_config = {
            "temperature": temperature,
            "responseMimeType": "application/json",
        }

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": gen_config,
        }

        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        url = f"{self.endpoint_base}/{self.model_id}:generateContent?key={self.api_key}"

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                raw_err = response.text[:200]
                if self.api_key in raw_err:
                    raw_err = raw_err.replace(self.api_key, "[REDACTED]")
                raise AIAnalystException(
                    AIErrorCode.AI_PROVIDER_UNAVAILABLE,
                    f"Gemini structured generate failed ({response.status_code}): {raw_err}",
                )

            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise AIAnalystException(
                    AIErrorCode.AI_INVALID_RESPONSE,
                    "Gemini returned empty candidates.",
                )

            raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            cleaned = raw_text.strip()
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
                logger.warning("Failed to validate structured Gemini response: %s", exc)
                raise AIAnalystException(
                    AIErrorCode.AI_INVALID_RESPONSE,
                    f"Gemini response failed schema validation: {str(exc)}",
                    details={"raw_output": raw_text[:500]},
                )

    async def health_check(self) -> bool:
        """Verifies Gemini API connectivity."""
        if not self.api_key:
            return False
        try:
            url = f"{self.endpoint_base}/{self.model_id}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": "ping"}]}],
                "generationConfig": {"maxOutputTokens": 2},
            }
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json=payload)
                return resp.status_code == 200
        except Exception:
            return False
