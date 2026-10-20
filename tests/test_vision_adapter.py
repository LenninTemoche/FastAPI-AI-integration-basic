"""Pruebas del adaptador de visión usando HTTPX MockTransport (sin Internet ni API real)."""

import base64
import json
import unittest

import httpx

from app.core.config import Settings
from app.integrations.llm.openai_compatible_vision import OpenAICompatibleVisionProvider
from app.services.ports.llm_provider import (
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
        "llm_model": "gpt-4o",
        "llm_timeout_seconds": 3,
        "llm_max_tokens": 64,
        "llm_temperature": 0.1,
    }
    defaults.update(overrides)
    return Settings(**defaults)


class VisionProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_analyzes_frames_and_normalizes_response(self) -> None:
        captured: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["authorization"] = request.headers.get("Authorization")
            captured["payload"] = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "model": "gpt-4o",
                    "choices": [{"message": {"content": "  El video muestra un perro  "}}],
                    "usage": {"prompt_tokens": 100, "completion_tokens": 25},
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleVisionProvider(
                settings=configured_settings(), client=client
            )
            frame = base64.b64decode("aGVsbG8=")  # fake frame bytes
            result = await provider.analyze_frames(
                frames=(frame,),
                prompt="Describe el video",
                system_prompt="Eres un asistente",
                frame_interval_seconds=5,
                transcript=None,
            )

        self.assertEqual(captured["url"], "https://llm.example.test/v1/chat/completions")
        self.assertEqual(captured["authorization"], "Bearer test-secret-key")
        payload = captured["payload"]
        self.assertEqual(payload["model"], "gpt-4o")
        self.assertEqual(len(payload["messages"]), 2)  # system + user
        user_content = payload["messages"][1]["content"]
        self.assertEqual(user_content[0]["type"], "text")
        self.assertEqual(user_content[0]["text"], "Describe el video\n\nSe adjuntan 1 fotogramas muestreados aproximadamente cada 5 segundos, comenzando cerca del inicio del video. Describe solo lo que puede inferirse de los fotogramas; no inventes eventos que ocurran entre ellos.")
        self.assertEqual(user_content[1]["type"], "text")
        self.assertEqual(user_content[1]["text"], "Fotograma 1 (aprox. segundo 0):")
        self.assertEqual(user_content[2]["type"], "image_url")
        self.assertEqual(result.content, "El video muestra un perro")
        self.assertEqual(result.provider, "openai_compatible")
        self.assertEqual(result.model, "gpt-4o")
        self.assertEqual(result.input_tokens, 100)
        self.assertEqual(result.output_tokens, 25)
        self.assertNotIn("test-secret-key", repr(result))

    async def test_with_transcript_includes_it_in_prompt(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            # system_prompt puede ser None, así que el user message está en [0] o [1]
            user_content = None
            for msg in payload["messages"]:
                if msg.get("role") == "user":
                    user_content = msg["content"]
                    break
            self.assertIsNotNone(user_content)
            text_parts = [p for p in user_content if p.get("type") == "text"]
            instructions = text_parts[0]["text"]
            self.assertIn("Transcripción de audio extraída del video:", instructions)
            self.assertIn("Hola desde el audio", instructions)
            return httpx.Response(
                200,
                json={"model": "gpt-4o", "choices": [{"message": {"content": "ok"}}]},
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleVisionProvider(
                settings=configured_settings(), client=client
            )
            frame = base64.b64decode("aGVsbG8=")
            await provider.analyze_frames(
                frames=(frame,),
                prompt="Describe",
                system_prompt=None,
                frame_interval_seconds=5,
                transcript="Hola desde el audio",
            )

    async def test_no_frames_raises_response_error(self) -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200))) as client:
            provider = OpenAICompatibleVisionProvider(
                settings=configured_settings(), client=client
            )
            with self.assertRaises(LLMProviderResponseError):
                await provider.analyze_frames(
                    frames=(),
                    prompt="test",
                    system_prompt=None,
                    frame_interval_seconds=5,
                    transcript=None,
                )

    async def test_http_429_maps_to_rate_limit_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleVisionProvider(
                settings=configured_settings(), client=client
            )
            frame = base64.b64decode("aGVsbG8=")
            with self.assertRaises(LLMProviderRateLimitError):
                await provider.analyze_frames(
                    frames=(frame,),
                    prompt="test",
                    system_prompt=None,
                    frame_interval_seconds=5,
                    transcript=None,
                )

    async def test_upstream_5xx_maps_to_unavailable_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleVisionProvider(
                settings=configured_settings(), client=client
            )
            frame = base64.b64decode("aGVsbG8=")
            with self.assertRaises(LLMProviderUnavailableError):
                await provider.analyze_frames(
                    frames=(frame,),
                    prompt="test",
                    system_prompt=None,
                    frame_interval_seconds=5,
                    transcript=None,
                )

    async def test_timeout_maps_to_timeout_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timeout", request=request)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleVisionProvider(
                settings=configured_settings(), client=client
            )
            frame = base64.b64decode("aGVsbG8=")
            with self.assertRaises(LLMProviderTimeoutError):
                await provider.analyze_frames(
                    frames=(frame,),
                    prompt="test",
                    system_prompt=None,
                    frame_interval_seconds=5,
                    transcript=None,
                )

    async def test_invalid_response_format_maps_to_response_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"unexpected": "shape"})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleVisionProvider(
                settings=configured_settings(), client=client
            )
            frame = base64.b64decode("aGVsbG8=")
            with self.assertRaises(LLMProviderResponseError):
                await provider.analyze_frames(
                    frames=(frame,),
                    prompt="test",
                    system_prompt=None,
                    frame_interval_seconds=5,
                    transcript=None,
                )


if __name__ == "__main__":
    unittest.main()
