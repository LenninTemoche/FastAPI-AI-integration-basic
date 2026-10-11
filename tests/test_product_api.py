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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

import app.main as main  # noqa: E402
from app.main import app  # noqa: E402


def _reset_state() -> None:
    """Reinicia el almacenamiento en memoria entre pruebas."""
    main._products.clear()
    main._next_product_id = 1


def _client() -> TestClient:
    _reset_state()
    return TestClient(app)


def test_read_root() -> None:
    client = _client()
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "FastAPI AI Integration Basic" in body["message"]


def test_create_product_success() -> None:
    client = _client()
    payload = {"name": "Router Wi-Fi", "price": 129.90, "stock": 15}
    r = client.post("/api/v1/products", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1
    assert body["name"] == "Router Wi-Fi"
    assert body["price"] == 129.90
    assert body["stock"] == 15
    assert body["description"] is None


def test_create_product_validation_error() -> None:
    client = _client()
    r = client.post(
        "/api/v1/products",
        json={"name": "Router", "price": 0, "stock": 0},
    )
    assert r.status_code == 422
    errors = r.json()["detail"]
    assert any(err["loc"] == ["body", "price"] for err in errors)


def test_get_product_not_found() -> None:
    client = _client()
    r = client.get("/api/v1/products/999")
    assert r.status_code == 404


def test_get_and_list_products() -> None:
    client = _client()
    client.post(
        "/api/v1/products",
        json={"name": "Router Wi-Fi", "price": 129.90, "stock": 15},
    )
    client.post(
        "/api/v1/products",
        json={"name": "Switch 8 puertos", "price": 79.50, "stock": 8},
    )

    r = client.get("/api/v1/products/1")
    assert r.status_code == 200
    assert r.json()["name"] == "Router Wi-Fi"

    r = client.get("/api/v1/products", params={"skip": 0, "limit": 1})
    assert r.status_code == 200
    listing = r.json()
    assert listing["total"] == 2
    assert len(listing["items"]) == 1
    assert listing["items"][0]["name"] == "Router Wi-Fi"


def test_update_product() -> None:
    client = _client()
    client.post(
        "/api/v1/products",
        json={"name": "Router Wi-Fi", "price": 129.90, "stock": 15},
    )
    r = client.put(
        "/api/v1/products/1",
        json={"name": "Router Wi-Fi 6", "price": 199.90, "stock": 5},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == 1
    assert body["name"] == "Router Wi-Fi 6"
    assert body["price"] == 199.90
    assert body["stock"] == 5


def test_delete_product() -> None:
    client = _client()
    client.post(
        "/api/v1/products",
        json={"name": "Router Wi-Fi", "price": 129.90, "stock": 15},
    )
    r = client.delete("/api/v1/products/1")
    assert r.status_code == 204

    r = client.get("/api/v1/products/1")
    assert r.status_code == 404


def test_validate_endpoint_removed() -> None:
    """El endpoint didáctico /validate se retiró al implementar el CRUD."""
    client = _client()
    r = client.post(
        "/api/v1/products/validate",
        json={"name": "Router Wi-Fi", "price": 129.90, "stock": 15},
    )
    assert r.status_code in (404, 405)


def test_404_detail_format() -> None:
    """Un 404 de producto inexistente devuelve {detail} sin datos internos."""
    client = _client()
    r = client.get("/api/v1/products/999999")
    assert r.status_code == 404
    body = r.json()
    assert "detail" in body
    assert isinstance(body["detail"], str) and body["detail"]
    assert "999999" in body["detail"]


def test_404_documented_as_error_response() -> None:
    """OpenAPI documenta ErrorResponse para el 404 de GET/PUT/DELETE por ID."""
    client = _client()
    spec = client.get("/openapi.json").json()
    path = spec["paths"]["/api/v1/products/{product_id}"]
    for method in ("get", "put", "delete"):
        responses = path[method]["responses"]
        assert "404" in responses
        schema = (
            responses["404"]
            .get("content", {})
            .get("application/json", {})
            .get("schema", {})
        )
        assert schema.get("$ref") == "#/components/schemas/ErrorResponse"
    assert "ErrorResponse" in spec["components"]["schemas"]


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
