"""Pruebas del adaptador HTTP usando HTTPX MockTransport (sin Internet ni API real)."""

import json
import unittest

import httpx

from app.core.config import Settings
from app.integrations.llm.openai_compatible import OpenAICompatibleChatProvider
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
        "llm_model": "test-model",
        "llm_timeout_seconds": 3,
        "llm_max_tokens": 64,
        "llm_temperature": 0.1,
    }
    defaults.update(overrides)
    return Settings(**defaults)


class LLMProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_external_provider_url_requires_https(self) -> None:
        with self.assertRaisesRegex(ValueError, "must use HTTPS"):
            configured_settings(llm_base_url="http://llm.example.test/v1")

    async def test_local_loopback_url_may_use_http_for_local_servers(self) -> None:
        settings = configured_settings(llm_base_url="http://127.0.0.1:8001/v1")
        self.assertEqual(str(settings.llm_base_url), "http://127.0.0.1:8001/v1")

    async def test_success_uses_server_side_bearer_key_and_normalizes_response(self) -> None:
        captured: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["authorization"] = request.headers.get("Authorization")
            captured["payload"] = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "model": "actual-model",
                    "choices": [{"message": {"content": "  Texto generado  "}}],
                    "usage": {"prompt_tokens": 12, "completion_tokens": 8},
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleChatProvider(configured_settings(), client)
            result = await provider.generate(
                prompt="Resume este contenido",
                system_prompt="Responde en español",
            )

        self.assertEqual(captured["url"], "https://llm.example.test/v1/chat/completions")
        self.assertEqual(captured["authorization"], "Bearer test-secret-key")
        payload = captured["payload"]
        self.assertEqual(payload["model"], "test-model")
        self.assertEqual(payload["messages"][0], {"role": "system", "content": "Responde en español"})
        self.assertEqual(payload["messages"][1], {"role": "user", "content": "Resume este contenido"})
        self.assertEqual(payload["max_tokens"], 64)
        self.assertEqual(result.content, "Texto generado")
        self.assertEqual(result.provider, "openai_compatible")
        self.assertEqual(result.model, "actual-model")
        self.assertEqual(result.input_tokens, 12)
        self.assertEqual(result.output_tokens, 8)
        self.assertNotIn("test-secret-key", repr(result))

    async def test_missing_provider_configuration_is_explicit_and_does_not_call_network(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.fail("No debe salir una solicitud si falta la configuración")
            return httpx.Response(500)

        settings = configured_settings(llm_api_key=None, llm_base_url=None, llm_model=None)
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleChatProvider(settings, client)
            with self.assertRaises(LLMNotConfiguredError):
                await provider.generate(prompt="hola")

    async def test_http_429_maps_to_rate_limit_exception(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, json={"error": {"message": "sensitive upstream detail"}})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleChatProvider(configured_settings(), client)
            with self.assertRaises(LLMProviderRateLimitError) as captured:
                await provider.generate(prompt="hola")
        self.assertNotIn("sensitive upstream detail", str(captured.exception))
        self.assertNotIn("test-secret-key", str(captured.exception))

    async def test_upstream_5xx_maps_to_safe_provider_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={"error": {"message": "internal provider data"}})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleChatProvider(configured_settings(), client)
            with self.assertRaises(LLMProviderUnavailableError) as captured:
                await provider.generate(prompt="hola")
        self.assertNotIn("internal provider data", str(captured.exception))

    async def test_upstream_auth_error_is_not_misreported_as_client_401(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"error": {"message": "secret provider detail"}})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleChatProvider(configured_settings(), client)
            with self.assertRaises(LLMProviderUnavailableError) as captured:
                await provider.generate(prompt="hola")
        self.assertNotIn("secret provider detail", str(captured.exception))
        self.assertNotIn("test-secret-key", str(captured.exception))

    async def test_invalid_provider_shape_maps_to_response_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"unexpected": "shape"})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleChatProvider(configured_settings(), client)
            with self.assertRaises(LLMProviderResponseError):
                await provider.generate(prompt="hola")

    async def test_timeout_maps_to_timeout_exception(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("internal timeout detail", request=request)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleChatProvider(configured_settings(), client)
            with self.assertRaises(LLMProviderTimeoutError) as captured:
                await provider.generate(prompt="hola")
        self.assertNotIn("internal timeout detail", str(captured.exception))
