"""Repositorio en memoria de demostración; no ofrece persistencia durable."""

from threading import Lock

from app.modules.products.models import Product, ProductDraft


class InMemoryProductRepository:
    """Implementación local sustituible por otro adaptador de persistencia.

    El bloqueo evita colisiones del contador dentro de un único proceso. El
    almacenamiento no se comparte entre varios workers o instancias y se pierde
    al reiniciar la aplicación; no debe usarse como persistencia de producción.
    """

    def __init__(self) -> None:
        self._products: dict[int, Product] = {}
        self._next_product_id = 1
        self._lock = Lock()

    def create(self, draft: ProductDraft) -> Product:
        with self._lock:
            product = Product(
                id=self._next_product_id,
                name=draft.name,
                price=draft.price,
                stock=draft.stock,
                description=draft.description,
            )
            self._products[product.id] = product
            self._next_product_id += 1
            return product

    def list_all(self) -> list[Product]:
        with self._lock:
            return sorted(self._products.values(), key=lambda product: product.id)

    def get_by_id(self, product_id: int) -> Product | None:
        with self._lock:
            return self._products.get(product_id)

    def update(self, product_id: int, draft: ProductDraft) -> Product | None:
        with self._lock:
            if product_id not in self._products:
                return None
            product = Product(
                id=product_id,
                name=draft.name,
                price=draft.price,
                stock=draft.stock,
                description=draft.description,
            )
            self._products[product_id] = product
            return product

    def delete(self, product_id: int) -> bool:
        with self._lock:
            if product_id not in self._products:
                return False
            del self._products[product_id]
            return True
