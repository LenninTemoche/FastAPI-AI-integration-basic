# Manifiesto de archivos — Sección 7

Archivos nuevos

- `app/api/__init__.py`
- `app/api/root.py`
- `app/api/v1/__init__.py`
- `app/api/v1/router.py`
- `app/api/v1/endpoints/__init__.py`
- `app/api/v1/endpoints/products.py`
- `docs/api-routing.md`
- `docs/create-and-idempotency-semantics.md`
- `docs/section-07-manifest.md` (este documento)
- `tests/test_product_create_semantics.py`

## Archivos existentes que se reemplazan

- `app/main.py`
- `README.md`
- `docs/architecture.md`
- `docs/acceptance-criteria.md`
- `docs/crud.md`
- `docs/http-errors.md`

## Archivos existentes que se conservan sin reemplazar

En particular, mantén `requirements.txt`, `.gitignore`, `AGENTS.md`, los documentos
de secciones anteriores no mencionados arriba y los módulos de dominio, esquemas,
servicios, repositorios y manejadores de excepciones de la sección 6. No hay que
crear ni cambiar `requirements.txt` para esta sección.

## Política de integración

1. Comprobar rutas respetando la ubicación relativa.
2. Revisar los cambios con `git status`, `git diff --check` y `git diff`.
3. No marcar como aceptada la sección 7 hasta ejecutar las pruebas locales.
4. Hacer el commit y push manualmente solo después de revisar el diff.
