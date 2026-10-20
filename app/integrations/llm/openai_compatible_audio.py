"""Adaptador de transcripción para APIs compatibles con OpenAI Audio Transcriptions."""

import logging
from pathlib import Path

import httpx

from app.core.config import Settings
from app.services.ports.llm_provider import (
    LLMNotConfiguredError,
    LLMProviderRateLimitError,
    LLMProviderResponseError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
)
from app.services.ports.media_provider import MediaTranscriptionResult

logger = logging.getLogger(__name__)


class OpenAICompatibleAudioTranscriber:
    """Transcribe archivos mediante POST {base_url}/audio/transcriptions."""

    provider_name = "openai_compatible"

    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._client = client

    async def transcribe(
        self,
        *,
        content: bytes,
        filename: str,
        content_type: str,
        language: str | None = None,
    ) -> MediaTranscriptionResult:
        api_key = (
            self._settings.llm_api_key.get_secret_value().strip()
            if self._settings.llm_api_key else ""
        )
        base_url = str(self._settings.llm_base_url).rstrip("/") if self._settings.llm_base_url else ""
        model = (self._settings.media_transcription_model or "").strip()
        if not api_key or not base_url or not model:
            raise LLMNotConfiguredError(
                "Configure LLM_API_KEY, LLM_BASE_URL and MEDIA_TRANSCRIPTION_MODEL on the server."
            )
        suffix = Path(filename).suffix.lower()
        safe_filename = f"audio{suffix if suffix else '.bin'}"
        fields = {"model": model, "response_format": "json"}
        if language:
            fields["language"] = language
        try:
            response = await self._client.post(
                f"{base_url}/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
                data=fields,
                files={"file": (safe_filename, content, content_type)},
            )
        except httpx.TimeoutException as exc:
            raise LLMProviderTimeoutError from exc
        except httpx.RequestError as exc:
            logger.warning("Audio transcription transport error: %s", type(exc).__name__)
            raise LLMProviderUnavailableError from exc

        if response.status_code == 429:
            logger.warning("Audio transcription provider rate limit: HTTP 429")
            raise LLMProviderRateLimitError
        if not response.is_success:
            logger.warning("Audio transcription provider returned HTTP %s", response.status_code)
            raise LLMProviderUnavailableError
        try:
            data = response.json()
            text = data.get("text")
            if not isinstance(text, str):
                raise ValueError("missing transcript text")
            actual_model = data.get("model")
            if not isinstance(actual_model, str) or not actual_model.strip():
                actual_model = model
        except (ValueError, TypeError, AttributeError) as exc:
            logger.warning("Audio transcription provider returned an unsupported response format")
            raise LLMProviderResponseError from exc

        return MediaTranscriptionResult(
            provider=self.provider_name,
            model=actual_model,
            text=text.strip(),
        )
