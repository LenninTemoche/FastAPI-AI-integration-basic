"""Pruebas de contrato HTTP y del esquema OpenAPI.

Ejecutar desde la raíz del repositorio:
    python -m unittest discover -s tests -v
"""

import unittest

from fastapi.testclient import TestClient

from app.core.dependencies import get_product_service
from app.main import app
from app.repositories.in_memory_product_repository import InMemoryProductRepository
from app.services.product_service import ProductService


class ProductHttpContractTests(unittest.TestCase):
    """Comprueba respuestas para éxito, error y validación."""

    def setUp(self) -> None:
        # Cada prueba recibe un servicio/repositorio nuevo para no depender del
        # orden de ejecución ni modificar el almacenamiento de desarrollo global.
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

    def assert_error_response(self, response, expected_status: int) -> None:
        self.assertEqual(response.status_code, expected_status)
        self.assertTrue(response.headers["content-type"].startswith("application/json"))
        body = response.json()
        self.assertEqual(set(body), {"detail"})
        self.assertIsInstance(body["detail"], str)
        self.assertTrue(body["detail"].strip())

    def test_get_missing_product_returns_documented_404(self) -> None:
        response = self.client.get("/api/v1/products/999999")
        self.assert_error_response(response, 404)
        self.assertEqual(
            response.json()["detail"],
            "Product with id 999999 not found",
        )

    def test_put_missing_product_returns_404_not_200(self) -> None:
        response = self.client.put(
            "/api/v1/products/999999",
            json=self.valid_payload(),
        )
        self.assert_error_response(response, 404)

    def test_delete_missing_product_returns_404_not_204(self) -> None:
        response = self.client.delete("/api/v1/products/999999")
        self.assert_error_response(response, 404)

    def test_successful_crud_contract_is_preserved(self) -> None:
        created = self.client.post("/api/v1/products", json=self.valid_payload())
        self.assertEqual(created.status_code, 201)
        product_id = created.json()["id"]

        read = self.client.get(f"/api/v1/products/{product_id}")
        self.assertEqual(read.status_code, 200)
        self.assertEqual(read.json()["id"], product_id)

        updated_payload = self.valid_payload() | {"name": "Router actualizado"}
        updated = self.client.put(
            f"/api/v1/products/{product_id}",
            json=updated_payload,
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["name"], "Router actualizado")

        deleted = self.client.delete(f"/api/v1/products/{product_id}")
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(deleted.content, b"")

        after_delete = self.client.get(f"/api/v1/products/{product_id}")
        self.assert_error_response(after_delete, 404)

    def test_pagination_and_optional_description_are_preserved(self) -> None:
        self.client.post("/api/v1/products", json=self.valid_payload())
        self.client.post(
            "/api/v1/products",
            json=self.valid_payload() | {"name": "Teclado mecánico"},
        )

        page = self.client.get("/api/v1/products?skip=1&limit=1")
        self.assertEqual(page.status_code, 200)
        body = page.json()
        self.assertEqual(body["total"], 2)
        self.assertEqual(body["skip"], 1)
        self.assertEqual(body["limit"], 1)
        self.assertEqual(len(body["items"]), 1)
        self.assertNotIn("description", body["items"][0])

        with_description = self.client.get(
            "/api/v1/products?include_desc=true",
        )
        self.assertIn("description", with_description.json()["items"][0])

    def test_invalid_path_and_query_parameters_keep_422(self) -> None:
        cases = (
            ("/api/v1/products/abc", "GET"),
            ("/api/v1/products/0", "GET"),
            ("/api/v1/products?limit=0", "GET"),
            ("/api/v1/products?limit=abc", "GET"),
        )
        for path, method in cases:
            with self.subTest(path=path):
                response = self.client.request(method, path)
                self.assertEqual(response.status_code, 422)
                self.assertIsInstance(response.json().get("detail"), list)

    def test_invalid_payload_keeps_422(self) -> None:
        payload = self.valid_payload() | {"name": "TV", "extra_field": True}
        response = self.client.post("/api/v1/products", json=payload)
        self.assertEqual(response.status_code, 422)
        self.assertIsInstance(response.json().get("detail"), list)

    def test_openapi_documents_error_response_for_id_operations(self) -> None:
        schema = self.client.get("/openapi.json").json()
        path = schema["paths"]["/api/v1/products/{product_id}"]
        for method in ("get", "put", "delete"):
            with self.subTest(method=method):
                response_404 = path[method]["responses"]["404"]
                self.assertEqual(
                    response_404["content"]["application/json"]["schema"]["$ref"],
                    "#/components/schemas/ErrorResponse",
                )

    def test_unknown_route_remains_standard_fastapi_404(self) -> None:
        response = self.client.get("/route-that-does-not-exist")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not Found"})


if __name__ == "__main__":
    unittest.main()
