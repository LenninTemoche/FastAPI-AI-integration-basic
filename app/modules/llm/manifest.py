"""Manifiesto del módulo LLM."""

from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Callable

import httpx
from app.core.http import HTTP_CLIENT_STATE_KEY
from app.core.module import ModuleSpec
from app.core.config import get_settings

from .errors import register_errors
from .router import router


@asynccontextmanager
async def _llm_lifespan(app) -> AbstractAsyncContextManager[None]:
    """Crea y cierra el cliente HTTP compartido para módulos llm y media."""
    settings = get_settings()
    http_client = httpx.AsyncClient(timeout=settings.llm_timeout_seconds)
    setattr(app.state, HTTP_CLIENT_STATE_KEY, http_client)
    try:
        yield
    finally:
        await http_client.aclose()


spec = ModuleSpec(
    name="llm",
    description="Generación de texto con proveedor LLM configurable (local o API key)",
    router=router,
    register=register_errors,
    lifespan=_llm_lifespan,
)