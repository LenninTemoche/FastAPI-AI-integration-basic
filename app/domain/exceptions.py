"""Excepciones del dominio independientes de FastAPI y del transporte HTTP."""


class ProductNotFoundError(Exception):
    """Indica que el producto solicitado no existe en el repositorio."""

    def __init__(self, product_id: int) -> None:
        self.product_id = product_id
        super().__init__(f"Product with id {product_id} not found")
