"""Adaptadores que traducen excepciones de dominio a respuestas HTTP."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.domain.exceptions import ProductNotFoundError
from app.schemas.errors import ErrorResponse


async def product_not_found_exception_handler(
    request: Request,
    exc: ProductNotFoundError,
) -> JSONResponse:
    """Traduce ProductNotFoundError al contrato HTTP 404 documentado.

    Mantiene el formato compatible ``{"detail": "..."}`` y no expone trazas
    ni detalles internos. La petición no se incorpora al mensaje de error.
    """
    del request  # Forma parte de la firma requerida por Starlette.
    payload = ErrorResponse(detail=str(exc)).model_dump()
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=payload,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registra la traducción de la excepción de dominio a HTTP."""
    app.add_exception_handler(
        ProductNotFoundError,
        product_not_found_exception_handler,
    )
