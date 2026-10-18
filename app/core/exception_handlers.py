"""Adaptadores que traducen excepciones de dominio/servicio a errores HTTP."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.domain.exceptions import ProductNotFoundError
from app.schemas.errors import ErrorResponse
from app.services.ports.llm_provider import (
    LLMNotConfiguredError,
    LLMProviderRateLimitError,
    LLMProviderResponseError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
)

def _json_error(status_code: int, detail: str) -> JSONResponse:
    """Construye el formato de error público compartido, sin detalles internos."""
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(detail=detail).model_dump(),
    )


async def product_not_found_exception_handler(
    request: Request,
    exc: ProductNotFoundError,
) -> JSONResponse:
    """Traduce ProductNotFoundError al contrato HTTP 404 existente."""
    del request
    return _json_error(status.HTTP_404_NOT_FOUND, str(exc))


async def llm_not_configured_exception_handler(
    request: Request,
    exc: LLMNotConfiguredError,
) -> JSONResponse:
    """Responde 503 sin exponer variables ni credenciales del servidor."""
    del request, exc
    return _json_error(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "El proveedor LLM no está configurado correctamente en el servidor.",
    )


async def llm_timeout_exception_handler(
    request: Request,
    exc: LLMProviderTimeoutError,
) -> JSONResponse:
    """Traduce el timeout de un proveedor externo a HTTP 504."""
    del request, exc
    return _json_error(
        status.HTTP_504_GATEWAY_TIMEOUT,
        "El proveedor LLM no respondió dentro del tiempo límite.",
    )


async def llm_rate_limit_exception_handler(
    request: Request,
    exc: LLMProviderRateLimitError,
) -> JSONResponse:
    """Traduce límites temporales del proveedor a HTTP 503."""
    del request, exc
    return _json_error(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "El proveedor LLM está limitando temporalmente las solicitudes.",
    )


async def llm_unavailable_exception_handler(
    request: Request,
    exc: LLMProviderUnavailableError,
) -> JSONResponse:
    """Devuelve un error seguro sin pasar el cuerpo externo al consumidor."""
    del request, exc
    return _json_error(
        status.HTTP_502_BAD_GATEWAY,
        "No fue posible completar la solicitud al proveedor LLM.",
    )


async def llm_response_exception_handler(
    request: Request,
    exc: LLMProviderResponseError,
) -> JSONResponse:
    """Normaliza respuestas inesperadas del proveedor a HTTP 502."""
    del request, exc
    return _json_error(
        status.HTTP_502_BAD_GATEWAY,
        "El proveedor LLM devolvió una respuesta no compatible.",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registra las conversiones entre errores internos y contratos HTTP."""
    app.add_exception_handler(
        ProductNotFoundError,
        product_not_found_exception_handler,
    )
    app.add_exception_handler(
        LLMNotConfiguredError,
        llm_not_configured_exception_handler,
    )
    app.add_exception_handler(
        LLMProviderTimeoutError,
        llm_timeout_exception_handler,
    )
    app.add_exception_handler(
        LLMProviderRateLimitError,
        llm_rate_limit_exception_handler,
    )
    app.add_exception_handler(
        LLMProviderUnavailableError,
        llm_unavailable_exception_handler,
    )
    app.add_exception_handler(
        LLMProviderResponseError,
        llm_response_exception_handler,
    )
