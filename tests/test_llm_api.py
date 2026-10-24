"""Pruebas de contrato HTTP para el endpoint LLM (sin API key real)."""

import unittest

from fastapi.testclient import TestClient

from app.factory import create_app
from app.modules.llm.deps import get_llm_service
from app.modules.llm.ports import (
    LLMGenerationResult,
    LLMNotConfiguredError,
    LLMProviderRateLimitError,
    LLMProviderResponseError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
)


class FakeLLMService:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.last_prompt: str | None = None
        self.last_system_prompt: str | None = None

    async def ask(self, *, prompt: str, system_prompt: str | None = None):
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt
        if self.error:
            raise self.error
        return LLMGenerationResult(
            provider="fake",
            model="test-model",
            content="Respuesta simulada",
            input_tokens=5,
            output_tokens=4,
        )


class LLMApiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_service = FakeLLMService()
        self.app = create_app(enabled=["llm"])
        self.app.dependency_overrides[get_llm_service] = lambda: self.fake_service
        self.context = TestClient(self.app)
        self.client = self.context.__enter__()

    def tearDown(self) -> None:
        self.app.dependency_overrides.pop(get_llm_service, None)
        self.context.__exit__(None, None, None)

    def test_valid_request_returns_stable_neutral_contract(self) -> None:
        response = self.client.post(
            "/api/v1/llm/ask",
            json={"prompt": "  Resume el texto  ", "system_prompt": "  En español  "},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "response": "Respuesta simulada",
                "provider": "fake",
                "model": "test-model",
                "usage": {"input_tokens": 5, "output_tokens": 4},
            },
        )
        self.assertEqual(self.fake_service.last_prompt, "Resume el texto")
        self.assertEqual(self.fake_service.last_system_prompt, "En español")

    def test_blank_prompt_is_rejected_with_422(self) -> None:
        response = self.client.post("/api/v1/llm/ask", json={"prompt": "   "})
        self.assertEqual(response.status_code, 422)

    def test_extra_fields_are_rejected_with_422(self) -> None:
        response = self.client.post(
            "/api/v1/llm/ask",
            json={"prompt": "hola", "api_key": "must-not-be-client-controlled"},
        )
        self.assertEqual(response.status_code, 422)

    def test_prompt_over_limit_is_rejected_with_422(self) -> None:
        response = self.client.post("/api/v1/llm/ask", json={"prompt": "x" * 12001})
        self.assertEqual(response.status_code, 422)

    def test_errors_are_translated_to_documented_http_statuses(self) -> None:
        cases = (
            (LLMNotConfiguredError(), 503),
            (LLMProviderRateLimitError(), 503),
            (LLMProviderUnavailableError(), 502),
            (LLMProviderResponseError(), 502),
            (LLMProviderTimeoutError(), 504),
        )
        for error, expected_status in cases:
            with self.subTest(error=type(error).__name__):
                self.fake_service.error = error
                response = self.client.post("/api/v1/llm/ask", json={"prompt": "hola"})
                self.assertEqual(response.status_code, expected_status)
                body = response.json()
                self.assertEqual(set(body), {"detail"})
                self.assertIsInstance(body["detail"], str)
                self.assertNotIn("api_key", body["detail"].lower())

    def test_openapi_documents_success_and_gateway_errors(self) -> None:
        schema = self.client.get("/openapi.json").json()
        operation = schema["paths"]["/api/v1/llm/ask"]["post"]
        self.assertIn("200", operation["responses"])
        for code in ("502", "503", "504"):
            with self.subTest(status=code):
                self.assertEqual(
                    operation["responses"][code]["content"]["application/json"]["schema"]["$ref"],
                    "#/components/schemas/ErrorResponse",
                )
        self.assertIn("LLMAskRequest", schema["components"]["schemas"])
        self.assertIn("LLMAskResponse", schema["components"]["schemas"])


if __name__ == "__main__":
    unittest.main()