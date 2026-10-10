"""Esquemas Pydantic relacionados con productos.

ProductCreate se reutilizará cuando se implemente el CRUD en la sección 5.
"""

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    """Payload de entrada para un producto nuevo, validado pero aún no persistido."""

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


class ProductValidationResult(BaseModel):
    """Respuesta explícita del endpoint didáctico de validación."""

    model_config = ConfigDict(extra="forbid")

    valid: bool = Field(description="Indica si el payload pasó las reglas de validación.")
    message: str = Field(description="Aclara que esta operación no persiste el producto.")
    product: ProductCreate
