"""Contrato de persistencia de productos.

El servicio depende de este protocolo, no de una implementación concreta. Una
futura implementación SQL puede reemplazar el repositorio en el punto de
composición sin cambiar rutas ni lógica de negocio.
"""

from typing import Protocol

from app.domain.models import Product, ProductDraft


class ProductRepository(Protocol):
    """Operaciones de persistencia que necesita ProductService."""

    def create(self, draft: ProductDraft) -> Product: ...

    def list_all(self) -> list[Product]: ...

    def get_by_id(self, product_id: int) -> Product | None: ...

    def update(self, product_id: int, draft: ProductDraft) -> Product | None: ...

    def delete(self, product_id: int) -> bool: ...
