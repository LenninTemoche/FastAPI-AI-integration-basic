"""Pruebas de lógica de negocio sin cliente HTTP ni dependencia de FastAPI."""

import unittest

from app.modules.products.exceptions import ProductNotFoundError
from app.modules.products.models import ProductDraft
from app.modules.products.in_memory_repository import InMemoryProductRepository
from app.modules.products.service import ProductService


class ProductServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryProductRepository()
        self.service = ProductService(self.repository)
        self.draft = ProductDraft(
            name="Router Wi-Fi",
            price=129.9,
            stock=15,
            description="Router de doble banda",
        )

    def test_create_and_get_product(self) -> None:
        created = self.service.create(self.draft)
        self.assertEqual(created.id, 1)
        self.assertEqual(self.service.get_by_id(created.id), created)

    def test_list_returns_total_and_requested_page(self) -> None:
        self.service.create(self.draft)
        self.service.create(
            ProductDraft(name="Teclado mecánico", price=80.0, stock=5)
        )
        total, page = self.service.list_products(skip=1, limit=1)
        self.assertEqual(total, 2)
        self.assertEqual(len(page), 1)
        self.assertEqual(page[0].name, "Teclado mecánico")

    def test_update_existing_product(self) -> None:
        created = self.service.create(self.draft)
        updated_draft = ProductDraft(
            name="Router actualizado",
            price=139.9,
            stock=10,
            description=None,
        )
        updated = self.service.update(created.id, updated_draft)
        self.assertEqual(updated.id, created.id)
        self.assertEqual(updated.name, "Router actualizado")
        self.assertIsNone(updated.description)

    def test_missing_product_operations_raise_domain_exception(self) -> None:
        with self.assertRaises(ProductNotFoundError):
            self.service.get_by_id(404)
        with self.assertRaises(ProductNotFoundError):
            self.service.update(404, self.draft)
        with self.assertRaises(ProductNotFoundError):
            self.service.delete(404)

    def test_delete_existing_product(self) -> None:
        created = self.service.create(self.draft)
        self.service.delete(created.id)
        with self.assertRaises(ProductNotFoundError):
            self.service.get_by_id(created.id)


if __name__ == "__main__":
    unittest.main()
