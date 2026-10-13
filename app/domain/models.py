"""Modelos de dominio independientes de FastAPI y Pydantic."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProductDraft:
    """Datos de producto validados que se entregan al servicio."""

    name: str
    price: float
    stock: int
    description: str | None = None


@dataclass(frozen=True, slots=True)
class Product:
    """Entidad de dominio con identificador asignado por el repositorio."""

    id: int
    name: str
    price: float
    stock: int
    description: str | None = None
