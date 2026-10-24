# Criterios de aceptación

Los criterios reflejan las secciones documentadas del proyecto. No marcar la
sección activa como cerrada hasta ejecutar las verificaciones en el entorno local
con Python 3.13 y las dependencias del repositorio.


## A. Sección 1 — alcance y arquitectura

- [x] A1. El README identifica claramente el propósito y el estado actual del proyecto.
- [x] A2. Se definen objetivos, casos de uso, requisitos funcionales y no funcionales.
- [x] A3. Se documentan explícitamente los temas fuera de alcance.
- [x] A4. La arquitectura se representa en un diagrama y se describen las responsabilidades de cada capa.
- [x] A5. Se aclara que la solución empieza como monolito modular, no como microservicios.
- [x] A6. Python 3.13 queda registrado como versión objetivo, con compatibilidad de dependencias por comprobar en la sección 2.
- [x] A7. El proveedor LLM queda abierto y se establece que su clave permanecerá del lado servidor.
- [x] A8. Se identifica la limitación del almacenamiento en memoria como recurso didáctico, no como persistencia de producción.
- [x] A9. La documentación indica cómo se organizarán las secciones y los avances de forma incremental.
- [x] A10. Se prepara el repositorio documental inicial.

## B. Sección 2 — entorno y primer endpoint

- [x] B1. Instalación reproducible de dependencias en un entorno limpio con Python 3.13.
- [x] B2. El entorno virtual `.venv` se crea en la raíz y está excluido por `.gitignore`.
- [x] B3. `pip install -r requirements.txt` termina sin errores.
- [x] B4. La versión instalada de FastAPI es `0.161.1`.
- [x] B5. La aplicación inicia con `fastapi dev` desde la raíz del repositorio.
- [x] B6. `GET /` responde `200 OK` con JSON de estado.
- [x] B7. Swagger UI en `/docs` muestra y ejecuta `GET /`.
- [x] B8. `/redoc` y `/openapi.json` responden correctamente.
- [x] B9. La documentación refleja los pasos verificados.
- [x] B10. Los cambios se confirmaron mediante commit manual, avance incremental.

## C. Sección 3 — rutas y parámetros

Sección 3 completada y verificada localmente. Las respuestas didácticas se sustituyeron por operaciones CRUD, pero los parámetros y restricciones principales se conservan.

- [x] C1. `GET /` sigue respondiendo `200 OK`.
- [x] C2. `GET /api/v1/products/25` devuelve el entero `product_id: 25`.
- [x] C3. `GET /api/v1/products` aplica `limit=10` e `include_desc=false` por defecto.
- [x] C4. `GET /api/v1/products?limit=5&include_desc=true` devuelve los valores tipados `5` y `true`.
- [x] C5. Un `product_id` no entero produce `422`.
- [x] C6. Un `limit` no entero produce `422`.
- [x] C7. Swagger muestra los tres endpoints y documenta los parámetros.
- [x] C8. La guía se revisó y se subió mediante commit manual.

## D. Sección 4 — validación con Pydantic

Hito cerrado según el flujo de trabajo del proyecto. El endpoint demostrativo `POST /api/v1/products/validate` se retiró deliberadamente en la sección 5; `ProductCreate` se conserva y se aplica al CRUD.

- [x] D1. La API sigue arrancando y `GET /` responde `200 OK`.
- [x] D2. `GET /api/v1/products/25` sigue devolviendo `product_id: 25`.
- [x] D3. `GET /api/v1/products?limit=0` y `limit=101` devuelven `422`.
- [x] D4. `GET /api/v1/products/0` devuelve `422`.
- [x] D5. El payload válido de `POST /api/v1/products/validate` devuelve `200` y `valid: true`.
- [x] D6. `name` con menos de 3 caracteres devuelve `422`.
- [x] D7. `price <= 0`, `stock < 0` y los tipos no válidos devuelven `422`.
- [x] D8. Un campo desconocido devuelve `422`.
- [x] D9. Una descripción de más de 500 caracteres devuelve `422`.
- [x] D10. Swagger muestra el esquema del body y las restricciones de campos.
- [x] D11. `docs/pydantic-validation.md` y este documento se revisan.
- [x] D12. Los cambios pasan `git diff --check`, se revisan y se incluyen en un commit manual.

## E. Sección 5 — CRUD en memoria

Sección completada y verificada localmente. El endpoint demostrativo `POST /api/v1/products/validate` se retiró deliberadamente en la sección 5; `ProductCreate` se conserva y se aplica al CRUD.

- [x] E1 Crear (`POST`), listar (`GET`), consultar (`GET` por ID), actualizar (`PUT`) y eliminar (`DELETE`).
- [x] E2 Paginación `skip`/`limit` y opción `include_desc`.
- [x] E3 Estados `201`, `200` y `204` documentados.
- [x] E4 Limitación de almacenamiento en memoria documentada.

## Secciones 1-6 completadas y verificadas localmente.

- [x] Alcance y arquitectura inicial documentados.
- [x] Entorno y primer endpoint validados localmente según seguimiento del proyecto.
- [x] Rutas y parámetros documentados y validados localmente.
- [x] Contratos Pydantic integrados al CRUD.
- [x] CRUD de productos y paginación en memoria.
- [x] Errores HTTP documentados; dominio, servicio y repositorio separados.
- [x] El repositorio mantiene almacenamiento en memoria explícitamente no apto para producción.

**En las secciones siguientes se trabajó en la separación de capas y la integración con IA**

## F. Sección 6 — manejo de errores HTTP y separación en capas 

- [x] F1 El servicio no importa FastAPI y las entidades de dominio no dependen de HTTP.
- [x] F2 El servicio depende del protocolo `ProductRepository`.
- [x] F3 GET/PUT/DELETE por ID inexistente devuelven `404` con formato `{"detail":"..."}`.
- [x] F4 Validaciones siguen devolviendo `422`; DELETE correcto devuelve `204` sin cuerpo.
- [x] F5 Se documenta `ErrorResponse` en OpenAPI.


## Sección 7 — modularización con APIRouter (completada)

- [x] G1 `app/main.py` solo compone la aplicación, maneja el registro de routers y los manejadores HTTP.
- [x] G2 `GET /` se conserva en un router general (`app/core/system.py`).
- [x] G3 El CRUD se mueve a `app/modules/products/router.py`.
- [x] G4 `app/core/registry.py` agrega routers bajo `/api/v1` vía `install_modules()`.
- [x] G5 Se conservan exactamente los métodos y paths públicos existentes.
- [x] G6 Se conservan respuestas 200, 201, 204, 404 y 422, esquemas y parámetros.
- [x] G7 Swagger/OpenAPI enumera cada endpoint solo una vez y mantiene el esquema `ErrorResponse` para los 404.
- [x] G8 Las pruebas existentes y `tests/test_product_create_semantics.py` pasan.
- [x] G9 Dos POST con payloads idénticos crean dos recursos con IDs distintos; este contrato está documentado, no se trata como deduplicación.
- [x] G10 `docs/api-routing.md`, `docs/create-and-idempotency-semantics.md` y referencias relacionadas están actualizadas.
- [x] G11 `git diff --check` pasa, el diff revisado y el commit/push manual queda realizado.

## Sección 8 — integración LLM mediante adaptador (completada)

- [x] H1 `/api/v1/llm/ask` aparece en OpenAPI y usa un contrato propio Pydantic.
- [x] H2 Se valida que el prompt no esté vacío y que no exceda los límites definidos.
- [x] H3 El cliente no puede enviar una `api_key` en el cuerpo del request.
- [x] H4 `LLMService` depende del protocolo `LLMProvider`, no de HTTPX ni de FastAPI.
- [x] H5 El adaptador usa HTTPX asíncrono y autenticación Bearer con una clave cargada desde el servidor.
- [x] H6 URL base, modelo, timeout, tokens máximos y temperatura se configuran por entorno.
- [x] H7 La clave se maneja como secreto; `.env` no se versiona y `.env.example` no contiene credenciales reales.
- [x] H8 Se reutiliza y cierra `AsyncClient` mediante el lifespan de FastAPI.
- [x] H9 No se exponen el body de error del proveedor, prompts ni API keys en errores de respuesta/logs.
- [x] H10 Falta de configuración devuelve `503`; límite externo devuelve `503`; error externo/formato incompatible `502`; timeout `504`.
- [x] H11 Se prueban éxito, validación, configuración ausente, timeout, rate limit, error externo y formato de respuesta sin llamadas reales.
- [x] H12 Se conserva el contrato CRUD existente y la suite completa pasa localmente.
- [x] H13 README, arquitectura, configuración y guía de integración están actualizados.
- [x] H14 `git diff --check` y revisión del diff pasan; el usuario realiza commit y push manual.

## Extensión multimodal de la sección 8 (completada)

- [x] H15. `POST /api/v1/media/transcriptions` está documentado en OpenAPI y devuelve texto normalizado.
- [x] H16. Audio usa `MEDIA_TRANSCRIPTION_MODEL`, clave de servidor y endpoint multipart dedicado.
- [x] H17. Tipos de archivo, tamaños y campos Form se validan con respuestas 413/415/422 controladas.
- [x] H18. `POST /api/v1/media/videos/analyze` extrae un máximo configurado de fotogramas y acota duración/tiempo de FFmpeg.
- [x] H19. Transcripción de video es opcional y su estado se devuelve explícitamente.
- [x] H20. La ruta de video usa un adaptador de visión separado; no exige modificar `/api/v1/llm/ask`.
- [x] H21. Tests de API, servicios y adaptadores usan mocks y no requieren API key real.
- [x] H22. El archivo existente `app/integrations/llm/openai_compatible.py` y el fallback Chat/Reasoning se preservan.
- [x] H23. Las pruebas se ejecutan localmente con Python 3.13 y las dependencias fijadas del repositorio.
- [x] H24. Se completa una llamada manual controlada con un modelo que admita la capacidad seleccionada.


## Fase 1 — Arquitectura modular con registry y módulos opcionales (COMPLETADA)

- [x] J1. Estructura `app/modules/{llm,media,products}/` con `manifest.py`, `router.py`, `service.py`, `ports.py`, `schemas.py`, `deps.py`, `errors.py`, `adapters/`.
- [x] J2. `app/core/module.py` define `ModuleSpec` dataclass.
- [x] J3. `app/core/registry.py` implementa `resolve()` (orden topológico + detección ciclos) e `install_modules()`.
- [x] J4. `app/core/system.py` expone `GET /`, `/health`, `/api/v1/modules`.
- [x] J5. `app/main.py` usa `create_app(enabled=...)` y `install_modules()`.
- [x] J6. Variable `ENABLED_MODULES` (coma-separated) controla qué módulos se cargan.
- [x] J7. Fábrica `build_provider(settings, client)` en `llm/adapters/__init__.py` seleccionable por `LLM_PROVIDER`.
- [x] J8. Módulo `media` declara `requires=("llm",)` y se carga después de `llm`.
- [x] J9. Cada módulo registra sus propios handlers de error vía `spec.register(app)`.
- [x] J10. Tests pasan: `create_app(enabled=["products"])` monta solo products (llm/media → 404).
- [x] J11. Módulo desconocido falla rápido con `ModuleLoadError`.
- [x] J12. Endpoint `/api/v1/modules` lista módulos activos con nombre, versión y descripción.
- [x] J12. URLs públicas preservadas: 6 originales + 2 nuevas (`/health`, `/api/v1/modules`).
- [x] J13. 78 tests pasan incluyendo tests de modularidad.
- [x] J14. Documentación actualizada (README, architecture.md, acceptance-criteria.md).
- [x] J15. `git diff --check` pasa, commit manual realizado.

## Objetivos globales

- [ ] I1 Proveedor LLM desacoplado detrás de un adaptador, llamado mediante API key en el servidor.
- [ ] I2 Autenticación de consumidores, límites de consumo y secretos gestionados correctamente.
- [ ] I3 Persistencia durable y configuración por entorno.
- [ ] I4 Pruebas de integración para llamadas externas, timeout y errores del proveedor.
- [ ] I5 Documentación de integración para Python, Java/Spring Boot y clientes web.
- [ ] I6 Preparación para Docker, CI y despliegue.

## Fase 2 — Auth con API keys + rate limiting + errores unificados + CI (PENDIENTE)

- [ ] K1. Módulo `auth` con API keys para consumidores (distintas de proveedor LLM).
- [ ] K2. Rate limiting por consumidor (token bucket / sliding window).
- [ ] K3. Errores unificados con códigos y formato consistente.
- [ ] K4. CI pipeline (lint, typecheck, tests, build).
- [ ] K5. Documentación actualizada.

## Sección 9 — producción (pendiente)

- [ ] Autenticación/autorización de clientes, distinta de la API key del proveedor.
- [ ] Rate limiting/cuotas, políticas de coste y límites por consumidor.
- [ ] Pruebas de integración/reproducibilidad en el conjunto de dependencias del repositorio.
- [ ] Logging, métricas y observabilidad sin secretos ni contenido sensible.
- [ ] Decisión e implementación de persistencia durable si el caso de uso lo necesita.
- [ ] Docker/CI/despliegue y comprobaciones operativas.

No declarar la API lista para producción hasta revisar los controles que correspondan al entorno donde vaya a exponerse.