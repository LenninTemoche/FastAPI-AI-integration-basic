"""Endpoints HTTP para transcripción de audio y análisis de videos subidos."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.core.config import Settings, get_settings
from app.core.schemas import ErrorResponse
from app.modules.media.schemas import MediaTranscriptionResponse, VideoAnalysisResponse
from app.modules.llm.schemas import LLMUsageResponse
from app.modules.media.service import AudioTranscriptionService, VideoAnalysisService
from app.modules.media.ports import (
    MediaInputError,
    MediaPayloadTooLargeError,
    UnsupportedMediaTypeError,
)
from .deps import get_audio_transcription_service, get_video_analysis_service

router = APIRouter(tags=["Audio y video"])

AUDIO_MIME_TYPES = {
    ".flac": "audio/flac",
    ".mp3": "audio/mpeg",
    ".mp4": "video/mp4",
    ".mpeg": "audio/mpeg",
    ".mpga": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".wav": "audio/wav",
    ".webm": "audio/webm",
}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi"}
MEDIA_ERROR_RESPONSES = {
    status.HTTP_413_CONTENT_TOO_LARGE: {"model": ErrorResponse, "description": "El archivo excede el límite local."},
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {"model": ErrorResponse, "description": "Extensión o modalidad no admitida."},
    status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse, "description": "Archivo vacío, dañado o no decodificable."},
    status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponse, "description": "Fallo del proveedor externo."},
    status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse, "description": "Capacidad o proveedor no configurado/disponible."},
    status.HTTP_504_GATEWAY_TIMEOUT: {"model": ErrorResponse, "description": "Timeout de proveedor externo o del procesamiento local."},
}


def _extension(filename: str | None) -> str:
    return Path(Path(filename or "").name).suffix.lower()


async def _read_limited(file: UploadFile, maximum_bytes: int) -> bytes:
    data = await file.read(maximum_bytes + 1)
    await file.close()
    if not data:
        raise MediaInputError("El archivo está vacío.")
    if len(data) > maximum_bytes:
        raise MediaPayloadTooLargeError("El archivo excede el tamaño máximo permitido.")
    return data


@router.post(
    "/transcriptions",
    response_model=MediaTranscriptionResponse,
    summary="Transcribir audio a texto",
    description=(
        "Recibe un archivo multipart/form-data y devuelve texto normalizado. "
        "La clave del proveedor permanece en el servidor. La transcripción de MP4 "
        "depende de que el contenedor incluya audio y el proveedor lo admita."
    ),
    responses=MEDIA_ERROR_RESPONSES,
)
async def transcribe_audio(
    service: Annotated[AudioTranscriptionService, Depends(get_audio_transcription_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    file: Annotated[UploadFile, File(description="Archivo de audio admitido; límite configurable.")],
    language: Annotated[str | None, Form(max_length=32, description="Código de idioma opcional, p. ej. es.")] = None,
) -> MediaTranscriptionResponse:
    suffix = _extension(file.filename)
    if suffix not in AUDIO_MIME_TYPES:
        await file.close()
        raise UnsupportedMediaTypeError("Formato de audio no admitido.")
    content = await _read_limited(file, settings.media_max_audio_mb * 1024 * 1024)
    result = await service.transcribe(
        content=content,
        filename=f"upload{suffix}",
        content_type=AUDIO_MIME_TYPES[suffix],
        language=language,
    )
    return MediaTranscriptionResponse(
        text=result.text,
        provider=result.provider,
        model=result.model,
    )


@router.post(
    "/videos/analyze",
    response_model=VideoAnalysisResponse,
    summary="Analizar un video mediante fotogramas y transcripción opcional",
    description=(
        "Extrae hasta el número máximo configurado de fotogramas del video. "
        "Si include_transcript=true y hay audio, intenta transcribirlo con el modelo "
        "MEDIA_TRANSCRIPTION_MODEL. El modelo de visión debe admitir image_url en Chat Completions."
    ),
    responses=MEDIA_ERROR_RESPONSES,
)
async def analyze_video(
    service: Annotated[VideoAnalysisService, Depends(get_video_analysis_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    file: Annotated[UploadFile, File(description="Archivo de video. Solo se analiza una duración inicial acotada.")],
    prompt: Annotated[str, Form(min_length=1, max_length=4000, description="Pregunta o instrucción sobre el video.")],
    system_prompt: Annotated[str | None, Form(max_length=2000)] = None,
    include_transcript: Annotated[bool, Form(description="Intenta transcribir la pista de audio si está disponible.")] = True,
) -> VideoAnalysisResponse:
    suffix = _extension(file.filename)
    if suffix not in VIDEO_EXTENSIONS:
        await file.close()
        raise UnsupportedMediaTypeError("Formato de video no admitido.")
    content = await _read_limited(file, settings.media_max_video_mb * 1024 * 1024)
    result = await service.analyze(
        content=content,
        filename=f"upload{suffix}",
        prompt=prompt,
        system_prompt=system_prompt,
        include_transcript=include_transcript,
    )
    generation = result.generation
    return VideoAnalysisResponse(
        analysis=generation.content,
        provider=generation.provider,
        model=generation.model,
        frames_analyzed=result.frames_analyzed,
        transcript=result.transcript,
        transcript_status=result.transcript_status,
        usage=LLMUsageResponse(
            input_tokens=generation.input_tokens,
            output_tokens=generation.output_tokens,
        ),
    )