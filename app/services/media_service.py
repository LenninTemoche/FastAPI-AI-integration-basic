"""Casos de uso de transcripción y análisis de video, desacoplados de HTTP."""

from app.services.ports.llm_provider import LLMNotConfiguredError, LLMGenerationResult
from app.services.ports.media_provider import (
    AudioTranscriptionProvider,
    MediaInputError,
    MediaTranscriptionResult,
    TranscriptStatus,
    VideoAnalysisResult,
    VideoProcessor,
    VideoVisionProvider,
)


class AudioTranscriptionService:
    def __init__(self, provider: AudioTranscriptionProvider) -> None:
        self._provider = provider

    async def transcribe(
        self,
        *,
        content: bytes,
        filename: str,
        content_type: str,
        language: str | None = None,
    ) -> MediaTranscriptionResult:
        if not content:
            raise MediaInputError("El archivo está vacío.")
        normalized_language = language.strip() if language and language.strip() else None
        return await self._provider.transcribe(
            content=content,
            filename=filename,
            content_type=content_type,
            language=normalized_language,
        )


class VideoAnalysisService:
    def __init__(
        self,
        *,
        processor: VideoProcessor,
        vision_provider: VideoVisionProvider,
        transcriber: AudioTranscriptionProvider,
    ) -> None:
        self._processor = processor
        self._vision_provider = vision_provider
        self._transcriber = transcriber

    async def analyze(
        self,
        *,
        content: bytes,
        filename: str,
        prompt: str,
        system_prompt: str | None = None,
        include_transcript: bool = True,
    ) -> VideoAnalysisResult:
        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            raise MediaInputError("El prompt no puede estar vacío.")
        extracted = await self._processor.extract(
            content=content,
            filename=filename,
            include_audio=include_transcript,
        )
        transcript: str | None = None
        if not include_transcript:
            transcript_status: TranscriptStatus = "disabled"
        elif extracted.audio_mp3 is None:
            transcript_status = "no_audio_track"
        else:
            try:
                transcript_result = await self._transcriber.transcribe(
                    content=extracted.audio_mp3,
                    filename="video-audio.mp3",
                    content_type="audio/mpeg",
                    language=None,
                )
            except LLMNotConfiguredError:
                # El análisis visual sigue disponible aunque no se haya activado
                # la capacidad opcional de transcripción de audio.
                transcript_status = "not_configured"
            else:
                transcript = transcript_result.text.strip() or None
                transcript_status = "completed" if transcript else "no_speech_detected"

        generation: LLMGenerationResult = await self._vision_provider.analyze_frames(
            frames=extracted.frames,
            prompt=normalized_prompt,
            system_prompt=system_prompt.strip() if system_prompt and system_prompt.strip() else None,
            frame_interval_seconds=extracted.frame_interval_seconds,
            transcript=transcript,
        )
        return VideoAnalysisResult(
            generation=generation,
            frames_analyzed=len(extracted.frames),
            transcript=transcript,
            transcript_status=transcript_status,
        )
