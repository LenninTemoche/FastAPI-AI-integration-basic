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
    try:
        return _PROVIDERS[settings.llm_provider](settings, client)
    except KeyError as exc:
        raise LLMNotConfiguredError(
            f"Proveedor LLM desconocido: {settings.llm_provider}"
        ) from exc