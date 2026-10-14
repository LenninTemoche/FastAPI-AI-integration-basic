"""Punto de entrada HTTP de FastAPI.

Las rutas se registran desde módulos APIRouter. Este archivo no contiene
operaciones CRUD: crea la aplicación, instala los manejadores HTTP y conecta
los routers.

"""
from fastapi import FastAPI

from app.api.root import router as root_router
from app.api.v1.router import router as api_v1_router
from app.core.exception_handlers import register_exception_handlers

app = FastAPI(
    title="FastAPI AI Integration Basic",
    description=(
        "API REST reutilizable para aprender e integrar servicios HTTP/JSON "
        "en aplicaciones web, móviles, análisis de datos, Machine Learning e IA."
    ),
    version="0.1.0",
)
register_exception_handlers(app)

# Rutas generales (por ejemplo, GET /).
app.include_router(root_router)

# Todas las rutas versionadas se agrupan bajo /api/v1.
app.include_router(api_v1_router)
