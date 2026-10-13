"""Punto de composición para servicios y persistencia de la aplicación."""

from app.repositories.in_memory_product_repository import InMemoryProductRepository
from app.services.product_service import ProductService

# La implementación por defecto es temporal y local. Para usar otra persistencia,
# se sustituye este enlace por un repositorio compatible con ProductRepository.
_product_repository = InMemoryProductRepository()
_product_service = ProductService(_product_repository)


def get_product_service() -> ProductService:
    """Proporciona el servicio de productos a los endpoints de FastAPI."""
    return _product_service
