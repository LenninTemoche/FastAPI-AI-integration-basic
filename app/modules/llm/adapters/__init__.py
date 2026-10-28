"""Fábrica de proveedores LLM seleccionable por configuración."""

from app.core.config import Settings
from app.modules.llm.ports import LLMProvider, LLMNotConfiguredError
from .openai_compatible import OpenAICompatibleChatProvider
import httpx


def _openai_compatible(settings: Settings, client: httpx.AsyncClient) -> LLMProvider:
    return OpenAICompatibleChatProvider(settings=settings, client=client)


_PROVIDERS = {
    "openai_compatible": _openai_compatible,
    # "anthropic": _anthropic,     # Futuro: un archivo + una línea
}


def build_provider(settings: Settings, client: httpx.AsyncClient) -> LLMProvider:
    # Normalizar: strip + lower para aceptar mayúsculas, espacios, etc.
    provider_key = settings.llm_provider.strip().lower()
    factory = _PROVIDERS.get(provider_key)
    if factory is None:
        raise LLMNotConfiguredError(
            f"Proveedor LLM desconocido: {settings.llm_provider}"
        )
    return factory(settings, client)