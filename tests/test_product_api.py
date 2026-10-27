"""Pruebas automatizadas de la API de productos (sección 5 — CRUD).

Ejecutar:
    python -m pytest tests/test_product_api.py -q
o, sin pytest:
    python tests/test_product_api.py

Usan ``fastapi.testclient.TestClient`` (basado en httpx, ya instalado en el
entorno), por lo que no requieren el servidor levantado ni dependencias nuevas.
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from app.factory import create_app  # noqa: E402
from app.modules.products.deps import get_product_service  # noqa: E402
from app.modules.products.in_memory_repository import InMemoryProductRepository  # noqa: E402
from app.modules.products.service import ProductService  # noqa: E402


def _reset_state(app) -> None:
    """Reinicia el almacenamiento en memoria entre pruebas."""
    repo = InMemoryProductRepository()
    service = ProductService(repo)
    app.dependency_overrides[get_product_service] = lambda: service


def _client() -> TestClient:
    app = create_app(enabled=["products"])
    _reset_state(app)
    return TestClient(app)


class ProductApiTests(unittest.TestCase):
    """Pruebas del contrato CRUD de productos."""

    def setUp(self) -> None:
        self.client = _client()

    def tearDown(self) -> None:
        self.client.close()

    def test_read_root(self) -> None:
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "ok")
        self.assertIn("FastAPI AI Integration Basic", body["message"])

    def test_create_product_success(self) -> None:
        payload = {"name": "Router Wi-Fi", "price": 129.90, "stock": 15}
        r = self.client.post("/api/v1/products", json=payload)
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertEqual(body["id"], 1)
        self.assertEqual(body["name"], "Router Wi-Fi")
        self.assertEqual(body["price"], 129.90)
        self.assertEqual(body["stock"], 15)
        self.assertIsNone(body["description"])

    def test_create_product_validation_error(self) -> None:
        r = self.client.post(
            "/api/v1/products",
            json={"name": "Router", "price": 0, "stock": 0},
        )
        self.assertEqual(r.status_code, 422)
        errors = r.json()["detail"]
        self.assertTrue(any(err["loc"] == ["body", "price"] for err in errors))

    def test_get_product_not_found(self) -> None:
        r = self.client.get("/api/v1/products/999")
        self.assertEqual(r.status_code, 404)

    def test_get_and_list_products(self) -> None:
        self.client.post(
            "/api/v1/products",
            json={"name": "Router Wi-Fi", "price": 129.90, "stock": 15},
        )
        self.client.post(
            "/api/v1/products",
            json={"name": "Switch 8 puertos", "price": 79.50, "stock": 8},
        )

        r = self.client.get("/api/v1/products/1")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["name"], "Router Wi-Fi")

        r = self.client.get("/api/v1/products", params={"skip": 0, "limit": 1})
        self.assertEqual(r.status_code, 200)
        listing = r.json()
        self.assertEqual(listing["total"], 2)
        self.assertEqual(len(listing["items"]), 1)
        self.assertEqual(listing["items"][0]["name"], "Router Wi-Fi")

    def test_update_product(self) -> None:
        self.client.post(
            "/api/v1/products",
            json={"name": "Router Wi-Fi", "price": 129.90, "stock": 15},
        )
        r = self.client.put(
            "/api/v1/products/1",
            json={"name": "Router Wi-Fi 6", "price": 199.90, "stock": 5},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["id"], 1)
        self.assertEqual(body["name"], "Router Wi-Fi 6")
        self.assertEqual(body["price"], 199.90)
        self.assertEqual(body["stock"], 5)

    def test_delete_product(self) -> None:
        self.client.post(
            "/api/v1/products",
            json={"name": "Router Wi-Fi", "price": 129.90, "stock": 15},
        )
        r = self.client.delete("/api/v1/products/1")
        self.assertEqual(r.status_code, 204)

        r = self.client.get("/api/v1/products/1")
        self.assertEqual(r.status_code, 404)

    def test_validate_endpoint_removed(self) -> None:
        """El endpoint didáctico /validate se retiró al implementar el CRUD."""
        r = self.client.post(
            "/api/v1/products/validate",
            json={"name": "Router Wi-Fi", "price": 129.90, "stock": 15},
        )
        self.assertIn(r.status_code, (404, 405))

    def test_404_detail_format(self) -> None:
        """Un 404 de producto inexistente devuelve {detail} sin datos internos."""
        r = self.client.get("/api/v1/products/999999")
        self.assertEqual(r.status_code, 404)
        body = r.json()
        self.assertIn("detail", body)
        self.assertIsInstance(body["detail"], str)
        self.assertTrue(body["detail"])
        self.assertIn("999999", body["detail"])

    def test_404_documented_as_error_response(self) -> None:
        """OpenAPI documenta ErrorResponse para el 404 de GET/PUT/DELETE por ID."""
        spec = self.client.get("/openapi.json").json()
        path = spec["paths"]["/api/v1/products/{product_id}"]
        for method in ("get", "put", "delete"):
            responses = path[method]["responses"]
            self.assertIn("404", responses)
            schema = (
                responses["404"]
                .get("content", {})
                .get("application/json", {})
                .get("schema", {})
            )
            self.assertEqual(schema.get("$ref"), "#/components/schemas/ErrorResponse")
        self.assertIn("ErrorResponse", spec["components"]["schemas"])


def _run_all() -> int:
    failures = 0
    tests = sorted(
        (name, obj) for name, obj in sorted(globals().items()) if name.startswith("test_") and callable(obj)
    )
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL {name}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} pruebas pasaron.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())