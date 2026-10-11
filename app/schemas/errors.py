"""Esquemas públicos para respuestas de error HTTP documentadas."""

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    """Formato de error para errores HTTP controlados por la aplicación.

    FastAPI usa este formato por defecto para HTTPException cuando el valor de
    ``detail`` es una cadena. La clase permite documentar el contrato en OpenAPI.
    """

    model_config = ConfigDict(extra="forbid")

    detail: str = Field(
        min_length=1,
        description="Mensaje breve que describe el error sin revelar información interna.",
        examples=["Product with id 999999 not found"],
    )
