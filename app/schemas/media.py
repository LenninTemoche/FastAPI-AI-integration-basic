"""Contratos HTTP/JSON normalizados para entrada multimodal."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.llm import LLMUsageResponse


class MediaTranscriptionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(description="Transcripción textual; puede estar vacía si no se detectó voz.")
    provider: str
    model: str


MediaTranscriptStatus = Literal["completed", "no_audio_track", "not_configured", "no_speech_detected", "disabled"]


class VideoAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    analysis: str = Field(min_length=1, description="Análisis basado en fotogramas muestreados y, si está disponible, la transcripción.")
    provider: str
    model: str
    frames_analyzed: int = Field(ge=1, le=16)
    transcript: str | None = Field(default=None, description="Transcripción extraída de la pista de audio, si se habilitó y configuró.")
    transcript_status: MediaTranscriptStatus
    usage: LLMUsageResponse
