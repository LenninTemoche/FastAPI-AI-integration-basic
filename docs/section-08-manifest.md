# Manifiesto — Sección 8

> **Nota:** Este manifiesto refleja el estado al completar la Sección 8 (antes de la modularización de la Fase 1). La estructura actual (Fase 1 completada) usa `app/modules/` con `app/core/registry.py`.

# Manifiesto incremental — extensión multimodal de sección 8

## Archivos NUEVOS (Sección 8 original)

- `app/services/ports/media_provider.py` → `app/modules/media/ports.py`
- `app/services/media_service.py` → `app/modules/media/service.py`
- `app/integrations/llm/openai_compatible_audio.py` → `app/modules/media/adapters/openai_audio.py`
- `app/integrations/llm/openai_compatible_vision.py` → `app/modules/media/adapters/openai_vision.py`
- `app/integrations/media/__init__.py` → `app/modules/media/adapters/__init__.py`
- `app/integrations/media/ffmpeg_video_processor.py` → `app/modules/media/adapters/ffmpeg_video_processor.py`
- `app/schemas/media.py` → `app/modules/media/schemas.py`
- `app/api/v1/endpoints/media.py` → `app/modules/media/router.py`
- `docs/multimodal-media.md`
- `tests/test_media_providers.py` → `tests/test_media_providers.py` (mantenido)
- `tests/test_media_service.py` → `tests/test_media_service.py` (mantenido)
- `tests/test_media_api.py` → `tests/test_media_api.py` (mantenido)
- `tests/test_video_processor_integration.py` → `tests/test_video_processor_integration.py` (mantenido)

## Archivos a REEMPLAZAR

- `.env.example`
- `requirements.txt`
- `app/core/config.py`
- `app/core/dependencies.py`
- `app/core/exception_handlers.py`
- `app/api/v1/router.py` → `app/core/registry.py`
- `app/services/ports/__init__.py` → `app/modules/media/ports.py`
- `docs/architecture.md`
- `docs/acceptance-criteria.md`
- `README.md`

## No reemplazar (mantenidos y movidos en Fase 1)

- `.gitignore`, `AGENTS.md`, `pyproject.toml`, `app/domain/`, `app/repositories/`, `app/services/product_service.py`, `app/schemas/product.py`, `app/api/v1/endpoints/products.py` ni las pruebas previas.

> **Estado actual (Fase 1 completada):** Los archivos de la Sección 8 fueron reorganizados en la arquitectura modular bajo `app/modules/media/` con sus propios `router.py`, `service.py`, `ports.py`, `schemas.py`, `deps.py`, `errors.py`, `manifest.py` y `adapters/`.