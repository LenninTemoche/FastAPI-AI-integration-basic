"""Punto de composición de la aplicación FastAPI.

Las rutas se registran desde módulos APIRouter. Este archivo no contiene
operaciones CRUD: crea la aplicación, instala los manejadores HTTP y conecta
los routers.

"""
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI

from app.core import system
from app.core.config import get_settings
from app.core.registry import install_modules


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Los lifespans de los módulos (llm, media) gestionan sus propios recursos
    # incluido el cliente HTTP compartido creado por el módulo llm.
    async with AsyncExitStack() as stack:
        for spec in app.state.modules.values():
            if spec.lifespan:
                await stack.enter_async_context(spec.lifespan(app))
        yield


def create_app(enabled: list[str] | None = None) -> FastAPI:
    settings = get_settings()
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
    app.include_router(system.router)
    install_modules(app, enabled if enabled is not None else settings.enabled_modules_list)
    return app


app = create_app()