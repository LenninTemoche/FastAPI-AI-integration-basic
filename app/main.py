"""Punto de composición de la aplicación FastAPI.

Las rutas se registran desde módulos APIRouter. Este archivo no contiene
operaciones CRUD: crea la aplicación, instala los manejadores HTTP y conecta
los routers.

"""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.api.root import router as root_router
from app.api.v1.router import router as api_v1_router
from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers

@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Gestiona un cliente HTTP compartido durante la vida de la aplicación."""
    settings = get_settings()
    timeout = httpx.Timeout(
        settings.llm_timeout_seconds,
        connect=min(settings.llm_timeout_seconds, 10.0),
    )
    limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)

    async with httpx.AsyncClient(
        timeout=timeout,
        limits=limits,
        follow_redirects=False,
    ) as client:
        application.state.llm_http_client = client
        try:
            yield
        finally:
            # HTTPX se cierra mediante async with al salir del lifespan.
            application.state.llm_http_client = None


app = FastAPI(
    title="FastAPI AI Integration Basic",
    description=(
        "API REST reutilizable para integrar productos y servicios de IA mediante "
        "HTTP/JSON. La capa HTTP, los casos de uso y los adaptadores externos están "
        "separados; el proveedor LLM se configura en el servidor."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

register_exception_handlers(app)

# Rutas generales (por ejemplo, GET /).
app.include_router(root_router)

# Todas las rutas versionadas se agrupan bajo /api/v1.
app.include_router(api_v1_router)
