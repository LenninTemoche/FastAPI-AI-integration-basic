"""Pruebas unitarias de LLMService sin FastAPI ni conexiones externas."""

import unittest

from app.services.llm_service import LLMService
from app.services.ports.llm_provider import LLMGenerationResult


class FakeProvider:
    def __init__(self) -> None:
        self.last_prompt: str | None = None
        self.last_system_prompt: str | None = None

    async def generate(
        self,
        *,
        prompt: str,
        system_prompt: str | None = None,
    ) -> LLMGenerationResult:
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt
        return LLMGenerationResult(
            provider="fake",
            model="fake-model",
            content="Respuesta de prueba",
            input_tokens=4,
            output_tokens=3,
        )


class LLMServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_service_normalizes_prompts_and_returns_provider_result(self) -> None:
        provider = FakeProvider()
        service = LLMService(provider)

        result = await service.ask(
            prompt="  ¿Qué es una API REST?  ",
            system_prompt="  Responde brevemente.  ",
        )

        self.assertEqual(provider.last_prompt, "¿Qué es una API REST?")
        self.assertEqual(provider.last_system_prompt, "Responde brevemente.")
        self.assertEqual(result.content, "Respuesta de prueba")
        self.assertEqual(result.provider, "fake")
        self.assertEqual(result.input_tokens, 4)

    async def test_service_does_not_pass_blank_system_prompt(self) -> None:
        provider = FakeProvider()
        service = LLMService(provider)

        await service.ask(prompt="hola", system_prompt="   ")

        self.assertIsNone(provider.last_system_prompt)

    async def test_service_rejects_blank_prompt_for_non_http_consumers(self) -> None:
        service = LLMService(FakeProvider())
        with self.assertRaisesRegex(ValueError, "prompt must not be empty"):
            await service.ask(prompt="   ")
