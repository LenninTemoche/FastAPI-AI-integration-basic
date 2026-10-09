"""Punto de entrada de la API REST reutilizable."""

from fastapi import FastAPI

app = FastAPI(
    title="FastAPI AI Integration Basic",
    description=(
        "API REST reutilizable para aprender e integrar servicios HTTP/JSON "
        "en aplicaciones web, móviles, análisis de datos, Machine Learning e IA."
    ),
    version="0.1.0",
)


@app.get(
    "/",
    tags=["Inicio"],
    summary="Presentación de la API",
    description="Confirma que la aplicación está ejecutándose y devuelve información básica.",
)
def read_root() -> dict[str, str]:
    """Devuelve información básica de la API."""
    return {
        "message": "FastAPI AI Integration Basic está funcionando.",
        "status": "ok",
        "version": app.version,
    }
