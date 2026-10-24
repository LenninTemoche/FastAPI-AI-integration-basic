# Sección 7 — Modularización con APIRouter

## Objetivo

Separar la definición de rutas de `app/main.py` manteniendo estables los paths,
métodos, contratos Pydantic, códigos HTTP y formato de errores que ya consumen
los clientes.

## Nueva organización (Fase 1: arquitectura modular)

```text
app/
├── main.py                       # composición de la aplicación (factory)
├── core/
│   ├── system.py                 # GET / · /health · /api/v1/modules
│   └── registry.py               # ModuleSpec, resolve(), install_modules()
└── modules/
    ├── products/                 # CRUD demo
    │   ├── router.py             # CRUD HTTP /products
    │   ├── service.py            # ProductService
    │   ├── repository.py         # ProductRepository protocol
    │   └── ...
    ├── llm/                      # Generación de texto
    │   ├── router.py             # POST /ask
    │   ├── service.py            # LLMService
    │   ├── adapters/             # proveedores LLM
    │   └── ...
    └── media/                    # Audio + Video
        ├── router.py             # POST /transcriptions, /videos/analyze
        ├── service.py            # Audio/Video Services
        ├── adapters/             # Whisper, visión, FFmpeg
        └── ...
```

`app/main.py` crea la aplicación vía `create_app()` (en `app/factory.py`), registra
el router de sistema y llama a `install_modules()` que carga dinámicamente los
módulos habilitados según `ENABLED_MODULES`.

## Límites de responsabilidad

- `main.py` / `factory.py`: composición del proceso HTTP; no define operaciones de negocio.
- `core/system.py`: endpoints transversales (`GET /`, `/health`, `/api/v1/modules`).
- `core/registry.py`: registro central de módulos, resolución de dependencias.
- `modules/<name>/router.py`: endpoints HTTP del módulo (sin prefijo, el registry lo añade).
- `modules/<name>/service.py`: casos de uso; no importa FastAPI.
- `modules/<name>/ports.py`: protocolos/contratos para adaptadores.
- `modules/<name>/adapters/`: implementaciones concretas (proveedores LLM, Whisper, FFmpeg).
- `ProductService` / `LLMService` / `AudioTranscriptionService` / `VideoAnalysisService`: casos de uso; no importan FastAPI.
- Repositorios y adaptadores: implementaciones concretas de puertos.

## Compatibilidad que se debe conservar

| Método | Ruta |
|---|---|
| GET | `/` |
| GET | `/health` |
| GET | `/api/v1/modules` |
| POST | `/api/v1/llm/ask` |
| POST | `/api/v1/media/transcriptions` |
| POST | `/api/v1/media/videos/analyze` |
| POST | `/api/v1/products` |
| GET | `/api/v1/products` |
| GET | `/api/v1/products/{product_id}` |
| PUT | `/api/v1/products/{product_id}` |
| DELETE | `/api/v1/products/{product_id}` |

Los códigos `200`, `201`, `204`, `404` y `422`, la paginación `skip`/`limit`,
`include_desc`, la excepción de dominio y el esquema `ErrorResponse` se mantienen.

## Comprobaciones

1. Ejecutar `python -m unittest discover -s tests -v`.
2. Arrancar `fastapi dev` desde la raíz del repo.
3. Verificar `/`, `/health`, `/api/v1/modules`, `/docs`, `/redoc` y `/openapi.json`.
4. En Swagger, comprobar que los endpoints aparecen agrupados por módulo
   (`llm`, `media`, `products`) y que el conjunto de paths se mantiene.
5. Probar CRUD, parámetros inválidos, los `404` y el `204` sin cuerpo.
6. Probar dos solicitudes POST idénticas y confirmar el contrato documentado en
   `docs/create-and-idempotency-semantics.md`.