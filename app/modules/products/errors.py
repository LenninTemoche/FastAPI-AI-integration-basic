"""Manejadores de errores para el módulo Products."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.schemas import ErrorResponse
from app.modules.products.exceptions import ProductNotFoundError


def _json_error(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(detail=detail).model_dump(),
    )


async def product_not_found_exception_handler(
    request: Request,
    exc: ProductNotFoundError,
) -> JSONResponse:
    del request
    return _json_error(status.HTTP_404_NOT_FOUND, str(exc))


def register_errors(app: FastAPI) -> None:
    app.add_exception_handler(ProductNotFoundError, product_not_found_exception_handler)