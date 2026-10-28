"""Manifiesto del módulo Media."""

from contextlib import AbstractAsyncContextManager, asynccontextmanager
from app.core.http import HTTP_CLIENT_STATE_KEY
from app.core.module import ModuleSpec

from .errors import register_errors
from .router import router


@asynccontextmanager
async def _media_lifespan(app) -> AbstractAsyncContextManager[None]:
    """El módulo media usa el cliente HTTP compartido del módulo llm (requires=llm)."""
    # Verificar que el cliente compartido existe
    if not hasattr(app.state, HTTP_CLIENT_STATE_KEY):
        raise RuntimeError("El módulo media requiere el cliente HTTP del módulo llm")
    yield


spec = ModuleSpec(
    name="media",
    description="Transcripción de audio y análisis de video por fotogramas",
    router=router,
    register=register_errors,
    requires=("llm",),
    lifespan=_media_lifespan,
)