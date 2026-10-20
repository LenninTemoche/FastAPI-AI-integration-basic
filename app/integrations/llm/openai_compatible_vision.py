"""Adaptador de análisis visual con fotogramas JPEG vía Chat Completions compatible.

El proveedor y el modelo deben admitir mensajes user.content multimodales con image_url.
No se intenta enviar un archivo de video crudo al endpoint de chat: el procesador extrae
una secuencia acotada de fotogramas y el servicio puede adjuntar la transcripción de audio.
"""

import base64
import logging
from typing import Any

import httpx

from app.core.config import Settings
from app.services.ports.llm_provider import (
    LLMGenerationResult,
    LLMNotConfiguredError,
    LLMProviderRateLimitError,
    LLMProviderResponseError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
)

logger = logging.getLogger(__name__)


class OpenAICompatibleVisionProvider:
    """Analiza fotogramas como data URLs en una petición Chat Completions."""

    provider_name = "openai_compatible"

    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._client = client

    async def analyze_frames(
        self,
        *,
        frames: tuple[bytes, ...],
        prompt: str,
        system_prompt: str | None,
        frame_interval_seconds: int,
        transcript: str | None = None,
    ) -> LLMGenerationResult:
        api_key = (
            self._settings.llm_api_key.get_secret_value().strip()
            if self._settings.llm_api_key else ""
        )
        base_url = str(self._settings.llm_base_url).rstrip("/") if self._settings.llm_base_url else ""
        model = (self._settings.llm_model or "").strip()
        if not api_key or not base_url or not model:
            raise LLMNotConfiguredError(
                "Configure LLM_API_KEY, LLM_BASE_URL and LLM_MODEL on the server."
            )
        if not frames:
            raise LLMProviderResponseError

        instructions = (
            f"{prompt.strip()}\n\n"
            f"Se adjuntan {len(frames)} fotogramas muestreados aproximadamente cada "
            f"{frame_interval_seconds} segundos, comenzando cerca del inicio del video. "
            "Describe solo lo que puede inferirse de los fotogramas; no inventes eventos "
            "que ocurran entre ellos."
        )
        if transcript and transcript.strip():
            instructions += "\n\nTranscripción de audio extraída del video:\n" + transcript.strip()

        user_content: list[dict[str, Any]] = [{"type": "text", "text": instructions}]
        for index, frame in enumerate(frames):
            encoded = base64.b64encode(frame).decode("ascii")
            seconds = index * frame_interval_seconds
            user_content.append({
                "type": "text",
                "text": f"Fotograma {index + 1} (aprox. segundo {seconds}):",
            })
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{encoded}"},
            })

        messages: list[dict[str, Any]] = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": user_content})
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": self._settings.llm_temperature,
            "max_tokens": self._settings.llm_max_tokens,
        }
        try:
            response = await self._client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=payload,
            )
        except httpx.TimeoutException as exc:
            raise LLMProviderTimeoutError from exc
        except httpx.RequestError as exc:
            logger.warning("Video vision transport error: %s", type(exc).__name__)
            raise LLMProviderUnavailableError from exc
        if response.status_code == 429:
            logger.warning("Video vision provider rate limit: HTTP 429")
            raise LLMProviderRateLimitError
        if not response.is_success:
            logger.warning("Video vision provider returned HTTP %s", response.status_code)
            raise LLMProviderUnavailableError

        try:
            data = response.json()
            message = data["choices"][0]["message"]
            content = self._extract_text(message)
            response_model = data.get("model")
            actual_model = response_model if isinstance(response_model, str) and response_model.strip() else model
            usage = data.get("usage") or {}
            input_tokens = self._optional_non_negative_int(usage.get("prompt_tokens"))
            output_tokens = self._optional_non_negative_int(usage.get("completion_tokens"))
        except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
            logger.warning("Video vision provider returned an unsupported response format")
            raise LLMProviderResponseError from exc
        return LLMGenerationResult(
            provider=self.provider_name,
            model=actual_model,
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    @staticmethod
    def _extract_text(message: dict[str, Any]) -> str:
        """Normaliza respuestas de chat y tolera content vacío más reasoning fallbacks.

        El fallback mantiene compatibilidad con proveedores de razonamiento; no es
        una garantía de que todos los modelos deban exponer campos reasoning.
        """
        raw_content = message.get("content")
        if isinstance(raw_content, str) and raw_content.strip():
            return raw_content.strip()
        if isinstance(raw_content, list):
            parts = [
                part.get("text", "").strip()
                for part in raw_content
                if isinstance(part, dict)
                and isinstance(part.get("text"), str)
                and part.get("text", "").strip()
            ]
            if parts:
                return "\n".join(parts)
        reasoning = message.get("reasoning") or message.get("reasoning_content")
        if isinstance(reasoning, str) and reasoning.strip():
            return reasoning.strip()
        raise ValueError("empty or non-text content")

    @staticmethod
    def _optional_non_negative_int(value: object) -> int | None:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return None
        return value
