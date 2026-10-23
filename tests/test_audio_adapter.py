"""Pruebas del adaptador de audio (Whisper) usando HTTPX MockTransport (sin Internet ni API real)."""

import json
import unittest

import httpx

from app.core.config import Settings
from app.modules.media.adapters.openai_audio import OpenAICompatibleAudioTranscriber
from app.modules.llm.ports import (
    LLMNotConfiguredError,
    LLMProviderRateLimitError,
    LLMProviderResponseError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
)


def configured_settings(**overrides) -> Settings:
    defaults = {
        "_env_file": None,
        "llm_provider": "openai_compatible",
        "llm_api_key": "test-secret-key",
        "llm_base_url": "https://llm.example.test/v1",
        "llm_model": "test-model",
        "llm_timeout_seconds": 3,
        "llm_max_tokens": 64,
        "llm_temperature": 0.1,
        "media_transcription_model": "whisper-large-v3",
        "media_max_audio_mb": 25,
    }
    defaults.update(overrides)
    return Settings(**defaults)


class AudioTranscriberTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_transcribes_audio_and_normalizes_response(self) -> None:
        captured: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["authorization"] = request.headers.get("Authorization")
            return httpx.Response(
                200,
                json={
                    "text": "  Hola, esto es una transcripción  ",
                    "model": "whisper-large-v3",
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleAudioTranscriber(
                settings=configured_settings(), client=client
            )
            result = await provider.transcribe(
                content=b"fake-audio-bytes",
                filename="audio.mp3",
                content_type="audio/mpeg",
                language="es",
            )

        self.assertEqual(
            captured["url"], "https://llm.example.test/v1/audio/transcriptions"
        )
        self.assertEqual(captured["authorization"], "Bearer test-secret-key")
        self.assertEqual(result.text, "Hola, esto es una transcripción")
        self.assertEqual(result.provider, "openai_compatible")
        self.assertEqual(result.model, "whisper-large-v3")
        self.assertNotIn("test-secret-key", repr(result))

    async def test_missing_transcription_model_raises_not_configured(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.fail("No debe salir una solicitud si falta la configuración")
            return httpx.Response(500)

        settings = configured_settings(media_transcription_model=None)
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleAudioTranscriber(settings=settings, client=client)
            with self.assertRaises(LLMNotConfiguredError):
                await provider.transcribe(
                    content=b"fake-audio", filename="audio.mp3", content_type="audio/mpeg"
                )

    async def test_http_429_maps_to_rate_limit_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, json={"error": {"message": "rate limited"}})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleAudioTranscriber(
                settings=configured_settings(), client=client
            )
            with self.assertRaises(LLMProviderRateLimitError):
                await provider.transcribe(
                    content=b"fake-audio", filename="audio.mp3", content_type="audio/mpeg"
                )

    async def test_upstream_5xx_maps_to_unavailable_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={"error": {"message": "internal error"}})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleAudioTranscriber(
                settings=configured_settings(), client=client
            )
            with self.assertRaises(LLMProviderUnavailableError):
                await provider.transcribe(
                    content=b"fake-audio", filename="audio.mp3", content_type="audio/mpeg"
                )

    async def test_timeout_maps_to_timeout_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timeout", request=request)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleAudioTranscriber(
                settings=configured_settings(), client=client
            )
            with self.assertRaises(LLMProviderTimeoutError):
                await provider.transcribe(
                    content=b"fake-audio", filename="audio.mp3", content_type="audio/mpeg"
                )

    async def test_invalid_response_format_maps_to_response_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"unexpected": "shape"})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleAudioTranscriber(
                settings=configured_settings(), client=client
            )
            with self.assertRaises(LLMProviderResponseError):
                await provider.transcribe(
                    content=b"fake-audio", filename="audio.mp3", content_type="audio/mpeg"
                )


if __name__ == "__main__":
    unittest.main()
