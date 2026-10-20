"""Pruebas unitarias de servicios multimedia sin FastAPI ni conexiones externas."""

import unittest

from app.core.config import Settings
from app.services.media_service import AudioTranscriptionService, VideoAnalysisService
from app.services.ports.media_provider import (
    ExtractedVideoMedia,
    MediaInputError,
    MediaTranscriptionResult,
    TranscriptStatus,
    VideoAnalysisResult,
)
from app.services.ports.llm_provider import LLMGenerationResult


class FakeTranscriptionProvider:
    def __init__(self, result: MediaTranscriptionResult | None = None, error: Exception | None = None):
        self.result = result or MediaTranscriptionResult(
            provider="fake", model="whisper-test", text="transcripción de prueba"
        )
        self.error = error
        self.last_content: bytes | None = None
        self.last_filename: str | None = None
        self.last_content_type: str | None = None
        self.last_language: str | None = None

    async def transcribe(
        self,
        *,
        content: bytes,
        filename: str,
        content_type: str,
        language: str | None = None,
    ) -> MediaTranscriptionResult:
        self.last_content = content
        self.last_filename = filename
        self.last_content_type = content_type
        self.last_language = language
        if self.error:
            raise self.error
        return self.result


class FakeVisionProvider:
    def __init__(self, result=None, error: Exception | None = None):
        self.result = result or LLMGenerationResult(
            provider="fake", model="gpt-4o", content="análisis de prueba", input_tokens=10, output_tokens=5
        )
        self.error = error
        self.last_frames: tuple | None = None
        self.last_prompt: str | None = None

    async def analyze_frames(
        self,
        *,
        frames: tuple,
        prompt: str,
        system_prompt: str | None = None,
        frame_interval_seconds: int,
        transcript: str | None = None,
    ):
        self.last_frames = frames
        self.last_prompt = prompt
        if self.error:
            raise self.error
        return self.result


class FakeVideoProcessor:
    """Procesador falso async para pruebas de servicio."""

    def __init__(self, frames: tuple = (b"frame1", b"frame2"), audio_mp3: bytes | None = None):
        self.frames = frames
        self.audio_mp3 = audio_mp3

    async def extract(
        self,
        *,
        content: bytes,
        filename: str,
        content_type: str = "video/mp4",
        max_frames: int = 8,
        max_duration_seconds: int = 120,
        frame_interval_seconds: int = 5,
        processing_timeout_seconds: float = 60.0,
        include_audio: bool = True,
    ) -> ExtractedVideoMedia:
        return ExtractedVideoMedia(
            frames=self.frames,
            audio_mp3=self.audio_mp3,
            frame_interval_seconds=frame_interval_seconds,
        )


class AudioTranscriptionServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_transcribes_audio_and_returns_result(self) -> None:
        provider = FakeTranscriptionProvider()
        service = AudioTranscriptionService(provider)

        result = await service.transcribe(
            content=b"audio-bytes",
            filename="test.mp3",
            content_type="audio/mpeg",
            language="es",
        )

        self.assertEqual(result.text, "transcripción de prueba")
        self.assertEqual(provider.last_content, b"audio-bytes")
        self.assertEqual(provider.last_filename, "test.mp3")
        self.assertEqual(provider.last_content_type, "audio/mpeg")
        self.assertEqual(provider.last_language, "es")

    async def test_rejects_empty_file(self) -> None:
        provider = FakeTranscriptionProvider()
        service = AudioTranscriptionService(provider)

        with self.assertRaises(MediaInputError):
            await service.transcribe(
                content=b"", filename="test.mp3", content_type="audio/mpeg"
            )

    async def test_normalizes_language(self) -> None:
        provider = FakeTranscriptionProvider()
        service = AudioTranscriptionService(provider)

        await service.transcribe(
            content=b"audio", filename="test.mp3", content_type="audio/mpeg", language="  es  "
        )
        self.assertEqual(provider.last_language, "es")


class VideoAnalysisServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_analyzes_video_with_transcript(self) -> None:
        processor = FakeVideoProcessor(audio_mp3=b"audio-bytes")
        fake_transcriber = FakeTranscriptionProvider()
        fake_vision = FakeVisionProvider()

        service = VideoAnalysisService(
            processor=processor,
            vision_provider=fake_vision,
            transcriber=fake_transcriber,
        )

        result = await service.analyze(
            content=b"video-bytes",
            filename="test.mp4",
            prompt="Describe el video",
        )

        self.assertEqual(result.generation.content, "análisis de prueba")
        self.assertEqual(result.frames_analyzed, 2)
        self.assertEqual(result.transcript, "transcripción de prueba")
        self.assertEqual(result.transcript_status, "completed")
        self.assertEqual(fake_transcriber.last_content, b"audio-bytes")
        self.assertEqual(fake_transcriber.last_filename, "video-audio.mp3")

    async def test_analyzes_video_without_transcript(self) -> None:
        processor = FakeVideoProcessor(audio_mp3=None)
        fake_vision = FakeVisionProvider()
        service = VideoAnalysisService(
            processor=processor,
            vision_provider=fake_vision,
            transcriber=FakeTranscriptionProvider(),
        )

        result = await service.analyze(
            content=b"video-bytes",
            filename="test.mp4",
            prompt="Describe",
            include_transcript=False,
        )

        self.assertEqual(result.transcript_status, "disabled")
        self.assertIsNone(result.transcript)

    async def test_analyzes_video_no_audio_track(self) -> None:
        processor = FakeVideoProcessor(audio_mp3=None)
        fake_vision = FakeVisionProvider()
        service = VideoAnalysisService(
            processor=processor,
            vision_provider=fake_vision,
            transcriber=FakeTranscriptionProvider(),
        )

        result = await service.analyze(
            content=b"video-bytes",
            filename="test.mp4",
            prompt="Describe",
            include_transcript=True,
        )

        self.assertEqual(result.transcript_status, "no_audio_track")
        self.assertIsNone(result.transcript)

    async def test_rejects_empty_prompt(self) -> None:
        processor = FakeVideoProcessor(audio_mp3=None)
        service = VideoAnalysisService(
            processor=processor,
            vision_provider=FakeVisionProvider(),
            transcriber=FakeTranscriptionProvider(),
        )

        with self.assertRaises(MediaInputError):
            await service.analyze(
                content=b"video-bytes",
                filename="test.mp4",
                prompt="   ",
            )


if __name__ == "__main__":
    unittest.main()
