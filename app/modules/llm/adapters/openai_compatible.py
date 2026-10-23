"""Adaptador HTTP para APIs que implementan el contrato Chat Completions compatible.

No depende de un SDK comercial. La URL, el modelo y la API key se suministran
mediante Settings, y el cliente HTTP se inyecta para reutilizar conexiones y
facilitar pruebas sin red.
"""

import logging
from typing import Any

import httpx

from app.core.config import Settings
from app.modules.llm.ports import (
    LLMGenerationResult,
    LLMNotConfiguredError,
    LLMProviderRateLimitError,
    LLMProviderResponseError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
)

logger = logging.getLogger(__name__)


class OpenAICompatibleChatProvider:
    """Cliente de Chat Completions para proveedores compatibles con OpenAI."""

    provider_name = "openai_compatible"

    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._client = client

    async def generate(
        self,
        *,
        prompt: str,
        system_prompt: str | None = None,
    ) -> LLMGenerationResult:
        api_key = (
            self._settings.llm_api_key.get_secret_value().strip()
            if self._settings.llm_api_key
            else ""
        )
        base_url = (
            str(self._settings.llm_base_url).rstrip("/")
            if self._settings.llm_base_url
            else ""
        )
        model = (self._settings.llm_model or "").strip()

        if not api_key or not base_url or not model:
            raise LLMNotConfiguredError(
                "Configure LLM_API_KEY, LLM_BASE_URL and LLM_MODEL on the server."
            )

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": self._settings.llm_temperature,
            "max_tokens": self._settings.llm_max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            response = await self._client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
        except httpx.TimeoutException as exc:
            # No se reintenta automáticamente: un timeout puede ocurrir después
            # de que el proveedor haya aceptado la solicitud y generar coste doble.
            raise LLMProviderTimeoutError from exc
        except httpx.RequestError as exc:
            logger.warning("LLM upstream transport error: %s", type(exc).__name__)
            raise LLMProviderUnavailableError from exc

        if response.status_code == 429:
            logger.warning("LLM upstream rate limit: HTTP 429")
            raise LLMProviderRateLimitError
        if not response.is_success:
            # No se registra ni devuelve el cuerpo de error del proveedor: podría
            # contener información sensible o mensajes específicos del servicio.
            logger.warning("LLM upstream returned HTTP %s", response.status_code)
            raise LLMProviderUnavailableError

        try:
            data = response.json()
            choices = data["choices"]
            message = choices[0]["message"]
            
            # Soporte dual: Chat clásico y Modelos de Razonamiento
            # En modelos de razonamiento (DeepSeek R1, Nemotron Reasoning, etc.), si se
            # agotan los tokens en la reflexión, 'content' puede venir nulo o vacío
            # mientras que el texto útil reside en 'reasoning' o 'reasoning_content'.
            raw_content = message.get("content")
            if isinstance(raw_content, str) and raw_content.strip():
                content = raw_content.strip()
            else:
                reasoning = message.get("reasoning") or message.get("reasoning_content")
                if isinstance(reasoning, str) and reasoning.strip():
                    content = reasoning.strip()
                else:
                    raise ValueError("empty or non-text content")

            response_model = data.get("model")
            output_model = response_model if isinstance(response_model, str) and response_model else model
            usage = data.get("usage") or {}
            input_tokens = self._optional_non_negative_int(usage.get("prompt_tokens"))
            output_tokens = self._optional_non_negative_int(usage.get("completion_tokens"))
        except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
            logger.warning("LLM upstream returned an unsupported response format")
            raise LLMProviderResponseError from exc

        return LLMGenerationResult(
            provider=self.provider_name,
            model=output_model,
            content=content.strip(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    @staticmethod
    def _optional_non_negative_int(value: object) -> int | None:
        """Acepta solo contadores de tokens enteros no negativos."""
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return None
        return value
