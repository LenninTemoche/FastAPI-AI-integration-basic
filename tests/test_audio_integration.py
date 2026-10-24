"""Pruebas de integración para el endpoint de transcripción de audio.

Usan TestClient con dependency_overrides para evitar llamadas reales a la red.
Para pruebas con proveedor real, ejecutar contra el servidor con .env configurado.
"""

import unittest

from fastapi.testclient import TestClient

from app.factory import create_app
from app.modules.media.deps import get_audio_transcription_service
from app.modules.media.service import AudioTranscriptionService
from app.modules.media.ports import MediaTranscriptionResult


class FakeAudioTranscriptionService(AudioTranscriptionService):
    def __init__(self, result: MediaTranscriptionResult | None = None, error: Exception | None = None):
        self.result = result or MediaTranscriptionResult(
            provider="fake", model="whisper-test", text="transcripción simulada"
        )
        self.error = error

    async def transcribe(
        self,
        *,
        content: bytes,
        filename: str,
        content_type: str,
        language: str | None = None,
    ) -> MediaTranscriptionResult:
        if self.error:
            raise self.error
        return self.result


class AudioTranscriptionIntegrationTests(unittest.TestCase):
    """Pruebas de contrato HTTP para /api/v1/media/transcriptions."""

    def setUp(self) -> None:
        self.fake_service = FakeAudioTranscriptionService()
        self.app = create_app(enabled=["llm", "media"])
        self.app.dependency_overrides[get_audio_transcription_service] = lambda: self.fake_service
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.pop(get_audio_transcription_service, None)
        self.client.close()

    def test_transcribe_audio_success(self) -> None:
        response = self.client.post(
            "/api/v1/media/transcriptions",
            files={"file": ("audio.mp3", b"fake-audio-bytes", "audio/mpeg")},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["text"], "transcripción simulada")
        self.assertEqual(body["provider"], "fake")
        self.assertEqual(body["model"], "whisper-test")

    def test_transcribe_audio_unsupported_format(self) -> None:
        response = self.client.post(
            "/api/v1/media/transcriptions",
            files={"file": ("document.txt", b"text content", "text/plain")},
        )
        self.assertEqual(response.status_code, 415)

    def test_transcribe_audio_empty_file(self) -> None:
        response = self.client.post(
            "/api/v1/media/transcriptions",
            files={"file": ("empty.mp3", b"", "audio/mpeg")},
        )
        self.assertEqual(response.status_code, 422)

    def test_openapi_documents_audio_errors(self) -> None:
        schema = self.client.get("/openapi.json").json()
        operation = schema["paths"]["/api/v1/media/transcriptions"]["post"]
        self.assertIn("200", operation["responses"])
        for code in ("413", "415", "422", "502", "503", "504"):
            with self.subTest(status=code):
                self.assertIn(code, operation["responses"])
                self.assertEqual(
                    operation["responses"][code]["content"]["application/json"]["schema"]["$ref"],
                    "#/components/schemas/ErrorResponse",
                )


if __name__ == "__main__":
    unittest.main()