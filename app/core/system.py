"""Rutas generales que no pertenecen a una versión concreta de la API."""

from fastapi import APIRouter, Request

router = APIRouter(tags=["system"])

@router.get(
    "/",
    summary="Presentación de la API",
    description="Confirma que la aplicación está ejecutándose.",
)
def read_root(request: Request) -> dict[str, str]:
    """Devuelve información básica de la API sin importar el módulo principal."""
    return {
        "message": "FastAPI AI Integration Basic está funcionando.",
        "status": "ok",
        "version": request.app.version,
    }


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/v1/modules")
async def list_modules(request: Request) -> list[dict[str, str]]:
    """Qué módulos están activos en esta instancia."""
    return [
        {"name": s.name, "version": s.version, "description": s.description}
        for s in request.app.state.modules.values()
    ]