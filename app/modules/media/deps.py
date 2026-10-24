"""Inyección de dependencias para el módulo Media."""

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.modules.llm.adapters import build_provider
from app.modules.llm.ports import LLMProvider, LLMNotConfiguredError
from app.modules.media.adapters import FFmpegVideoProcessor
from app.modules.media.adapters.openai_audio import OpenAICompatibleAudioTranscriber
from app.modules.media.adapters.openai_vision import OpenAICompatibleVisionProvider
from app.modules.media.service import AudioTranscriptionService, VideoAnalysisService
import httpx


def get_llm_provider(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> LLMProvider:
    client = getattr(request.app.state, "http_client", None)
    if client is None:
        raise LLMNotConfiguredError
    return build_provider(settings, client)


def get_audio_transcription_service(
    request: Request,
    provider: LLMProvider = Depends(get_llm_provider),
) -> AudioTranscriptionService:
    settings = get_settings()
    client = getattr(request.app.state, "http_client", None)
    if client is None:
        raise LLMNotConfiguredError
    transcriber = OpenAICompatibleAudioTranscriber(settings=settings, client=client)
    return AudioTranscriptionService(transcriber)


def get_video_analysis_service(
    request: Request,
    provider: LLMProvider = Depends(get_llm_provider),
) -> VideoAnalysisService:
    settings = get_settings()
    client = getattr(request.app.state, "http_client", None)
    if client is None:
        raise LLMNotConfiguredError
    processor = FFmpegVideoProcessor(settings)
    vision_provider = OpenAICompatibleVisionProvider(settings=settings, client=client)
    transcriber = OpenAICompatibleAudioTranscriber(settings=settings, client=client)
    return VideoAnalysisService(
        processor=processor,
        vision_provider=vision_provider,
        transcriber=transcriber,
    )