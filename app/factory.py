"""Fábrica de la aplicación FastAPI.

Este módulo contiene la función `create_app` para crear la aplicación.
Separar la fábrica permite importar sin instanciar la app (útil para tests
y instalaciones mínimas sin arrancar lifespan).
"""

from contextlib import AsyncExitStack, asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI

from app.core import system
from app.core.config import get_settings
from app.core.registry import install_modules


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        for spec in app.state.modules.values():
            if spec.lifespan:
                await stack.enter_async_context(spec.lifespan(app))
        yield


def create_app(enabled: Optional[List[str]] = None) -> FastAPI:
    """
    Crea la aplicación FastAPI.

    Args:
        enabled: Lista de módulos a habilitar. Si es None, usa ENABLED_MODULES
                 del entorno (por defecto: "llm,media,products").

    Returns:
        Instancia de FastAPI configurada con los módulos habilitados.
    """
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.factory:create_app", host="0.0.0.0", port=8000, reload=True)