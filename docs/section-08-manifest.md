# Manifiesto — Sección 8

# Manifiesto incremental — extensión multimodal de sección 8

## Archivos NUEVOS
- `app/services/ports/media_provider.py`
- `app/services/media_service.py`
- `app/integrations/llm/openai_compatible_audio.py`
- `app/integrations/llm/openai_compatible_vision.py`
- `app/integrations/media/__init__.py`
- `app/integrations/media/ffmpeg_video_processor.py`
- `app/schemas/media.py`
- `app/api/v1/endpoints/media.py`
- `docs/multimodal-media.md`
- `tests/test_media_providers.py`
- `tests/test_media_service.py`
- `tests/test_media_api.py`
- `tests/test_video_processor_integration.py`

## Archivos a REEMPLAZAR
- `.env.example`
- `requirements.txt`
- `app/core/config.py`
- `app/core/dependencies.py`
- `app/core/exception_handlers.py`
- `app/api/v1/router.py`
- `app/services/ports/__init__.py`
- `docs/architecture.md`
- `docs/acceptance-criteria.md`
- `README.md`

## No reemplazar

- `.gitignore`, `AGENTS.md`, `pyproject.toml`, `app/domain/`, `app/repositories/`, `app/services/product_service.py`, `app/schemas/product.py`, `app/api/v1/endpoints/products.py` ni las pruebas previas.
