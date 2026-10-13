## Sección 6 — avance evolutivo

Este paquete asume que las secciones 1–5 ya existen en el repositorio. No incluye `requirements.txt`, `pyproject.toml` ni `app/schemas/product.py` porque no necesitan cambios para esta entrega.

## Archivos nuevos

- `app/core/__init__.py`
- `app/core/dependencies.py`
- `app/core/exception_handlers.py`
- `app/domain/__init__.py`
- `app/domain/exceptions.py`
- `app/domain/models.py`
- `app/repositories/__init__.py`
- `app/repositories/product_repository.py`
- `app/repositories/in_memory_product_repository.py`
- `app/services/__init__.py`
- `app/services/product_service.py`
- `app/schemas/errors.py`
- `tests/__init__.py`
- `tests/test_http_errors.py`
- `tests/test_product_service.py`
- `docs/section-06-manifest.md`

## Archivos que se reemplazan o actualizan

- `app/main.py`
- `README.md`
- `docs/architecture.md`
- `docs/crud.md`
- `docs/acceptance-criteria.md`
- `docs/http-errors.md`

## Qué no hace esta sección

- No mueve las rutas a `APIRouter`; esa es la sección 7.
- No añade una base de datos ni persistencia durable.
- No elige ni llama un proveedor de IA.
- No modifica dependencias fijadas en `requirements.txt`.
