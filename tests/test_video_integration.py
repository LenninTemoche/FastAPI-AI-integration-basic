"""Pruebas de integración para el endpoint de análisis de vídeo.

Usan TestClient con dependency_overrides para evitar llamadas reales a la red.
Para pruebas con proveedor real, ejecutar contra el servidor con .env configurado.
"""

import unittest

from fastapi.testclient import TestClient

from app.main import create_app
from app.modules.media.deps import get_video_analysis_service
from app.modules.media.service import VideoAnalysisService
from app.modules.media.ports import VideoAnalysisResult
from app.modules.llm.ports import LLMGenerationResult


class FakeVideoAnalysisService(VideoAnalysisService):
    def __init__(self, result: VideoAnalysisResult | None = None, error: Exception | None = None):
        self.result = result or VideoAnalysisResult(
            generation=LLMGenerationResult(
                provider="fake", model="vision-test", content="análisis simulado",
                input_tokens=10, output_tokens=5,
            ),
            frames_analyzed=2,
            transcript=None,
            transcript_status="no_audio_track",
        )
        self.error = error

    async def analyze(
        self,
        *,
        content: bytes,
        filename: str,
        prompt: str,
        system_prompt: str | None = None,
        include_transcript: bool = True,
    ) -> VideoAnalysisResult:
        if not prompt or not prompt.strip():
            from app.modules.media.ports import MediaInputError
            raise MediaInputError("El prompt no puede estar vacío.")
        if self.error:
            raise self.error
        return self.result


class VideoAnalysisIntegrationTests(unittest.TestCase):
    """Pruebas de contrato HTTP para /api/v1/media/videos/analyze."""

    def setUp(self) -> None:
        self.fake_service = FakeVideoAnalysisService()
        self.app = create_app(enabled=["llm", "media"])
        self.app.dependency_overrides[get_video_analysis_service] = lambda: self.fake_service
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.pop(get_video_analysis_service, None)
        self.client.close()

    def test_analyze_video_success(self) -> None:
        response = self.client.post(
            "/api/v1/media/videos/analyze",
            files={"file": ("video.mp4", b"fake-video-bytes", "video/mp4")},
            data={"prompt": "Describe el video"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["analysis"], "análisis simulado")
        self.assertEqual(body["provider"], "fake")
        self.assertEqual(body["model"], "vision-test")
        self.assertEqual(body["frames_analyzed"], 2)
        self.assertEqual(body["transcript_status"], "no_audio_track")

    def test_analyze_video_unsupported_format(self) -> None:
        response = self.client.post(
            "/api/v1/media/videos/analyze",
            files={"file": ("document.txt", b"text", "text/plain")},
            data={"prompt": "test"},
        )
        self.assertEqual(response.status_code, 415)

    def test_analyze_video_empty_prompt(self) -> None:
        response = self.client.post(
            "/api/v1/media/videos/analyze",
            files={"file": ("video.mp4", b"fake-video", "video/mp4")},
            data={"prompt": "   "},
        )
        self.assertEqual(response.status_code, 422)

    def test_openapi_documents_video_errors(self) -> None:
        schema = self.client.get("/openapi.json").json()
        operation = schema["paths"]["/api/v1/media/videos/analyze"]["post"]
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