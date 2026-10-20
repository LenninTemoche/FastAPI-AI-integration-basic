"""Puertos y resultados neutrales para capacidades de audio y video.

Estos contratos no dependen de FastAPI, HTTPX, FFmpeg ni un proveedor concreto.
"""

from dataclasses import dataclass
from typing import Literal, Protocol

from app.services.ports.llm_provider import LLMGenerationResult


TranscriptStatus = Literal[
    "completed", "no_audio_track", "not_configured", "no_speech_detected", "disabled"
]


@dataclass(frozen=True, slots=True)
class MediaTranscriptionResult:
    provider: str
    model: str
    text: str


@dataclass(frozen=True, slots=True)
class ExtractedVideoMedia:
    """Fotogramas JPEG muestreados y pista de audio MP3 opcional."""
    frames: tuple[bytes, ...]
    audio_mp3: bytes | None
    frame_interval_seconds: int


@dataclass(frozen=True, slots=True)
class VideoAnalysisResult:
    generation: LLMGenerationResult
    frames_analyzed: int
    transcript: str | None
    transcript_status: TranscriptStatus


class AudioTranscriptionProvider(Protocol):
    async def transcribe(
        self,
        *,
        content: bytes,
        filename: str,
        content_type: str,
        language: str | None = None,
    ) -> MediaTranscriptionResult:
        """Devuelve una transcripción normalizada de un archivo de audio."""
        ...


class VideoVisionProvider(Protocol):
    async def analyze_frames(
        self,
        *,
        frames: tuple[bytes, ...],
        prompt: str,
        system_prompt: str | None,
        frame_interval_seconds: int,
        transcript: str | None = None,
    ) -> LLMGenerationResult:
        """Analiza una secuencia limitada de fotogramas de un video."""
        ...


class VideoProcessor(Protocol):
    async def extract(
        self,
        *,
        content: bytes,
        filename: str,
        include_audio: bool,
    ) -> ExtractedVideoMedia:
        """Extrae fotogramas y, opcionalmente, audio de un contenedor de video."""
        ...


class MediaInputError(Exception):
    """El archivo está vacío, corrupto o no puede interpretarse como medio válido."""


class UnsupportedMediaTypeError(Exception):
    """La extensión o modalidad de archivo no está admitida por el endpoint."""


class MediaPayloadTooLargeError(Exception):
    """El archivo excede el límite local de carga configurado."""


class MediaProcessorUnavailableError(Exception):
    """No está disponible el ejecutable o recurso de procesamiento multimedia."""


class MediaProcessingTimeoutError(Exception):
    """El procesamiento local excedió el timeout configurado."""
