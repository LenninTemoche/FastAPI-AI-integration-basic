"""Casos de uso de productos, sin dependencia del transporte HTTP."""

from app.domain.exceptions import ProductNotFoundError
from app.domain.models import Product, ProductDraft
from app.repositories.product_repository import ProductRepository


class ProductService:
    """Orquesta operaciones de producto y aplica reglas de existencia.

    Pydantic valida la forma y los tipos del cuerpo de entrada. Este servicio
    aplica reglas de aplicación y lanza excepciones de dominio, pero no importa
    FastAPI ni construye respuestas HTTP.
    """

    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    def create(self, draft: ProductDraft) -> Product:
        return self._repository.create(draft)

    def list_products(self, skip: int, limit: int) -> tuple[int, list[Product]]:
        products = self._repository.list_all()
        return len(products), products[skip : skip + limit]

    def get_by_id(self, product_id: int) -> Product:
        product = self._repository.get_by_id(product_id)
        if product is None:
            raise ProductNotFoundError(product_id)
        return product

    def update(self, product_id: int, draft: ProductDraft) -> Product:
        product = self._repository.update(product_id, draft)
        if product is None:
            raise ProductNotFoundError(product_id)
        return product

    def delete(self, product_id: int) -> None:
        if not self._repository.delete(product_id):
            raise ProductNotFoundError(product_id)
