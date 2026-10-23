"""Pruebas de contrato HTTP para endpoints de multimedia (sin API key real)."""

import unittest

from fastapi.testclient import TestClient

from app.main import create_app
from app.modules.media.deps import get_audio_transcription_service, get_video_analysis_service
from app.modules.media.service import AudioTranscriptionService, VideoAnalysisService
from app.modules.media.ports import (
    ExtractedVideoMedia,
    MediaInputError,
    MediaPayloadTooLargeError,
    MediaProcessorUnavailableError,
    MediaTranscriptionResult,
    TranscriptStatus,
    VideoAnalysisResult,
)
from app.modules.llm.ports import LLMGenerationResult


class FakeAudioTranscriptionService(AudioTranscriptionService):
    def __init__(self, result: MediaTranscriptionResult | None = None, error: Exception | None = None):
        self.result = result or MediaTranscriptionResult(
            provider="fake", model="whisper-test", text="transcripción simulada"
        )
        self.error = error
        self.last_language: str | None = None

    async def transcribe(
        self,
        *,
        content: bytes,
        filename: str,
        content_type: str,
        language: str | None = None,
    ) -> MediaTranscriptionResult:
        self.last_language = language.strip() if language else None
        if self.error:
            raise self.error
        return self.result


class FakeVideoAnalysisService(VideoAnalysisService):
    def __init__(self, result: VideoAnalysisResult | None = None, error: Exception | None = None):
        from app.modules.llm.ports import LLMGenerationResult
        self.result = result or VideoAnalysisResult(
            generation=LLMGenerationResult(
                provider="fake", model="gpt-4o", content="análisis simulado",
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
            raise MediaInputError("El prompt no puede estar vacío.")
        if self.error:
            raise self.error
        return self.result


class MediaEndpointsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_audio = FakeAudioTranscriptionService()
        self.fake_video = FakeVideoAnalysisService()
        self.app = create_app(enabled=["llm", "media"])
        self.app.dependency_overrides[get_audio_transcription_service] = lambda: self.fake_audio
        self.app.dependency_overrides[get_video_analysis_service] = lambda: self.fake_video
        self.context = TestClient(self.app)
        self.client = self.context.__enter__()

    def tearDown(self) -> None:
        self.app.dependency_overrides.pop(get_audio_transcription_service, None)
        self.app.dependency_overrides.pop(get_video_analysis_service, None)
        self.context.__exit__(None, None, None)

    def test_transcribe_audio_returns_200(self) -> None:
        response = self.client.post(
            "/api/v1/media/transcriptions",
            files={"file": ("audio.mp3", b"fake-audio-bytes", "audio/mpeg")},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["text"], "transcripción simulada")
        self.assertEqual(body["provider"], "fake")
        self.assertEqual(body["model"], "whisper-test")

    def test_transcribe_audio_with_language(self) -> None:
        response = self.client.post(
            "/api/v1/media/transcriptions",
            files={"file": ("audio.wav", b"fake-audio", "audio/wav")},
            data={"language": "es"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.fake_audio.last_language, "es")

    def test_transcribe_unsupported_format_returns_415(self) -> None:
        response = self.client.post(
            "/api/v1/media/transcriptions",
            files={"file": ("document.txt", b"text content", "text/plain")},
        )
        self.assertEqual(response.status_code, 415)

    def test_transcribe_empty_file_returns_422(self) -> None:
        response = self.client.post(
            "/api/v1/media/transcriptions",
            files={"file": ("empty.mp3", b"", "audio/mpeg")},
        )
        self.assertEqual(response.status_code, 422)

    def test_analyze_video_returns_200(self) -> None:
        response = self.client.post(
            "/api/v1/media/videos/analyze",
            files={"file": ("video.mp4", b"fake-video-bytes", "video/mp4")},
            data={"prompt": "Describe el video"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["analysis"], "análisis simulado")
        self.assertEqual(body["provider"], "fake")
        self.assertEqual(body["model"], "gpt-4o")
        self.assertEqual(body["frames_analyzed"], 2)
        self.assertEqual(body["transcript_status"], "no_audio_track")

    def test_analyze_video_with_transcript(self) -> None:
        self.fake_video.result = VideoAnalysisResult(
            generation=LLMGenerationResult(
                provider="fake", model="gpt-4o", content="análisis con audio",
                input_tokens=10, output_tokens=5,
            ),
            frames_analyzed=3,
            transcript="transcripción de audio",
            transcript_status="completed",
        )
        response = self.client.post(
            "/api/v1/media/videos/analyze",
            files={"file": ("video.mp4", b"fake-video", "video/mp4")},
            data={"prompt": "Describe", "include_transcript": "true"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["transcript"], "transcripción de audio")
        self.assertEqual(body["transcript_status"], "completed")

    def test_analyze_video_empty_prompt_returns_422(self) -> None:
        response = self.client.post(
            "/api/v1/media/videos/analyze",
            files={"file": ("video.mp4", b"fake-video", "video/mp4")},
            data={"prompt": "   "},
        )
        self.assertEqual(response.status_code, 422)

    def test_analyze_video_unsupported_format_returns_415(self) -> None:
        response = self.client.post(
            "/api/v1/media/videos/analyze",
            files={"file": ("document.txt", b"text", "text/plain")},
            data={"prompt": "test"},
        )
        self.assertEqual(response.status_code, 415)

    def test_transcribe_provider_error_returns_503(self) -> None:
        self.fake_audio.error = MediaProcessorUnavailableError("proveedor no disponible")
        response = self.client.post(
            "/api/v1/media/transcriptions",
            files={"file": ("audio.mp3", b"audio", "audio/mpeg")},
        )
        self.assertEqual(response.status_code, 503)

    def test_video_provider_error_returns_503(self) -> None:
        self.fake_video.error = MediaProcessorUnavailableError("proveedor no disponible")
        response = self.client.post(
            "/api/v1/media/videos/analyze",
            files={"file": ("video.mp4", b"video", "video/mp4")},
            data={"prompt": "test"},
        )
        self.assertEqual(response.status_code, 503)

    def test_openapi_documents_media_endpoints(self) -> None:
        schema = self.client.get("/openapi.json").json()
        paths = schema["paths"]
        self.assertIn("/api/v1/media/transcriptions", paths)
        self.assertIn("/api/v1/media/videos/analyze", paths)
        transcribe_op = paths["/api/v1/media/transcriptions"]["post"]
        self.assertIn("200", transcribe_op["responses"])
        self.assertIn("415", transcribe_op["responses"])
        self.assertIn("422", transcribe_op["responses"])
        self.assertIn("502", transcribe_op["responses"])
        self.assertIn("503", transcribe_op["responses"])
        self.assertIn("504", transcribe_op["responses"])
        video_op = paths["/api/v1/media/videos/analyze"]["post"]
        self.assertIn("200", video_op["responses"])


if __name__ == "__main__":
    unittest.main()