"""Punto de entrada de la API REST reutilizable.
El CRUD utiliza almacenamiento en memoria únicamente para fines didácticos.
Los datos se pierden al reiniciar el proceso. La persistencia real se abordará
cuando se incorpore una base de datos y un repositorio apropiado.
"""

from typing import Annotated
from fastapi import FastAPI, Path, Query, HTTPException, Response, status
from app.schemas.product import ProductCreate, ProductListResponse, ProductRead
from app.schemas.errors import ErrorResponse

app = FastAPI(
    title="FastAPI AI Integration Basic",
    description=(
        "API REST reutilizable para aprender e integrar servicios HTTP/JSON "
        "en aplicaciones web, móviles, análisis de datos, Machine Learning e IA."
    ),
    version="0.1.0",
)

# Almacenamiento temporal en memoria. No es persistente ni compartido
_products: dict[int, ProductRead] = {}
_next_product_id = 1


# Mantiene el contrato de los errores 404 visible en Swagger/OpenAPI.
# La respuesta de ejecución sigue usando el manejador HTTPException estándar.
PRODUCT_NOT_FOUND_RESPONSE = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "El producto solicitado no existe.",
    }
}

def _get_product_or_404(product_id: int) -> ProductRead:
    """Obtiene un producto o lanza un 404 si el ID no existe.
    """
    product = _products.get(product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )
    return product


@app.get(
    "/",
    tags=["Inicio"],
    summary="Presentación de la API",
    description=("Confirma que la aplicación está ejecutándose y devuelve información básica."),
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
        "Valida los campos mediante ProductCreate y asigna un ID incremental. "
        "El producto queda guardado solo en memoria y se pierde al reiniciar la API."
    ),
)
def create_product(product: ProductCreate) -> ProductRead:
    """Crea un producto en el almacén temporal en memoria."""
    global _next_product_id

    created_product = ProductRead(id=_next_product_id, **product.model_dump())
    _products[created_product.id] = created_product
    _next_product_id += 1
    return created_product


@app.get(
    "/api/v1/products",
    response_model=ProductListResponse,
    response_model_exclude_unset=True,
    tags=["Productos"],
    summary="Listar productos",
    description=(
        "Devuelve productos ordenados por ID, con paginación mediante skip y limit. "
        "include_desc=false omite el campo description en cada elemento del listado."
    ),
)
def list_products(
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
    """Lista productos con paginación y opción de incluir las descripciones."""
    products = list(_products.values())
    page = products[skip : skip + limit]

    if include_desc:
        items = [product.model_dump() for product in page]
    else:
        items = [product.model_dump(exclude={"description"}) for product in page]

    return {
        "total": len(products),
        "skip": skip,
        "limit": limit,
        "items": items,
    }


@app.get(
    "/api/v1/products/{product_id}",
    response_model=ProductRead,
    tags=["Productos"],
    summary="Consultar un producto",
    description="Devuelve el producto identificado por su ID o un 404 si no existe.",
    responses=PRODUCT_NOT_FOUND_RESPONSE,
)

def read_product(
    product_id: Annotated[
        int,
        Path(ge=1, description="Identificador entero positivo del producto."),
    ],
) -> ProductRead:
    """Recupera un producto por ID."""
    return _get_product_or_404(product_id)


@app.put(
    "/api/v1/products/{product_id}",
    response_model=ProductRead,
    tags=["Productos"],
    summary="Actualizar un producto",
    description=(
        "Reemplaza los campos editables del producto. Debe enviarse un ProductCreate "
        "completo; si se omite description, vuelve a null. Devuelve 404 si no existe."
    ),
    responses=PRODUCT_NOT_FOUND_RESPONSE,
)

def update_product(
    product_id: Annotated[
        int,
        Path(ge=1, description="Identificador entero positivo del producto."),
    ],
    product: ProductCreate,
) -> ProductRead:
    """Reemplaza los campos editables de un producto existente (PUT)."""
    _get_product_or_404(product_id)
    updated_product = ProductRead(id=product_id, **product.model_dump())
    _products[product_id] = updated_product
    return updated_product


@app.delete(
    "/api/v1/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
    tags=["Productos"],
    summary="Eliminar un producto",
    description=(
        "Elimina el producto indicado. Devuelve 204 sin cuerpo si se eliminó, "
        "o 404 si no existe."
    ),
    responses=PRODUCT_NOT_FOUND_RESPONSE,
)

def delete_product(
    product_id: Annotated[
        int,
        Path(ge=1, description="Identificador entero positivo del producto."),
    ],
) -> Response:
    """Elimina un producto existente y devuelve 204 No Content."""
    _get_product_or_404(product_id)
    del _products[product_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)
