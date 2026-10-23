"""Esquemas Pydantic de entrada y salida para el recurso Product.
ProductCreate se reutilizará cuando se implemente el CRUD en la sección 5.
"""

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    """Campos compartidos por los modelos de creación y lectura."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: str = Field(
        min_length=3,
        max_length=100,
        description="Nombre del producto; de 3 a 100 caracteres después de quitar espacios externos.",
        examples=["Router Wi-Fi"],
    )
    price: float = Field(
        gt=0,
        allow_inf_nan=False,
        description="Precio numérico mayor que cero; no admite NaN ni infinitos.",
        examples=[129.90],
    )
    stock: int = Field(
        ge=0,
        description="Unidades disponibles; debe ser cero o un entero positivo.",
        examples=[15],
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Descripción opcional de hasta 500 caracteres.",
        examples=["Router de doble banda"],
    )

class ProductCreate(ProductBase):
    """Cuerpo de entrada para crear o reemplazar los campos de un producto."""


class ProductRead(ProductBase):
    """Representación pública de un producto, incluyendo su identificador."""

    id: int = Field(
        gt=0,
        description="Identificador asignado por la API al crear el producto.",
        examples=[1],
    )


class ProductListResponse(BaseModel):
    """Respuesta paginada del listado de productos."""

    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0, description="Cantidad total de productos disponibles.")
    skip: int = Field(ge=0, description="Cantidad de elementos omitidos.")
    limit: int = Field(ge=1, le=100, description="Máximo de elementos solicitado.")
    items: list[ProductRead] = Field(description="Productos de la página actual.")


class ProductValidationResult(BaseModel):
    """Respuesta explícita del endpoint didáctico de validación."""

    model_config = ConfigDict(extra="forbid")

    valid: bool = Field(description="Indica si el payload pasó las reglas de validación.")
    message: str = Field(description="Aclara que esta operación no persiste el producto.")
    product: ProductCreate
