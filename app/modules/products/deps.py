"""Inyección de dependencias para el módulo Products."""

from functools import lru_cache
from fastapi import Depends

from app.modules.products.in_memory_repository import InMemoryProductRepository
from app.modules.products.repository import ProductRepository
from app.modules.products.service import ProductService


@lru_cache
def get_product_repository() -> ProductRepository:
    return InMemoryProductRepository()


def get_product_service(repo: ProductRepository = Depends(get_product_repository)) -> ProductService:
    return ProductService(repo)