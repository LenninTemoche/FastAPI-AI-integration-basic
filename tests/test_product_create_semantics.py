"""Pruebas del contrato de creación repetida y modularización de rutas.

Ejecutar desde la raíz del repositorio:
    python -m unittest discover -s tests -v
"""

import unittest

from fastapi.testclient import TestClient

from app.api.v1.router import router as api_v1_router
from app.core.dependencies import get_product_service
from app.main import app
from app.repositories.in_memory_product_repository import InMemoryProductRepository
from app.services.product_service import ProductService


class ProductCreateSemanticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryProductRepository()
        self.service = ProductService(self.repository)
        app.dependency_overrides[get_product_service] = lambda: self.service
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.pop(get_product_service, None)
        self.client.close()

    @staticmethod
    def valid_payload() -> dict[str, object]:
        return {
            "name": "Router Wi-Fi",
            "price": 129.9,
            "stock": 15,
            "description": "Router de doble banda",
        }

    def test_identical_post_payloads_create_distinct_resources_by_default(self) -> None:
        """POST no deduplica por contenido: cada petición crea un recurso nuevo."""
        first = self.client.post("/api/v1/products", json=self.valid_payload())
        second = self.client.post("/api/v1/products", json=self.valid_payload())

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first.json()["id"], 1)
        self.assertEqual(second.json()["id"], 2)

        first_product = first.json() | {"id": None}
        second_product = second.json() | {"id": None}
        self.assertEqual(first_product, second_product)

        listing = self.client.get("/api/v1/products?include_desc=true")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.json()["total"], 2)
        self.assertEqual([item["id"] for item in listing.json()["items"]], [1, 2])

    def test_put_updates_existing_resource_without_changing_id(self) -> None:
        created = self.client.post("/api/v1/products", json=self.valid_payload())
        self.assertEqual(created.status_code, 201)
        product_id = created.json()["id"]

        updated_payload = self.valid_payload() | {"name": "Router actualizado"}
        updated = self.client.put(
            f"/api/v1/products/{product_id}", json=updated_payload
        )

        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["id"], product_id)
        self.assertEqual(updated.json()["name"], "Router actualizado")

    def test_router_registry_preserves_existing_paths(self) -> None:
        """El refactor debe conservar paths y métodos públicos existentes."""
        schema = self.client.get("/openapi.json").json()
        paths = schema["paths"]
        self.assertIn("/", paths)
        self.assertIn("/api/v1/products", paths)
        self.assertIn("/api/v1/products/{product_id}", paths)
        self.assertIn("post", paths["/api/v1/products"])
        self.assertIn("get", paths["/api/v1/products"])
        self.assertIn("get", paths["/api/v1/products/{product_id}"])
        self.assertIn("put", paths["/api/v1/products/{product_id}"])
        self.assertIn("delete", paths["/api/v1/products/{product_id}"])


if __name__ == "__main__":
    unittest.main()
