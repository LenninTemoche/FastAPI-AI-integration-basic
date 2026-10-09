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
@app.get(
    "/api/v1/products",
    tags=["Productos"],
    summary="Demostrar parámetros de consulta",
    description=(
        "Demuestra cómo se reciben parámetros query. No consulta todavía datos reales; "
        "el listado funcional se implementará en la sección de CRUD."
    ),
)
def list_products(limit: int = 10, include_desc: bool = False) -> dict[str, object]:
    """Devuelve los valores recibidos por query para demostrar su conversión de tipos."""
    return {
        "message": (
            "Parámetros de consulta recibidos. El listado real se implementará "
            "en la sección de CRUD."
        ),
        "limit": limit,
        "include_desc": include_desc,
    }


@app.get(
    "/api/v1/products/{product_id}",
    tags=["Productos"],
    summary="Demostrar un parámetro de ruta",
    description=(
        "Demuestra cómo FastAPI obtiene y convierte el identificador desde la URL. "
        "La consulta de un producto real se implementará en la sección de CRUD."
    ),
)
def read_product(product_id: int) -> dict[str, object]:
    """Devuelve el identificador recibido como parámetro de ruta."""
    return {
        "message": (
            "Parámetro de ruta recibido. La consulta del producto real "
            "se implementará en la sección de CRUD."
        ),
        "product_id": product_id,
    }
