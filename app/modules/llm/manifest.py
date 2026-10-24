"""Manifiesto del módulo LLM."""

from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Callable

import httpx
from app.core.module import ModuleSpec
from app.core.config import get_settings

from .errors import register_errors
from .router import router


@asynccontextmanager
async def _llm_lifespan(app) -> AbstractAsyncContextManager[None]:
    """Crea y cierra el cliente HTTP compartido para módulos llm y media."""
    settings = get_settings()
    from contextlib import AsyncExitStack
    async with AsyncExitStack() as stack:
        http_client = httpx.AsyncClient(timeout=settings.llm_timeout_seconds)
        await stack.enter_async_context(http_client)
        # Contrato explícito: cliente HTTP compartido en app.state.http_client
        app.state.http_client = http_client
        yield


spec = ModuleSpec(
    name="llm",
    description="Generación de texto con proveedor LLM configurable (local o API key)",
    router=router,
    register=register_errors,
    lifespan=_llm_lifespan,
)