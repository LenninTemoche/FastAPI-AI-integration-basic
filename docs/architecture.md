# Arquitectura evolutiva

## Objetivo

Construir una API modular y documentada que se pueda integrar mediante HTTP/JSON en aplicaciones web, móviles, servicios Python/Java, proyectos de análisis de datos, Machine Learning e IA, manteniendo separadas la capa HTTP, la lógica de negocio, la persistencia y las integraciones externas.

## 1. Estilo arquitectónico

La primera versión es un **monolito modular**: una sola aplicación desplegable, organizada en módulos con responsabilidades claras. No se dividirá prematuramente en microservicios.

El objetivo es que la API pueda crecer sin acoplar sus rutas HTTP a la lógica de negocio, al mecanismo de persistencia ni al proveedor de IA.

### Estructura actual (Fase 1 completada)

```text
app/
├── main.py                                    # create_app(enabled=...) + lifespan
├── core/
│   ├── config.py                              # Settings + enabled_modules_list + LLM_PROVIDER
│   ├── module.py                              # ModuleSpec dataclass
│   ├── registry.py                            # resolve() + install_modules()
│   ├── system.py                              # GET / · /health · /api/v1/modules
│   └── schemas.py                             # ErrorResponse compartido
└── modules/
    ├── llm/                                   # Generación de texto
    │   ├── manifest.py                        # ModuleSpec (register=errors)
    │   ├── router.py                          # POST /ask
    │   ├── service.py                         # LLMService
    │   ├── deps.py                            # get_llm_service (inyecta proveedor)
    │   ├── errors.py                          # 502/503/504 handlers
    │   ├── ports.py                           # LLMProvider protocol + errores dominio
    │   ├── schemas.py                         # LLMAskRequest/Response/Usage
    │   └── adapters/
    │       ├── __init__.py                    # build_provider factory (LLM_PROVIDER)
    │       └── openai_compatible.py           # Chat Completions
    ├── media/                                 # Audio + Video
    │   ├── manifest.py                        # ModuleSpec (requires=llm)
    │   ├── router.py                          # POST /transcriptions, /videos/analyze
    │   ├── service.py                         # Audio/Video Analysis Services
    │   ├── deps.py                            # get_audio/video_service
    │   ├── errors.py                          # 413/415/422/502/503/504 handlers
    │   ├── ports.py                           # Audio/Video/Vision protocols
    │   ├── schemas.py                         # Media/Video responses
    │   └── adapters/
    │       ├── __init__.py                    # exports
    │       ├── ffmpeg_video_processor.py
    │       ├── openai_audio.py                # /audio/transcriptions
    │       └── openai_vision.py               # Chat Completions + frames
    └── products/                              # CRUD demo
        ├── manifest.py                        # ModuleSpec (name=products)
        ├── router.py                          # CRUD /products
        ├── service.py                         # ProductService
        ├── deps.py                            # get_product_service (singleton repo)
        ├── errors.py                          # ProductNotFoundError → 404
        ├── repository.py                      # ProductRepository protocol
        ├── in_memory_repository.py
        ├── models.py                          # Product / ProductDraft
        ├── exceptions.py                      # ProductNotFoundError
        └── schemas.py                         # ProductCreate/Read/ListResponse
```

## 2. Vista de alto nivel

```mermaid
flowchart TD
    C[Clientes HTTP/JSON<br/>Web · móvil · Java · Python · ML] --> MAIN[app/main.py<br/>create_app(enabled=...) + lifespan]
    MAIN --> SYS[app/core/system.py<br/>GET / · /health · /modules]
    MAIN --> REG[app/core/registry.py<br/>resolve + install_modules]
    MAIN -.->|importlib| MODS[app/modules/<name>/]
    MODS --> LLM[llm/<br/>service · ports · adapters]
    MODS --> MEDIA[media/<br/>service · ports · adapters]
    MODS --> PROD[products/<br/>service · repo · in-memory]
    MEDIA --> LLM
    SYS -.->|OpenAPI| DOCS[/docs · /openapi.json]
    MAIN -.->|lifespan| LIFESPAN[httpx.AsyncClient<br/>shared pool]

    style C fill:#1a202c,stroke:#0d1117,color:#f1f5f9
    style MAIN fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style SYS fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style REG fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style MODS fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style LLM fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style MEDIA fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style PROD fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style LIFESPAN fill:#4a5568,stroke:#2d3748,color:#f1f5f9
```

### Responsabilidades y dirección de dependencias

| Capa                           | Responsabilidad                                                                                          | No debe depender de                        |
| ------------------------------ | -------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| `main.py`                      | Crear la aplicación, registrar excepciones, instalar módulos                                             | Lógica CRUD concreta                       |
| `app/core/system.py`           | Endpoints transversales (GET /, /health, /modules)                                                       | Módulos específicos                        |
| `app/core/registry.py`         | Resolver dependencias e instalar módulos en orden topológico                                             | Implementaciones concretas                 |
| `app/modules/<name>/manifest.py` | Exporta `ModuleSpec` (router, register, requires, lifespan)                                              | Otros módulos (salvo `requires`)           |
| `app/modules/<name>/router.py` | Endpoints HTTP del módulo, sin prefijo (registry añade `/api/v1/<name>`)                                 | Servicios y esquemas del mismo módulo      |
| `app/modules/<name>/service.py`| Casos de uso, reglas de aplicación                                                                       | FastAPI, HTTPX, SDKs                       |
| `app/modules/<name>/ports.py`  | Protocolos/Interfaces para adaptadores                                                                   | FastAPI, HTTPX, SDKs, FFmpeg               |
| `app/modules/<name>/adapters/` | Implementaciones concretas de puertos                                                                    | Contratos HTTP públicos                    |
| `app/modules/<name>/schemas.py`| Contratos Pydantic de entrada/salida del módulo                                                          | Servicios, persistencia                    |
| `app/modules/<name>/errors.py` | Manejadores de excepción del módulo                                                                      | Implementaciones concretas                 |
| `app/modules/<name>/deps.py`   | Inyección de dependencias del módulo (servicios, proveedores)                                            | Reglas de negocio                          |
| `app/core/config.py`           | Cargar y validar variables de entorno, `SecretStr`, `enabled_modules_list`, `LLM_PROVIDER`               | Reglas de negocio                          |
| `app/core/schemas.py`          | `ErrorResponse` compartido                                                                               | —                                          |

## 3. Module Registry (Nuevo en Fase 1)

### `ModuleSpec` (`app/core/module.py`)

```python
@dataclass(frozen=True)
class ModuleSpec:
    name: str                                   # Debe coincidir con la carpeta
    description: str
    version: str = "1.0.0"
    router: APIRouter | None = None
    prefix: str | None = None                   # Por defecto: /api/v1/<name>
    requires: tuple[str, ...] = ()              # Otros módulos que deben cargarse antes
    register: Callable[[FastAPI], None] | None = None   # Manejadores de error, middleware...
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]] | None = None
```

### `install_modules` (`app/core/registry.py`)

```python
def install_modules(app: FastAPI, enabled: list[str]) -> list[ModuleSpec]:
    specs = resolve(enabled)  # orden topológico con detección de ciclos
    for spec in specs:
        if spec.register:
            spec.register(app)
        if spec.router:
            app.include_router(
                spec.router,
                prefix=spec.prefix or f"/api/v1/{spec.name}",
                tags=[spec.name],
            )
        log.info("Módulo cargado: %s v%s", spec.name, spec.version)
    app.state.modules = {s.name: s for s in specs}
    return specs
```

### Carga dinámica y orden

- `resolve(enabled)` construye el grafo de dependencias (`requires`) y devuelve módulos en orden de carga.
- Detección de ciclos: `ModuleLoadError` si hay dependencia circular.
- Módulos no listados en `enabled` no se montan (404 en sus rutas).
- `app.state.modules` expone los módulos cargados para `/api/v1/modules`.

## 4. Módulos implementados

### 4.1 `llm` — Generación de texto

- **Endpoints**: `POST /api/v1/llm/ask`
- **Contratos**: `LLMAskRequest` → `LLMAskResponse` (proveedor, modelo, usage)
- **Puerto**: `LLMProvider` (protocol `generate(prompt, system_prompt)`)
- **Adaptador**: `OpenAICompatibleChatProvider` (HTTPX + Bearer token)
- **Factory**: `build_provider(settings, client)` seleccionable por `LLM_PROVIDER`
- **Errores**: 502 (response error), 503 (not configured / rate limit), 504 (timeout)
- **Config**: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS`, `LLM_MAX_TOKENS`, `LLM_TEMPERATURE`

### 4.2 `media` — Audio y video

- **Endpoints**:
  - `POST /api/v1/media/transcriptions` (multipart audio → texto)
  - `POST /api/v1/media/videos/analyze` (multipart video → análisis + transcripción opcional)
- **Requiere**: `llm` (usa `LLMProvider` para visión y transcripción)
- **Puertos**:
  - `AudioTranscriptionProvider` (transcribe audio)
  - `VideoVisionProvider` (analiza frames + transcript)
  - `VideoProcessor` (extrae frames + audio opcional)
- **Adaptadores**:
  - `OpenAICompatibleAudioTranscriber` (POST /audio/transcriptions)
  - `OpenAICompatibleVisionProvider` (Chat Completions + frames base64)
  - `FFmpegVideoProcessor` (extracción local con límites configurados)
- **Errores**: 413 (too large), 415 (unsupported), 422 (input error), 502/503/504 (provider/processor)
- **Config**: `MEDIA_TRANSCRIPTION_MODEL`, `MEDIA_MAX_AUDIO_MB`, `MEDIA_MAX_VIDEO_MB`, `MEDIA_VIDEO_MAX_FRAMES`, `MEDIA_VIDEO_FRAME_INTERVAL_SECONDS`, `MEDIA_PROCESSING_TIMEOUT_SECONDS`

### 4.3 `products` — CRUD demostrativo

- **Endpoints**: CRUD completo bajo `/api/v1/products`
- **Repositorio**: `ProductRepository` protocol + `InMemoryProductRepository`
- **Singleton**: `get_product_repository` usa `@lru_cache` para mantener estado entre requests
- **Errores**: `ProductNotFoundError` → 404 con `ErrorResponse`
- **Config**: ninguna específica (usa repositorio en memoria)

## 5. Configuración (`app/core/config.py`)

```python
class Settings(BaseSettings):
    # Módulos activos
    enabled_modules: str = "llm,media,products"
    
    @property
    def enabled_modules_list(self) -> list[str]:
        return [m.strip() for m in self.enabled_modules.split(",") if m.strip()]

    # Proveedor LLM
    llm_provider: Literal["openai_compatible"] = "openai_compatible"
    llm_api_key: SecretStr | None = None
    llm_base_url: AnyHttpUrl | None = None
    llm_model: str | None = None
    # ... timeouts, tokens, temperature ...

    # Media
    media_transcription_model: str | None = None
    media_max_audio_mb: int = 25
    media_max_video_mb: int = 50
    # ... video limits, ffmpeg timeouts ...
```

Validación: `LLM_BASE_URL` debe ser HTTPS salvo loopback (`localhost`, `127.0.0.1`, `::1`).

## 6. Cómo se conectan los routers

`app/main.py` crea la app y llama a `install_modules`:

```python
def create_app(enabled: list[str] | None = None) -> FastAPI:
    settings = get_settings()
    app = FastAPI(..., lifespan=lifespan)
    app.include_router(system.router)  # GET /, /health, /api/v1/modules
    install_modules(app, enabled if enabled is not None else settings.enabled_modules_list)
    return app
```

El registry monta cada router bajo `/api/v1/<module>` (o `prefix` personalizado en `ModuleSpec`).

## 7. Endpoints raíz y versiones

- `GET /`: informa del propósito de la API.
- `GET /health`: `{"status": "ok"}` para health checks.
- `GET /api/v1/modules`: lista módulos activos con `name`, `version`, `description`.

## 8. Contracts, excepciones y transformaciones

Cada módulo define sus propios esquemas y manejadores de error:

- `app/modules/products/errors.py` → `ProductNotFoundError` → 404
- `app/modules/llm/errors.py` → errores LLM → 502/503/504
- `app/modules/media/errors.py` → errores media → 413/415/422/502/503/504
- `app/core/schemas.py` → `ErrorResponse` compartido (`detail: str`)

Esta separación mantiene los dominios y servicios agnósticos a HTTP. Los endpoints no tratan excepciones de dominio directamente; las dejan a los handlers registrados por `spec.register(app)`.

## 9. Persistencia, servicios y composición

- `ProductService` depende del protocolo `ProductRepository`, no de la implementación.
- `InMemoryProductRepository` es singleton vía `@lru_cache` en `deps.py`.
- Para incorporar SQL u otro almacenamiento, se implementa el protocolo y se cambia el enlace en `products/deps.py`.

## 10. Integración LLM mediante adaptador

El proveedor por defecto es `openai_compatible`, seleccionable mediante `LLM_PROVIDER`. El diseño permite elegirlo desde configuración y, si se requiere un protocolo distinto, añadir un nuevo adaptador que implemente `LLMProvider` sin modificar el endpoint ni el caso de uso.

### Flujo de la solicitud LLM

1. FastAPI valida el JSON como `LLMAskRequest`.
2. El endpoint depende de `LLMService` (inyectado vía `deps.py`), sin conocer URLs, API keys ni librerías de proveedor.
3. `LLMService` invoca el contrato `LLMProvider`.
4. `OpenAICompatibleChatProvider` prepara la solicitud HTTP y usa el `AsyncClient` compartido del lifespan.
5. El adaptador normaliza texto/modelo/uso a `LLMGenerationResult`.
6. El endpoint devuelve `LLMAskResponse`; los fallos conocidos se convierten a `ErrorResponse` con estado 502/503/504.

### Cómo incorporar otro proveedor

Si el nuevo proveedor es compatible con el mismo contrato Chat Completions, se cambian base URL, credencial y modelo mediante entorno. Si el protocolo es distinto, crear una implementación nueva de `LLMProvider` bajo `app/modules/llm/adapters/` y añadir su selección en `build_provider` (una línea en `_PROVIDERS`). Mantener estable `LLMService`, `LLMAskRequest` y `LLMAskResponse` siempre que la funcionalidad sea equivalente.

## 11. Extensión multimodal

- `app/modules/media/router.py` expone contratos HTTP para transcripción y análisis de video.
- `app/modules/media/service.py` orquesta transcripción/análisis sin importar FastAPI ni HTTPX.
- `app/modules/media/ports.py` define los puertos de transcripción, visión y procesamiento de medios.
- `app/modules/media/adapters/openai_audio.py` implementa el protocolo de transcripción con multipart.
- `app/modules/media/adapters/openai_vision.py` envía fotogramas como imágenes a un modelo de visión compatible.
- `app/modules/media/adapters/ffmpeg_video_processor.py` extrae fotogramas y una pista de audio opcional mediante FFmpeg.

El video no se sube como video nativo al endpoint de chat: se toma una muestra acotada de frames y, si se habilita, se transcribe por separado su audio.

## 12. Errores y contratos

- Los errores de validación se expondrán mediante respuestas coherentes con FastAPI y su contrato OpenAPI.
- Los recursos inexistentes devolverán `404` cuando aplique.
- Los errores de autenticación y autorización se distinguirán (`401` y `403`).
- Los conflictos del estado del recurso podrán usar `409`.
- Los fallos inesperados no expondrán trazas, secretos ni detalles internos al consumidor.
- El formato común de errores es `ErrorResponse` (`detail: str`).

## 13. Versionado y compatibilidad

La API pública está bajo `/api/v1`. Los cambios compatibles podrán añadirse dentro de la versión actual; los cambios incompatibles exigirán una estrategia explícita de migración y una versión nueva cuando corresponda.

## 14. Decisiones aún abiertas

- Gestor de dependencias y formato de bloqueo.
- Almacenamiento persistente definitivo.
- Mecanismo de autenticación y política de autorización concreta (Fase 2).
- Estrategia de despliegue y observabilidad.
- Forma de distribuir la plantilla como repositorio plantilla o paquete Python.

## 15. Testing de modularidad

`tests/test_modularity.py` verifica:

```python
def test_only_enabled_modules_are_mounted(self):
    client = TestClient(create_app(enabled=["products"]))
    self.assertEqual(client.get("/api/v1/products").status_code, 200)
    self.assertEqual(client.post("/api/v1/llm/ask", json={"prompt": "hola"}).status_code, 404)

def test_unknown_module_fails_fast(self):
    with self.assertRaises(ModuleLoadError):
        create_app(enabled=["no_existe"])

def test_modules_endpoint_lists_enabled(self):
    client = TestClient(create_app(enabled=["llm"]))
    names = [m["name"] for m in client.get("/api/v1/modules").json()]
    self.assertEqual(names, ["llm"])
```

## Arquitectura implementada (Fase 1 completa)

```mermaid
flowchart TD
    CLIENT[Clients HTTP/JSON<br/>Web · móvil · Python · Java · ML] --> MAIN[app/main.py<br/>create_app(enabled=...) + lifespan]
    MAIN --> SYSTEM[app/core/system.py<br/>GET / · /health · /api/v1/modules]
    MAIN --> REGISTRY[app/core/registry.py<br/>resolve + install_modules]
    MAIN -.->|importlib| LLM[app/modules/llm/]
    MAIN -.->|importlib| MEDIA[app/modules/media/]
    MAIN -.->|importlib| PROD[app/modules/products/]

    subgraph LLM_MOD [app/modules/llm/]
        LLM_MAN[manifest.py<br/>ModuleSpec]
        LLM_ROUTER[router.py<br/>POST /ask]
        LLM_SVC[service.py<br/>LLMService]
        LLM_DEPS[deps.py<br/>get_llm_service]
        LLM_ERR[errors.py<br/>502/503/504 handlers]
        LLM_PORTS[ports.py<br/>LLMProvider protocol]
        LLM_SCH[schemas.py<br/>LLMAskRequest/Response]
        LLM_ADAPTS[adapters/__init__.py<br/>build_provider factory]
        LLM_OPENAI[adapters/openai_compatible.py<br/>Chat Completions]
    end

    subgraph MEDIA_MOD [app/modules/media/]
        MEDIA_MAN[manifest.py<br/>ModuleSpec<br/>requires=llm]
        MEDIA_ROUTER[router.py<br/>POST /transcriptions<br/>POST /videos/analyze]
        MEDIA_SVC[service.py<br/>Audio/Video Services]
        MEDIA_DEPS[deps.py<br/>get_audio/video_service]
        MEDIA_ERR[errors.py<br/>413/415/422/502/503/504]
        MEDIA_PORTS[ports.py<br/>Audio/Video/Vision protocols]
        MEDIA_SCH[schemas.py<br/>Media/Video responses]
        MEDIA_FFMPEG[adapters/ffmpeg_video_processor.py]
        MEDIA_AUDIO[adapters/openai_audio.py<br/>/audio/transcriptions]
        MEDIA_VISION[adapters/openai_vision.py<br/>Chat Completions + frames]
    end

    subgraph PROD_MOD [app/modules/products/]
        PROD_MAN[manifest.py<br/>ModuleSpec]
        PROD_ROUTER[router.py<br/>CRUD /products]
        PROD_SVC[service.py<br/>ProductService]
        PROD_DEPS[deps.py<br/>get_product_service]
        PROD_ERR[errors.py<br/>404 handler]
        PROD_REPO[repository.py<br/>ProductRepository protocol]
        PROD_MEM[in_memory_repository.py<br/>InMemoryProductRepository]
        PROD_MODS[models.py<br/>Product/ProductDraft]
        PROD_EXC[exceptions.py<br/>ProductNotFoundError]
        PROD_SCH[schemas.py<br/>ProductCreate/Read/List]
    end

    subgraph CORE [app/core/]
        CORE_CONF[config.py<br/>Settings + enabled_modules_list]
        CORE_MOD[module.py<br/>ModuleSpec dataclass]
        CORE_REG[registry.py<br/>resolve + install_modules]
        CORE_SYS[system.py<br/>system router]
        CORE_SCH[schemas.py<br/>ErrorResponse compartido]
    end

    MEDIA_MOD --> LLM_MOD
    MAIN -.->|lifespan| HTTP_CLIENT[httpx.AsyncClient<br/>shared pool]
    CLIENT -.->|OpenAPI| DOCS[/docs · /openapi.json]

    style CLIENT fill:#1a202c,stroke:#0d1117,color:#f1f5f9
    style MAIN fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style SYSTEM fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style REGISTRY fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style LLM_MOD fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style MEDIA_MOD fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style PROD_MOD fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style CORE fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style HTTP_CLIENT fill:#4a5568,stroke:#2d3748,color:#f1f5f9
```