"""Rutas generales que no pertenecen a una versión concreta de la API."""

from fastapi import APIRouter, Request

router = APIRouter(tags=["Inicio"])

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
