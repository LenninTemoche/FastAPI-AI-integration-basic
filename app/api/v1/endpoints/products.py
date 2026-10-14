"""Endpoints HTTP del recurso Product.

Este módulo adapta solicitudes/respuestas HTTP a ProductService. No contiene
reglas de persistencia ni construye directamente el almacenamiento.
"""

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.core.dependencies import get_product_service
from app.domain.models import Product, ProductDraft
from app.schemas.errors import ErrorResponse
from app.schemas.product import ProductCreate, ProductListResponse, ProductRead
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Productos"])

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
    """Mapea un payload Pydantic validado al comando de dominio."""
    return ProductDraft(**payload.model_dump())

@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un producto",
    description=(
        "Crea un recurso nuevo. Cada solicitud POST válida crea un producto "
        "con un ID nuevo, incluso si el JSON coincide con uno ya enviado; no "
        "se aplica deduplicación por igualdad de campos. Consulte la guía de "
        "idempotencia antes de implementar reintentos automáticos."
    ),
)
def create_product(
    payload: ProductCreate,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductRead:
    """Crea un producto y devuelve su representación pública."""
    return _to_product_read(service.create(_to_product_draft(payload)))

@router.get(
    "",
    response_model=ProductListResponse,
    response_model_exclude_unset=True,
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
    """Lista productos paginados conservando el contrato HTTP previo."""
    total, products = service.list_products(skip=skip, limit=limit)
    items: list[dict[str, object]] = []
    for product in products:
        item = asdict(product)
        if not include_desc:
            item.pop("description", None)
        items.append(item)
    return {"total": total, "skip": skip, "limit": limit, "items": items}

@router.get(
    "/{product_id}",
    response_model=ProductRead,
    summary="Consultar un producto",
    description=(
        "Devuelve el producto identificado por su ID. Si no existe, "
        "ProductService lanza ProductNotFoundError y el adaptador HTTP responde 404."
    ),
    responses=PRODUCT_NOT_FOUND_RESPONSE,
)
def read_product(
    product_id: Annotated[
        int, Path(ge=1, description="Identificador entero positivo del producto.")
    ],
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductRead:
    """Recupera un producto mediante la capa de servicio."""
    return _to_product_read(service.get_by_id(product_id))

@router.put(
    "/{product_id}",
    response_model=ProductRead,
    summary="Actualizar un producto",
    description=(
        "Reemplaza los campos editables; el cuerpo debe ser completo. "
        "Si el producto no existe, devuelve 404 con ErrorResponse."
    ),
    responses=PRODUCT_NOT_FOUND_RESPONSE,
)
def update_product(
    product_id: Annotated[
        int, Path(ge=1, description="Identificador entero positivo del producto.")
    ],
    payload: ProductCreate,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductRead:
    """Actualiza los campos editables y conserva el identificador."""
    updated = service.update(product_id, _to_product_draft(payload))
    return _to_product_read(updated)

@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
    summary="Eliminar un producto",
    description=(
        "Elimina un producto y devuelve 204 sin cuerpo. Si no existe, "
        "responde 404 con ErrorResponse."
    ),
    responses=PRODUCT_NOT_FOUND_RESPONSE,
)
def delete_product(
    product_id: Annotated[
        int, Path(ge=1, description="Identificador entero positivo del producto.")
    ],
    service: Annotated[ProductService, Depends(get_product_service)],
) -> Response:
    """Elimina un producto existente sin devolver contenido."""
    service.delete(product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
