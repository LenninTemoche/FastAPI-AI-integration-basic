"""Endpoints HTTP para generación de texto mediante un proveedor LLM."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_llm_service
from app.schemas.errors import ErrorResponse
from app.schemas.llm import LLMAskRequest, LLMAskResponse, LLMUsageResponse
from app.services.llm_service import LLMService

router = APIRouter(prefix="/llm", tags=["IA generativa"])

LLM_ERROR_RESPONSES = {
    status.HTTP_502_BAD_GATEWAY: {
        "model": ErrorResponse,
        "description": "El proveedor externo devolvió un error o una respuesta no compatible.",
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": ErrorResponse,
        "description": "El proveedor no está configurado o está limitado temporalmente.",
    },
    status.HTTP_504_GATEWAY_TIMEOUT: {
        "model": ErrorResponse,
        "description": "El proveedor excedió el tiempo máximo de respuesta.",
    },
}


@router.post(
    "/ask",
    response_model=LLMAskResponse,
    status_code=status.HTTP_200_OK,
    summary="Enviar una pregunta a un LLM",
    description=(
        "Realiza una única generación de texto a través del adaptador configurado. "
        "La API key permanece en el servidor. No se conserva historial de conversación."
    ),
    responses=LLM_ERROR_RESPONSES,
)
async def ask_llm(
    payload: LLMAskRequest,
    service: Annotated[LLMService, Depends(get_llm_service)],
) -> LLMAskResponse:
    """Valida el contrato HTTP, llama al servicio y normaliza la respuesta."""
    result = await service.ask(
        prompt=payload.prompt,
        system_prompt=payload.system_prompt,
    )
    return LLMAskResponse(
        response=result.content,
        provider=result.provider,
        model=result.model,
        usage=LLMUsageResponse(
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        ),
    )
