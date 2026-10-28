# Cierre de la Fase 1 — Arquitectura modular

## Estado

**Implementada; cierre en verificación.** La Fase 1 no está cerrada: queda pendiente el cierre formal de verificaciones (suite hermética, CI, regeneración de reporte y evidencia).

## Qué está implementado y verificado

| ID | Elemento | Evidencia (medido en esta sesión) |
|----|----------|-----------------------------------|
| V1 | Rama y HEAD | `fix/fase1-cierre`, HEAD `16dab3b`, árbol sincronizado con `origin/fix/fase1-cierre`, árbol limpio |
| V2 | Suite | 172 tests recolectados y 172 pasados, 0 fallos, 0 omitidos (`python -m pytest -q`, 27.99s) |
| V3 | Archivos de tests | 24 archivos `test_*.py` en `tests/`; 23 aportan tests (`test_llm_connection.py` es standalone, 0 tests). No existe `tests/test_modularity.py` |
| V4 | Suite sin credenciales LLM | No es hermética: sin `LLM_API_KEY`/`LLM_BASE_URL`/`LLM_MODEL`, `test_lifespan.py::LifespanTests::test_llm_ask_with_mock_transport_returns_200` falla (recibe 503, espera 200). Pendiente: suite hermética |
| V5 | OpenAPI | 8 paths idénticos a `main`: `/`, `/health`, `/api/v1/modules`, `/api/v1/llm/ask`, `/api/v1/media/transcriptions`, `/api/v1/media/videos/analyze`, `/api/v1/products`, `/api/v1/products/{product_id}` |
| V6 | .env.example | Alineado 1:1 con `Settings` (15 variables / 15 campos) |
| V7 | Dependencias | `pyproject.toml` fuente única; `requirements.txt = "-e .[media,dev]"` sin pines `==`; `constraints.txt = 64 pines generados en Windows + Python 3.13` (no lock multiplataforma) |
| V8 | Versión Python | `requires-python = ">=3.13"`; `pip install -e .` falla en 3.11/3.12; el código ejecuta en 3.11 con las dependencias del proyecto |
| V9 | `imageio-ffmpeg` | Import perezoso en `app/modules/media/adapters/ffmpeg_video_processor.py` (dentro de `_extract_sync`). `create_app(enabled=["media"])` funciona sin el extra; solo el análisis de video devuelve 503 |
| V10 | Estructura `app/` | `main.py`, `factory.py`, `core/` (config, module, registry, http, system, schemas), `modules/` (llm, media, products) |
| V11 | Deprecaciones | 6 `StarletteDeprecationWarning` por `HTTP_422_UNPROCESSABLE_ENTITY` en `app/modules/media/errors.py:36` y `app/modules/media/router.py:37`. Pendiente, sin modificar `app/` en esta tarea |
| V12 | Cierre | `PHASE1_VERIFICATION_REPORT.md` y `evidence.txt` citan datos históricos desfasados (rama `refactor/fase1-modulos`, SHA `cf9e996`, 126/104/78 tests). Se mantienen como registro histórico |

## Pendientes de cierre (P1–P5)

| Pendiente | Criterio de salida (verificable) |
|-----------|----------------------------------|
| P1 Suite hermética | `python -m pytest -q` pasa en 172/172 sin requerir `LLM_API_KEY`, `LLM_BASE_URL` ni `LLM_MODEL` reales |
| P2 Reporte con SHA de cierre | `PHASE1_VERIFICATION_REPORT.md` tiene un anexo al inicio con la tabla "dato del reporte vs valor medido hoy" (rama/SHA, conteo de tests, `test_modularity`, suite sin credenciales, OpenAPI, `evidence.txt`) |
| P3 Evidencia regenerada o retirada | `evidence.txt` y `evidence-s8.txt` reflejan el SHA de cierre real o están marcados como históricos/no reproducibles |
| P4 CI | Pipeline de CI configurado (lint, typecheck, tests, build) — fuera de esta tarea, queda para Fase 2 |
| P5 Deprecaciones 422 | `HTTP_422_UNPROCESSABLE_ENTITY` reemplazado por `HTTP_422_UNPROCESSABLE_CONTENT` en `app/modules/media/errors.py` y `app/modules/media/router.py` |

## Fuera de alcance de esta tarea

- **Fase 2**: autenticación con API keys para consumidores, rate limiting, errores unificados (RFC 9457), CI.
- **Fase 3**: SQLAlchemy, Alembic, observabilidad.
- **Fases 4–6**: CLI forge, prompts, RAG/ML/agentes.

## Riesgos aceptados

1. **`app = create_app()` a nivel de módulo** (`app/main.py`): crea la app al importarse con `ENABLED_MODULES` por defecto (`llm,media,products`), cargando todos los módulos en `sys.modules` incluso cuando se usa `create_app(enabled=["products"])`. Los tests de aislamiento usan subprocess para evitar esto.
2. **`get_settings()` con `@lru_cache`**: la configuración se cachea tras la primera llamada; cambios de variables de entorno después del primer `get_settings()` no se reflejan.

## Documentación relacionada

- [`architecture.md`](architecture.md): arquitectura modular y `ModuleSpec`.
- [`acceptance-criteria.md`](acceptance-criteria.md): criterios de aceptación por sección.
- [`setup.md`](setup.md): instalación, dependencias y ejecución de pruebas.
- [`../PHASE1_VERIFICATION_REPORT.md`](../PHASE1_VERIFICATION_REPORT.md): reporte de verificación (cuerpo histórico, anexo con datos medidos hoy).
- [`../AGENTS.md`](../AGENTS.md): reglas para agentes de programación.
