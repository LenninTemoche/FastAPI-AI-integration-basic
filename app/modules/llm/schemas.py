"""Contratos HTTP/JSON para solicitudes y respuestas LLM."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class LLMAskRequest(BaseModel):
    """Petición de una generación de texto de una sola interacción."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    prompt: Annotated[
        str,
        Field(
            min_length=1,
            max_length=12_000,
            description="Instrucción o pregunta enviada al modelo (máximo 12 000 caracteres).",
        ),
    ]
    system_prompt: Annotated[
        str | None,
        Field(
            default=None,
            min_length=1,
            max_length=4_000,
            description="Instrucción de contexto opcional (máximo 4 000 caracteres).",
        ),
    ] = None


class LLMUsageResponse(BaseModel):
    """Uso de tokens si el proveedor devuelve esta información."""

    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)


class LLMAskResponse(BaseModel):
    """Respuesta estable e independiente del formato nativo del proveedor."""

    response: str = Field(min_length=1)
    provider: str
    model: str
    usage: LLMUsageResponse
