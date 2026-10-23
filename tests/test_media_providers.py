"""Pruebas de adaptadores de audio y visión sin red ni API key real."""

import json
import unittest

import httpx

from app.core.config import Settings
from app.modules.media.adapters.openai_audio import OpenAICompatibleAudioTranscriber
from app.modules.media.adapters.openai_vision import OpenAICompatibleVisionProvider
from app.modules.llm.ports import LLMNotConfiguredError, LLMProviderResponseError


def media_settings(**overrides) -> Settings:
    values = {
        "_env_file": None,
        "llm_provider": "openai_compatible",
        "llm_api_key": "test-secret",
        "llm_base_url": "https://example.test/v1",
        "llm_model": "vision-test-model",
        "media_transcription_model": "transcribe-test-model",
        "llm_timeout_seconds": 45,
        "llm_max_tokens": 1024,
        "llm_temperature": 0.75,
    }
    values.update(overrides)
    return Settings(**values)


class AudioAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_transcription_uses_multipart_and_returns_normalized_result(self):
        captured = {}
        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["authorization"] = request.headers.get("authorization")
            captured["content_type"] = request.headers.get("content-type")
            captured["body"] = request.content
            return httpx.Response(200, json={"text": "  Hola mundo  "})
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            result = await OpenAICompatibleAudioTranscriber(media_settings(), client).transcribe(
                content=b"fake-audio", filename="upload.wav", content_type="audio/wav", language="es"
            )
        self.assertEqual(captured["url"], "https://example.test/v1/audio/transcriptions")
        self.assertEqual(captured["authorization"], "Bearer test-secret")
        self.assertIn("multipart/form-data", captured["content_type"])
        self.assertIn(b"transcribe-test-model", captured["body"])
        self.assertIn(b"language", captured["body"])
        self.assertEqual(result.text, "Hola mundo")
        self.assertEqual(result.model, "transcribe-test-model")

    async def test_missing_transcription_model_fails_before_network(self):
        def handler(request: httpx.Request) -> httpx.Response:
            self.fail("No se debe llamar a red si falta el modelo de transcripción")
            return httpx.Response(500)
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleAudioTranscriber(media_settings(media_transcription_model=None), client)
            with self.assertRaises(LLMNotConfiguredError):
                await provider.transcribe(content=b"abc", filename="a.wav", content_type="audio/wav")

    async def test_malformed_transcription_response_is_rejected(self):
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"wrong": 1}))) as client:
            provider = OpenAICompatibleAudioTranscriber(media_settings(), client)
            with self.assertRaises(LLMProviderResponseError):
                await provider.transcribe(content=b"abc", filename="a.wav", content_type="audio/wav")


class VisionAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_frames_are_base64_payload_and_reasoning_fallback_is_preserved(self):
        captured = {}
        def handler(request: httpx.Request) -> httpx.Response:
            captured["payload"] = json.loads(request.content)
            return httpx.Response(200, json={
                "model": "vision-returned",
                "choices": [{"message": {"content": None, "reasoning_content": "Análisis visual"}}],
                "usage": {"prompt_tokens": 22, "completion_tokens": 9},
            })
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenAICompatibleVisionProvider(media_settings(), client)
            result = await provider.analyze_frames(
                frames=(b"jpeg-one", b"jpeg-two"), prompt="Describe el video", system_prompt=None,
                frame_interval_seconds=5, transcript="Audio: empieza la reunión",
            )
        self.assertEqual(result.content, "Análisis visual")
        self.assertEqual(result.model, "vision-returned")
        self.assertEqual(result.input_tokens, 22)
        parts = captured["payload"]["messages"][0]["content"]
        self.assertTrue(any(part.get("type") == "image_url" for part in parts))
        self.assertTrue(any("empieza la reunión" in part.get("text", "") for part in parts))
        self.assertIn("data:image/jpeg;base64,", str(parts))

    async def test_blank_content_without_reasoning_is_rejected(self):
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"choices":[{"message":{"content":" "}}]}))) as client:
            provider = OpenAICompatibleVisionProvider(media_settings(), client)
            with self.assertRaises(LLMProviderResponseError):
                await provider.analyze_frames(frames=(b"jpeg",), prompt="Describe", system_prompt=None, frame_interval_seconds=5)
