# Manifiesto — Sección 8

## Archivos nuevos

- `.env.example`
- `app/core/config.py`
- `app/integrations/__init__.py`
- `app/integrations/llm/__init__.py`
- `app/services/ports/__init__.py`
- `app/services/ports/llm_provider.py`
- `app/services/llm_service.py`
- `app/schemas/llm.py`
- `app/api/v1/endpoints/llm.py`
- `docs/llm-integration.md`
- `docs/section-08-manifest.md`
- `tests/test_llm_api.py`
- `tests/test_llm_provider.py`
- `tests/test_llm_service.py`

## Archivos que se reemplazan o actualizan

- `requirements.txt`: incorpora HTTPX, Pydantic Settings y python-dotenv como dependencias directas.
- `app/main.py`: añade lifespan para un cliente HTTPX reutilizable.
- `app/core/dependencies.py`: compone el servicio LLM y el adaptador.
- `app/core/exception_handlers.py`: traduce fallos LLM a errores HTTP controlados.
- `app/api/v1/router.py`: registra el router LLM además del router CRUD existente.
- `README.md`, `docs/architecture.md` y `docs/acceptance-criteria.md`: reflejan el estado de la sección 8.

## No reemplazar

- `.gitignore`, `AGENTS.md`, `pyproject.toml`, `app/domain/`, `app/repositories/`, `app/services/product_service.py`, `app/schemas/product.py`, `app/api/v1/endpoints/products.py` ni las pruebas previas.

El `.env` local no se incluye en el ZIP y nunca debe subirse a Git.
