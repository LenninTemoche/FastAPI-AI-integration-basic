"""Manejadores de errores para el módulo Media."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.schemas import ErrorResponse
from app.modules.media.ports import (
    MediaInputError,
    MediaPayloadTooLargeError,
    MediaProcessingTimeoutError,
    MediaProcessorUnavailableError,
    UnsupportedMediaTypeError,
)
from app.modules.llm.ports import LLMNotConfiguredError


def _json_error(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(detail=detail).model_dump(),
    )


async def unsupported_media_type_handler(request: Request, exc: UnsupportedMediaTypeError) -> JSONResponse:
    del request
    return _json_error(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(exc))


async def media_too_large_handler(request: Request, exc: MediaPayloadTooLargeError) -> JSONResponse:
    del request
    return _json_error(status.HTTP_413_CONTENT_TOO_LARGE, str(exc))


async def media_input_error_handler(request: Request, exc: MediaInputError) -> JSONResponse:
    del request
    return _json_error(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))


async def media_processor_unavailable_handler(request: Request, exc: MediaProcessorUnavailableError) -> JSONResponse:
    del request, exc
    return _json_error(status.HTTP_503_SERVICE_UNAVAILABLE, "El procesador multimedia no está disponible en el servidor.")


async def media_processing_timeout_handler(request: Request, exc: MediaProcessingTimeoutError) -> JSONResponse:
    del request, exc
    return _json_error(status.HTTP_504_GATEWAY_TIMEOUT, "El procesamiento multimedia excedió el tiempo máximo configurado.")


async def llm_not_configured_for_media_handler(request: Request, exc: LLMNotConfiguredError) -> JSONResponse:
    del request, exc
    return _json_error(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "El proveedor LLM no está configurado correctamente en el servidor.",
    )


def register_errors(app: FastAPI) -> None:
    app.add_exception_handler(UnsupportedMediaTypeError, unsupported_media_type_handler)
    app.add_exception_handler(MediaPayloadTooLargeError, media_too_large_handler)
    app.add_exception_handler(MediaInputError, media_input_error_handler)
    app.add_exception_handler(MediaProcessorUnavailableError, media_processor_unavailable_handler)
    app.add_exception_handler(MediaProcessingTimeoutError, media_processing_timeout_handler)
    app.add_exception_handler(LLMNotConfiguredError, llm_not_configured_for_media_handler)