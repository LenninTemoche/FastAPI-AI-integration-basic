"""Esquemas públicos para respuestas de error HTTP documentadas."""

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    """Contrato estable para errores HTTP controlados por la API."""

    model_config = ConfigDict(extra="forbid")

    detail: str = Field(
        min_length=1,
        description="Mensaje breve que describe el error sin revelar información interna.",
        examples=["Product with id 999999 not found"],
    )
