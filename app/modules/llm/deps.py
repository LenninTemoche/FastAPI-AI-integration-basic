"""Inyección de dependencias para el módulo LLM."""

from fastapi import Depends, Request

from app.core.http import get_shared_http_client
from app.core.config import Settings, get_settings
from app.modules.llm.adapters import build_provider
from app.modules.llm.ports import LLMProvider
from app.modules.llm.service import LLMService


def get_llm_provider(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> LLMProvider:
    client = get_shared_http_client(request)
    if client is None:
        from app.modules.llm.ports import LLMNotConfiguredError
        raise LLMNotConfiguredError
    return build_provider(settings, client)


def get_llm_service(
    provider: LLMProvider = Depends(get_llm_provider),
) -> LLMService:
    return LLMService(provider)