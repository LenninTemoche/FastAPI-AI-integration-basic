"""Punto de composición para servicios y adaptadores de infraestructura."""

from fastapi import Request

from app.core.config import get_settings
from app.integrations.llm.openai_compatible import OpenAICompatibleChatProvider
from app.integrations.llm.openai_compatible_audio import OpenAICompatibleAudioTranscriber
from app.integrations.llm.openai_compatible_vision import OpenAICompatibleVisionProvider
from app.integrations.media.ffmpeg_video_processor import FFmpegVideoProcessor
from app.repositories.in_memory_product_repository import InMemoryProductRepository
from app.services.llm_service import LLMService
from app.services.media_service import AudioTranscriptionService, VideoAnalysisService
from app.services.ports.llm_provider import LLMNotConfiguredError
from app.services.product_service import ProductService


# La implementación por defecto es temporal y local. Para usar otra persistencia,
# se sustituye este enlace por un repositorio compatible con ProductRepository.
_product_repository = InMemoryProductRepository()
_product_service = ProductService(_product_repository)


def get_product_service() -> ProductService:
    """Proporciona el servicio de productos a los endpoints de FastAPI."""
    return _product_service

def _get_http_client(request: Request):
    client = getattr(request.app.state, "llm_http_client", None)
    if client is None:
        raise LLMNotConfiguredError
    return client

def get_llm_service(request: Request) -> LLMService:
    """Compone generación de texto con el adaptador configurado."""
    settings = get_settings()
    if settings.llm_provider != "openai_compatible":
        raise LLMNotConfiguredError
    return LLMService(OpenAICompatibleChatProvider(settings=settings, client=_get_http_client(request)))


def get_audio_transcription_service(request: Request) -> AudioTranscriptionService:
    """Compone la transcripción sin acoplarla a las rutas HTTP."""
    settings = get_settings()
    if settings.llm_provider != "openai_compatible":
        raise LLMNotConfiguredError
    provider = OpenAICompatibleAudioTranscriber(settings=settings, client=_get_http_client(request))
    return AudioTranscriptionService(provider)


def get_video_analysis_service(request: Request) -> VideoAnalysisService:
    """Compone el procesador local y los adaptadores remotos de audio/visión."""
    settings = get_settings()
    if settings.llm_provider != "openai_compatible":
        raise LLMNotConfiguredError
    client = _get_http_client(request)
    return VideoAnalysisService(
        processor=FFmpegVideoProcessor(settings),
        vision_provider=OpenAICompatibleVisionProvider(settings=settings, client=client),
        transcriber=OpenAICompatibleAudioTranscriber(settings=settings, client=client),
    )
