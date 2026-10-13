"""Punto de entrada HTTP de FastAPI.

Las rutas convierten contratos Pydantic en comandos de dominio y entidades de
dominio en respuestas HTTP. La lógica se delega en ProductService; la persistencia
se abstrae tras ProductRepository. En la sección 7 se moverán las rutas a routers.
"""
from dataclasses import asdict
from typing import Annotated

from fastapi import Depends, FastAPI, Path, Query, Response, status

from app.core.dependencies import get_product_service
from app.core.exception_handlers import register_exception_handlers
from app.domain.models import Product, ProductDraft
from app.schemas.errors import ErrorResponse
from app.schemas.product import ProductCreate, ProductListResponse, ProductRead
from app.services.product_service import ProductService


app = FastAPI(
    title="FastAPI AI Integration Basic",
    description=(
        "API REST reutilizable para aprender e integrar servicios HTTP/JSON "
        "en aplicaciones web, móviles, análisis de datos, Machine Learning e IA."
    ),
    version="0.1.0",
)
register_exception_handlers(app)

# Mantiene el contrato de los errores 404 visible en Swagger/OpenAPI.
# La respuesta de ejecución sigue usando el manejador HTTPException estándar.
PRODUCT_NOT_FOUND_RESPONSE = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "El producto solicitado no existe.",
    }
}




def _to_product_read(product: Product) -> ProductRead:
    """Mapea una entidad de dominio al contrato de salida HTTP."""
    return ProductRead(**asdict(product))


def _to_product_draft(payload: ProductCreate) -> ProductDraft:
    """Mapea un payload validado al comando de dominio."""
    return ProductDraft(**payload.model_dump())


@app.get(
    "/",
    tags=["Inicio"],
    summary="Presentación de la API",
    description="Confirma que la aplicación está ejecutándose.",
)
def read_root() -> dict[str, str]:
    """Devuelve información básica de la API."""
    return {
        "message": "FastAPI AI Integration Basic está funcionando.",
        "status": "ok",
        "version": app.version,
    }


@app.post(
    "/api/v1/products",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Productos"],
    summary="Crear un producto",
    description=(
        "Valida el cuerpo con ProductCreate y delega la creación en ProductService. "
        "El repositorio predeterminado almacena los datos solo en memoria."
    ),
)
def create_product(
    payload: ProductCreate,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductRead:
    """Crea un producto y devuelve la representación pública."""
    return _to_product_read(service.create(_to_product_draft(payload)))


@app.get(
    "/api/v1/products",
    response_model=ProductListResponse,
    response_model_exclude_unset=True,
    tags=["Productos"],
    summary="Listar productos",
    description=(
        "Devuelve productos ordenados por ID, con paginación mediante skip y limit. "
        "include_desc=false omite description en cada elemento del listado."
    ),
)
def list_products(
    service: Annotated[ProductService, Depends(get_product_service)],
    skip: Annotated[
        int,
        Query(ge=0, description="Cantidad de productos que se omiten desde el inicio."),
    ] = 0,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Cantidad máxima de productos que se devuelven (1 a 100).",
        ),
    ] = 10,
    include_desc: Annotated[
        bool,
        Query(description="Si es true, incluye la descripción en cada producto."),
    ] = False,
) -> dict[str, object]:
    """Lista productos paginados, conservando el contrato HTTP anterior."""
    total, products = service.list_products(skip=skip, limit=limit)
    items: list[dict[str, object]] = []
    for product in products:
        item = asdict(product)
        if not include_desc:
            item.pop("description", None)
        items.append(item)
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@app.get(
    "/api/v1/products/{product_id}",
    response_model=ProductRead,
    tags=["Productos"],
    summary="Consultar un producto",
    description=(
        "Devuelve el producto identificado por su ID. Si no existe, ProductService "
        "lanza ProductNotFoundError y el adaptador HTTP responde 404 con ErrorResponse."
    ),
    responses=PRODUCT_NOT_FOUND_RESPONSE,
)
def read_product(
    product_id: Annotated[
        int,
        Path(ge=1, description="Identificador entero positivo del producto."),
    ],
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductRead:
    """Recupera un producto mediante la capa de servicio."""
    return _to_product_read(service.get_by_id(product_id))


@app.put(
    "/api/v1/products/{product_id}",
    response_model=ProductRead,
    tags=["Productos"],
    summary="Actualizar un producto",
    description=(
        "Reemplaza los campos editables; el cuerpo debe ser completo. Si el producto "
        "no existe, devuelve 404 con el esquema ErrorResponse."
    ),
    responses=PRODUCT_NOT_FOUND_RESPONSE,
)
def update_product(
    product_id: Annotated[
        int,
        Path(ge=1, description="Identificador entero positivo del producto."),
    ],
    payload: ProductCreate,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductRead:
    """Reemplaza los campos editables de un producto existente."""
    updated = service.update(product_id, _to_product_draft(payload))
    return _to_product_read(updated)


@app.delete(
    "/api/v1/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
    tags=["Productos"],
    summary="Eliminar un producto",
    description=(
        "Elimina un producto y devuelve 204 sin cuerpo. Si no existe, responde 404 "
        "con el esquema ErrorResponse."
    ),
    responses=PRODUCT_NOT_FOUND_RESPONSE,
)
def delete_product(
    product_id: Annotated[
        int,
        Path(ge=1, description="Identificador entero positivo del producto."),
    ],
    service: Annotated[ProductService, Depends(get_product_service)],
) -> Response:
    """Elimina un producto existente sin devolver contenido."""
    service.delete(product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
