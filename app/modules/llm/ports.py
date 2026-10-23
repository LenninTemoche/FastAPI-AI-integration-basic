"""Contrato del proveedor LLM; no depende de FastAPI ni de HTTPX."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class LLMGenerationResult:
    """Resultado neutral de una generación de texto."""

    provider: str
    model: str
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class LLMError(Exception):
    """Error base de integración LLM, independiente del transporte HTTP."""


class LLMNotConfiguredError(LLMError):
    """No se han configurado los datos mínimos para llamar al proveedor."""


class LLMProviderTimeoutError(LLMError):
    """El proveedor no respondió dentro del timeout configurado."""


class LLMProviderRateLimitError(LLMError):
    """El proveedor limitó temporalmente el número de solicitudes."""


class LLMProviderUnavailableError(LLMError):
    """El proveedor rechazó o no pudo procesar una solicitud."""


class LLMProviderResponseError(LLMError):
    """La respuesta del proveedor no cumple el formato esperado."""


class LLMProvider(Protocol):
    """Puerto asíncrono que implementan los adaptadores de proveedores LLM."""

    async def generate(
        self,
        *,
        prompt: str,
        system_prompt: str | None = None,
    ) -> LLMGenerationResult:
        """Genera una respuesta de texto normalizada."""
        ...
