"""Punto de entrada de la API REST reutilizable."""

from typing import Annotated
from fastapi import FastAPI, Path, Query
from app.schemas.product import ProductCreate, ProductValidationResult

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
def list_products(
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Cantidad máxima de productos a devolver (entre 1 y 100).",
        ),
    ] = 10,
    include_desc: Annotated[
        bool,
        Query(description="Indica si se desea incluir la descripción en el listado."),
    ] = False,
) -> dict[str, object]:
    """Devuelve los parámetros query validados, sin consultar datos reales todavía."""
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
def read_product(
    product_id: Annotated[
        int,
        Path(ge=1, description="Identificador entero positivo del producto."),
    ],
) -> dict[str, object]:
    """Devuelve el identificador validado recibido como parámetro de ruta."""
    return {
        "message": (
            "Parámetro de ruta recibido. La consulta del producto real "
            "se implementará en la sección de CRUD."
        ),
        "product_id": product_id,
    }
@app.post(
    "/api/v1/products/validate",
    response_model=ProductValidationResult,
    tags=["Validación"],
    summary="Validar los datos de un producto",
    description=(
        "Endpoint didáctico para demostrar la validación del cuerpo JSON con Pydantic. "
        "No crea ni persiste productos. En la sección de CRUD se implementará "
        "POST /api/v1/products para crear recursos reales."
    ),
)
def validate_product_payload(product: ProductCreate) -> ProductValidationResult:
    """Valida y devuelve una vista previa del payload, sin guardar datos."""
    return ProductValidationResult(
        valid=True,
        message=(
            "El payload cumple las reglas de validación. No se ha creado "
            "ni almacenado un producto."
        ),
        product=product,
    )


