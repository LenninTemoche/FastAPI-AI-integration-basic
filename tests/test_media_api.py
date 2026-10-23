"""Contratos HTTP multimodales: UploadFile, límites, esquemas OpenAPI y errores."""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import create_app
from app.core.config import Settings, get_settings
from app.modules.media.deps import get_audio_transcription_service, get_video_analysis_service
from app.modules.llm.ports import LLMGenerationResult
from app.modules.media.ports import MediaTranscriptionResult, VideoAnalysisResult


class FakeAudioService:
    async def transcribe(self, **kwargs):
        return MediaTranscriptionResult("fake", "transcribe-model", "texto de prueba")


class FakeVideoService:
    async def analyze(self, **kwargs):
        return VideoAnalysisResult(
            generation=LLMGenerationResult("fake", "vision-model", "análisis de prueba", 30, 10),
            frames_analyzed=2,
            transcript="texto de audio",
            transcript_status="completed",
        )


class MediaApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(enabled=["llm", "media"])
        self.app.dependency_overrides[get_audio_transcription_service] = lambda: FakeAudioService()
        self.app.dependency_overrides[get_video_analysis_service] = lambda: FakeVideoService()
        self.app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None)
        self.context = TestClient(self.app)
        self.client = self.context.__enter__()

    def tearDown(self):
        self.app.dependency_overrides.pop(get_audio_transcription_service, None)
        self.app.dependency_overrides.pop(get_video_analysis_service, None)
        self.app.dependency_overrides.pop(get_settings, None)
        self.context.__exit__(None, None, None)

    def test_transcription_endpoint_contract(self):
        response = self.client.post("/api/v1/media/transcriptions", files={"file": ("voice.wav", b"fake", "audio/wav")}, data={"language": "es"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"text": "texto de prueba", "provider": "fake", "model": "transcribe-model"})

    def test_rejects_unsupported_audio_extension(self):
        response = self.client.post("/api/v1/media/transcriptions", files={"file": ("program.exe", b"fake", "application/octet-stream")})
        self.assertEqual(response.status_code, 415)
        self.assertIn("detail", response.json())

    def test_video_analysis_endpoint_contract(self):
        response = self.client.post(
            "/api/v1/media/videos/analyze",
            files={"file": ("clip.mp4", b"fake-video", "video/mp4")},
            data={"prompt": "Resume la escena", "include_transcript": "true"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["analysis"], "análisis de prueba")
        self.assertEqual(body["frames_analyzed"], 2)
        self.assertEqual(body["transcript_status"], "completed")
        self.assertIn("usage", body)

    def test_rejects_unsupported_video_extension(self):
        response = self.client.post(
            "/api/v1/media/videos/analyze",
            files={"file": ("clip.pdf", b"not-video", "application/pdf")},
            data={"prompt": "Resume la escena"},
        )
        self.assertEqual(response.status_code, 415)

    def test_openapi_documents_both_multimodal_routes(self):
        schema = self.client.get("/openapi.json").json()
        paths = schema["paths"]
        self.assertIn("/api/v1/media/transcriptions", paths)
        self.assertIn("/api/v1/media/videos/analyze", paths)
        self.assertIn("multipart/form-data", paths["/api/v1/media/transcriptions"]["post"]["requestBody"]["content"])

    def test_audio_upload_limit_is_enforced_before_provider_call(self):
        fake = FakeAudioService()
        self.app.dependency_overrides[get_audio_transcription_service] = lambda: fake
        small_limit = Settings(_env_file=None, media_max_audio_mb=1)
        self.app.dependency_overrides[get_settings] = lambda: small_limit
        response = self.client.post(
            "/api/v1/media/transcriptions",
            files={"file": ("voice.wav", b"x" * (1024 * 1024 + 1), "audio/wav")},
        )
        self.assertEqual(response.status_code, 413)
        # La respuesta es temprana: no se llama al servicio falso.
        self.assertEqual(response.json().get("detail"), "El archivo excede el tamaño máximo permitido.")


if __name__ == "__main__":
    unittest.main()