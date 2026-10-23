"""Manejadores de errores para el módulo LLM."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.schemas import ErrorResponse
from app.modules.llm.ports import (
    LLMNotConfiguredError,
    LLMProviderRateLimitError,
    LLMProviderResponseError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
)


def _json_error(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(detail=detail).model_dump(),
    )


async def llm_not_configured_exception_handler(
    request: Request,
    exc: LLMNotConfiguredError,
) -> JSONResponse:
    del request, exc
    return _json_error(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "El proveedor LLM no está configurado correctamente en el servidor.",
    )


async def llm_timeout_exception_handler(
    request: Request,
    exc: LLMProviderTimeoutError,
) -> JSONResponse:
    del request, exc
    return _json_error(
        status.HTTP_504_GATEWAY_TIMEOUT,
        "El proveedor LLM no respondió dentro del tiempo límite.",
    )


async def llm_rate_limit_exception_handler(
    request: Request,
    exc: LLMProviderRateLimitError,
) -> JSONResponse:
    del request, exc
    return _json_error(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "El proveedor LLM está limitando temporalmente las solicitudes.",
    )


async def llm_unavailable_exception_handler(
    request: Request,
    exc: LLMProviderUnavailableError,
) -> JSONResponse:
    del request, exc
    return _json_error(
        status.HTTP_502_BAD_GATEWAY,
        "No fue posible completar la solicitud al proveedor LLM.",
    )


async def llm_response_exception_handler(
    request: Request,
    exc: LLMProviderResponseError,
) -> JSONResponse:
    del request, exc
    return _json_error(
        status.HTTP_502_BAD_GATEWAY,
        "El proveedor LLM devolvió una respuesta no compatible.",
    )


def register_errors(app: FastAPI) -> None:
    app.add_exception_handler(LLMNotConfiguredError, llm_not_configured_exception_handler)
    app.add_exception_handler(LLMProviderTimeoutError, llm_timeout_exception_handler)
    app.add_exception_handler(LLMProviderRateLimitError, llm_rate_limit_exception_handler)
    app.add_exception_handler(LLMProviderUnavailableError, llm_unavailable_exception_handler)
    app.add_exception_handler(LLMProviderResponseError, llm_response_exception_handler)