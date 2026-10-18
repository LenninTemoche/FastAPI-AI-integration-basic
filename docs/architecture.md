# Arquitectura evolutiva

## Objetivo

Construir una API modular y documentada que se pueda integrar mediante HTTP/JSON en aplicaciones web, móviles, servicios Python/Java, proyectos de análisis de datos, Machine Learning e IA, manteniendo separadas la capa HTTP, la lógica de negocio, la persistencia y las integraciones externas.

## 1. Estilo arquitectónico

La primera versión será un **monolito modular**: una sola aplicación desplegable, organizada en módulos con responsabilidades claras. No se dividirá prematuramente en microservicios.

El objetivo es que la API pueda crecer sin acoplar sus rutas HTTP a la lógica de negocio, al mecanismo de persistencia ni al proveedor de IA.

### Estructura actual

```text
app/
├── main.py                                    # compone FastAPI, lifespan y registra routers
├── api/
│   ├── root.py                                # GET /
│   └── v1/
│       ├── router.py                          # prefijo /api/v1 y agregación de routers
│       ├── endpoints/products.py              # adaptador HTTP del CRUD
│       └── endpoints/llm.py                  # adaptador HTTP de generación de texto
├── core/
│   ├── config.py                              # Settings con SecretStr y validador HTTPS
│   ├── dependencies.py                        # composición de servicio/repositorio/LLM
│   └── exception_handlers.py                 # dominio + errores LLM -> respuesta HTTP
├── domain/
│   ├── models.py                              # Product y ProductDraft
│   └── exceptions.py                          # errores de dominio producto
├── schemas/
│   ├── product.py                             # contratos Pydantic del recurso
│   ├── llm.py                                 # LLMAskRequest / LLMAskResponse
│   └── errors.py                              # contrato de errores HTTP
├── services/
│   ├── product_service.py                     # casos de uso CRUD
│   ├── llm_service.py                         # caso de uso de generación de texto
│   └── ports/llm_provider.py                 # puerto LLMProvider y excepciones de dominio LLM
├── integrations/
│   └── llm/
│       └── openai_compatible.py               # adaptador HTTPX para Chat Completions
└── repositories/
    ├── product_repository.py                  # protocolo de persistencia
    └── in_memory_product_repository.py        # adaptador temporal en memoria
```

## 2. Vista de alto nivel

```mermaid
flowchart TD
    C[Clientes HTTP/JSON<br/>Web · móvil · Java · Python · ML] --> API[FastAPI<br/>routers y versionado]
    API --> SCH[Esquemas Pydantic<br/>contratos y validación]
    API --> SVC[Servicios<br/>casos de uso]
    SVC --> REP[Interfaces/repositorios<br/>acceso a datos]
    REP --> DB[(Almacenamiento<br/>intercambiable)]
    SVC --> LLM_SVC[LLMService<br/>caso de uso]
    LLM_SVC --> LLM_PORT[LLMProvider<br/>puerto/protocolo]
    LLM_PORT --> LLM_ADAPT[OpenAICompatibleChatProvider<br/>adaptador HTTPX]
    LLM_ADAPT --> EXT[Proveedor externo de IA]
    API --> SEC[Configuración y seguridad]

    style C fill:#1a202c,stroke:#0d1117,color:#f1f5f9
    style API fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style SCH fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style SVC fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style REP fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style DB fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style LLM_SVC fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style LLM_PORT fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style LLM_ADAPT fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style EXT fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style SEC fill:#4a5568,stroke:#2d3748,color:#f1f5f9
```

**Arquitectura implementada (secciones 7 y 8):**

```mermaid
flowchart TD
    CLIENT[Clients HTTP/JSON<br/>Web · móvil · Python · Java · ML] --> MAIN[app/main.py<br/>Composición FastAPI<br/>sin rutas CRUD]
    MAIN --> ROOT[app/api/root.py<br/>GET /]
    MAIN --> V1[app/api/v1/router.py<br/>prefijo /api/v1]
    V1 --> PROD[app/api/v1/endpoints/products.py<br/>adaptador HTTP del CRUD]
    V1 --> LLM_EP[app/api/v1/endpoints/llm.py<br/>adaptador HTTP del LLM]
    PROD --> SVC[app/services/product_service.py<br/>ProductService<br/>Casos de uso]
    LLM_EP --> LLM_SVC[app/services/llm_service.py<br/>LLMService<br/>Caso de uso]
    SVC --> REPO_PROTO[app/repositories/product_repository.py<br/>Protocolo ProductRepository]
    REPO_PROTO --> REPO_IMPL[app/repositories/in_memory_product_repository.py<br/>Adaptador temporal]
    LLM_SVC --> LLM_PORT[app/services/ports/llm_provider.py<br/>Puerto LLMProvider]
    LLM_PORT --> LLM_ADAPT[app/integrations/llm/openai_compatible.py<br/>Adaptador OpenAI-compatible]
    LLM_ADAPT --> EXT[Proveedor externo<br/>configurado por entorno]

    subgraph DOM["app/domain/"]
        MODELS["models.py<br/>Product · ProductDraft"]
        EXC["exceptions.py<br/>ProductNotFoundError<br/>(sin dependencia HTTP)"]
    end

    subgraph CORE["app/core/"]
        DEPS["dependencies.py<br/>composición servicio + repositorio"]
        ERR["exception_handlers.py<br/>ProductNotFoundError → HTTP 404<br/>+ ErrorResponse"]
        LLM_ERR["exception_handlers.py<br/>errores LLM → HTTP 502/503/504"]
        CONF["config.py<br/>configuración por entorno + SecretStr"]
    end

    PROD --> DEPS
    SVC --> MODELS
    SVC --> EXC
    EXC --> ERR
    REPO_IMPL --> MODELS
    REPO_IMPL --> EXC

    LLM_EP --> DEPS
    LLM_SVC --> CONF
    LLM_ADAPT --> CONF

    style CLIENT fill:#1a202c,stroke:#0d1117,color:#f1f5f9
    style MAIN fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style ROOT fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style V1 fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style PROD fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style LLM_EP fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style SVC fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style LLM_SVC fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style REPO_PROTO fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style REPO_IMPL fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style LLM_PORT fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style LLM_ADAPT fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style EXT fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style MODELS fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style EXC fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style DEPS fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style ERR fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style LLM_ERR fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style CONF fill:#4a5568,stroke:#2d3748,color:#f1f5f9
```

### Responsabilidades y dirección de dependencias

| Capa                           | Responsabilidad                                                                                          | No debe depender de                        |
| ------------------------------ | -------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| `main.py`                    | Crear la aplicación, registrar excepciones e incluir routers                                            | Lógica CRUD concreta                      |
| `app/api/`                   | Routers HTTP (root + v1 + endpoints). Traduce HTTP/JSON a llamadas de servicio y resultados a respuestas | Implementación directa de almacenamiento  |
| `schemas/`                   | Validar solicitudes y definir contratos públicos                                                        | Servicio y persistencia                    |
| `services/`                  | Coordinar casos de uso y reglas de aplicación                                                           | FastAPI, `Response` o SDK de proveedores |
| `domain/`                    | Modelos y excepciones centrales del dominio                                                              | FastAPI, Pydantic y tecnología de datos   |
| `repositories/`              | Contrato y adaptadores de persistencia                                                                   | Rutas HTTP                                 |
| `core/dependencies.py`       | Elegir y entregar implementaciones a la aplicación                                                      | Reglas de negocio                          |
| `core/config.py`             | Cargar y validar variables de entorno, tratando secretos como `SecretStr`                              | Reglas de negocio                          |
| `core/exception_handlers.py` | Traducir errores internos a respuestas HTTP conocidas sin filtrar contenido externo                      | Implementación concreta de proveedores    |
| `integrations/llm/`          | Adaptadores concretos para APIs externas                                                                 | Contratos HTTP públicos del proyecto      |

## Cómo se conectan los routers

`app/main.py` incluye `app.api.root.router` para `GET /` y
`app/api.v1.router.router` para la API versionada. El router v1 aplica `/api/v1`
y agrega los routers de los recursos productos (`/products`) y LLM (`/llm`).
Esta composición conserva los paths publicados.

- `app/api/root.py`: define `GET /` con una respuesta de estado básica.
- `app/api/v1/router.py`: router agregador con prefijo `/api/v1` que incluye
  `app/api/v1/endpoints/products.py` y `app/api/v1/endpoints/llm.py`.
- `app/api/v1/endpoints/products.py`: contiene las operaciones CRUD HTTP
  adaptadas a `ProductService`.
- `app/api/v1/endpoints/llm.py`: contiene la operación HTTP para generación
  de texto, adaptada a `LLMService`.

Para añadir un recurso futuro, se creará otro módulo bajo
`app/api/v1/endpoints/` y se incluirá su router en `app/api/v1/router.py`. Evitar
declarar una misma ruta en más de un módulo.

## Endpoints raíz y versiones

- `GET /`: informa del propósito de la API y enlaza a `/docs`.
- `GET /api/v1/`: redirige a `/api/v1/docs` sin repetir la descripción del servicio.

## Contracts, excepciones y transformaciones

- `schemas/product.py` define los contratos de entrada y salida para el recurso producto.
- `app/domain/exceptions.py` define las excepciones de dominio (ej. `ProductNotFoundError`), que no contienen lógica HTTP.
- `app/core/exception_handlers.py` transforma excepciones de dominio en respuestas HTTP (ej. `ProductNotFoundError → 404 + ErrorResponse`).

Esta separación mantiene los dominios y servicios agnósticos a HTTP. Los endpoints
HTTP (`app/api/v1/endpoints/products.py`) no tratan excepciones de dominio directamente;
las dejan al manejador registrado en `app/main.py`.

## Persistencia, servicios y composición

- `app/services/product_service.py` implementa los casos de uso y coordina repositorio y otros adaptadores.
- `app/repositories/` contiene el protocolo `ProductRepository` y su implementación en memoria.
- `app/core/dependencies.py` une servicio y repositorio para inyección de dependencias en los endpoints.
- `app/api/v1/endpoints/products.py` adapta HTTP/JSON a `ProductService` mediante `Depends(get_product_service)`.

El servicio no conoce detalles de persistencia y el endpoint solo interactúa con el servicio, lo que facilita el intercambio de mecanismos de almacenamiento.

### Duplicados y reintentos

El CRUD didáctico no deduplica un POST por igualdad de contenido. La decisión está
documentada en `docs/create-and-idempotency-semantics.md`. La unicidad de negocio
y una futura clave de idempotencia deben aplicarse en las capas apropiadas y no
introducirse como lógica improvisada en los endpoints.

## 3. Responsabilidades por capa

### Capa HTTP: `app/api/`

- `app/api/root.py`: define `GET /` con una respuesta de estado básica.
- `app/api/v1/router.py`: router agregador con prefijo `/api/v1` que incluye los routers de los recursos.
- `app/api/v1/endpoints/products.py`: adaptador HTTP del CRUD, traduce solicitudes y respuestas a/from `ProductService`.
- Declara rutas, métodos HTTP, parámetros y códigos de respuesta.
- Mantiene el versionado público, inicialmente `/api/v1`.
- No debe contener lógica de negocio extensa ni acceder directamente a la base de datos.

### Contratos: `schemas/`

- Define modelos de solicitud y respuesta con Pydantic.
- Expresa campos obligatorios, OPTIONALES, límites y formatos.
- Evita devolver objetos internos arbitrarios como contrato público.
- No almacena secretos ni realiza llamadas externas.

### Lógica de negocio: `services/`

- Implementa casos de uso y reglas de negocio.
- Coordina repositorios y adaptadores.
- Puede probarse sin iniciar un servidor HTTP.
- No debe depender directamente de un framework web cuando una abstracción sencilla sea suficiente.

### Persistencia: `repositories/`

- Define cómo se consulta o modifica el estado persistente.
- La implementación en memoria, si se usa para la fase didáctica, será una implementación temporal.
- El servicio no debe depender de detalles específicos de una base de datos.
- La persistencia duradera y sus migraciones quedan para una etapa posterior.

### Integraciones externas: `integrations/`

- Encapsula las llamadas HTTP o SDK a proveedores externos.
- Define una frontera estable para el proveedor LLM.
- Configura timeout y tratamiento de errores de red.
- Evita que los nombres de modelos, esquemas de SDK o formatos internos del proveedor se filtren innecesariamente al contrato público.

### Configuración y seguridad: `core/`

- Centraliza configuración a partir de variables de entorno.
- Distingue configuración local de secretos.
- Aloja dependencias comunes de seguridad cuando se implementen.
- No debe incluir claves reales en código, ejemplos ni logs.

### Extensión de Machine Learning: `ml/` (futura y opcional)

- Podrá cargar artefactos de modelos existentes y exponer inferencia.
- Mantendrá separadas las dependencias pesadas de ML de los módulos básicos de la API cuando sea viable.
- No forma parte de la implementación de la sección 1.

## 4. Flujo de una solicitud

1. Un consumidor envía una solicitud HTTP/JSON.
2. FastAPI identifica la ruta y procesa parámetros y dependencias.
3. Pydantic valida la estructura de entrada.
4. El router delega el caso de uso a un servicio.
5. El servicio usa un repositorio o adaptador externo según sea necesario.
6. El resultado se convierte a un esquema de respuesta documentado.
7. La API devuelve el código HTTP y el cuerpo definidos en el contrato.

## 5. Persistencia

`ProductService` depende del protocolo `ProductRepository`, no del `InMemoryProductRepository`. Para incorporar SQL u otro almacenamiento, se implementa el protocolo y se cambia el enlace en `app/core/dependencies.py`. No se deben introducir consultas a la base de datos directamente en los endpoints.

La implementación actual guarda datos en memoria del proceso. No es durable, no sincroniza distintas instancias y solo sirve para desarrollo y aprendizaje.

## 6. Integración HTTP/JSON

Los esquemas Pydantic forman el contrato externo. Los clientes no deberían depender de clases Python internas ni de la implementación del repositorio. Cambios en esas capas deben preservar los endpoints, los códigos HTTP y la forma de respuesta, o documentarse como una evolución incompatible.

## 7. Decisión sobre LLM

El proveedor por defecto es `openai_compatible`, seleccionable mediante la variable
`LLM_PROVIDER`. El diseño permite elegirlo desde configuración y, si se requiere un
protocolo distinto, añadir un nuevo adaptador que implemente `LLMProvider` sin
modificar el endpoint ni el caso de uso.

La clave del proveedor se mantendrá en el backend. No se enviará al navegador, a
aplicaciones móviles ni a los clientes que consuman esta API. La autenticación de
los consumidores de nuestra API es una responsabilidad independiente de la
credencial del proveedor.

Ver la implementación completa en la sección [8. Integración LLM](#8-integración-llm-mediante-adaptador-sección-8) más abajo.

## 9. Errores y contratos

- Los errores de validación se expondrán mediante respuestas coherentes con FastAPI y su contrato OpenAPI.
- Los recursos inexistentes devolverán `404` cuando aplique.
- Los errores de autenticación y autorización se distinguirán (`401` y `403`).
- Los conflictos del estado del recurso podrán usar `409`.
- Los fallos inesperados no expondrán trazas, secretos ni detalles internos al consumidor.
- El formato común de errores se definirá durante la implementación, evitando prometer uniformidad antes de probarla.

## 10. Versionado y compatibilidad

La API pública comenzará bajo `/api/v1`. Los cambios compatibles podrán añadirse dentro de la versión actual; los cambios incompatibles exigirán una estrategia explícita de migración y una versión nueva cuando corresponda.

## 11. Decisiones aún abiertas

- Gestor de dependencias y formato de bloqueo.
- Almacenamiento persistente definitivo.
- Mecanismo de autenticación y política de autorización concreta.
- Estrategia de despliegue y observabilidad.
- Forma de distribuir la plantilla como repositorio plantilla o paquete Python.

## 8. Integración LLM mediante adaptador (sección 8)

La API expone una operación de generación de texto reutilizable por HTTP/JSON sin
acoplar endpoints ni casos de uso a un proveedor comercial específico. El diseño
sigue la arquitectura de puertos y adaptadores:

- `app/services/ports/llm_provider.py`: puerto neutral `LLMProvider` y tipos de
  error de integración (`LLMError`, `LLMNotConfiguredError`,
  `LLMProviderTimeoutError`, `LLMProviderRateLimitError`,
  `LLMProviderUnavailableError`, `LLMProviderResponseError`). No importa FastAPI
  ni HTTPX.
- `app/services/llm_service.py`: caso de uso que inyecta un `LLMProvider` y
  devuelve un resultado neutral (`LLMGenerationResult`).
- `app/api/v1/endpoints/llm.py`: adaptador HTTP que traduce `LLMAskRequest` en una
  llamada al servicio y normaliza la respuesta a `LLMAskResponse`.
- `app/integrations/llm/openai_compatible.py`: adaptador concreto para proveedores
  compatibles con OpenAI Chat Completions, usando HTTPX asíncrono y autenticación
  Bearer con la clave cargada desde el servidor.
- `app/core/config.py`: carga y valida variables de entorno (`LLM_API_KEY`,
  `LLM_BASE_URL`, `LLM_MODEL`, etc.) tratando la API key como `SecretStr`.
- `app/core/dependencies.py`: compone el servicio LLM y selecciona el adaptador
  por configuración.
- `app/core/exception_handlers.py`: traduce errores del dominio LLM a respuestas
  HTTP 503/504/502 sin exponer credenciales ni cuerpos de error externos.

### Flujo de la solicitud LLM

1. FastAPI valida el JSON como `LLMAskRequest`.
2. El endpoint depende de `LLMService`, sin conocer URLs, API keys ni librerías
   de proveedor.
3. `LLMService` invoca el contrato `LLMProvider`.
4. `OpenAICompatibleChatProvider` prepara la solicitud HTTP y usa el
   `AsyncClient` compartido del lifespan.
5. El adaptador normaliza texto/modelo/uso a `LLMGenerationResult`.
6. El endpoint devuelve `LLMAskResponse`; los fallos conocidos se convierten a
   `ErrorResponse` con estado 502/503/504.

### Cómo incorporar otro proveedor

Si el nuevo proveedor es compatible con el mismo contrato Chat Completions, se
pueden cambiar base URL, credencial y modelo mediante entorno. Si el protocolo es
distinto, crear una implementación nueva de `LLMProvider` bajo
`app/integrations/llm/` y añadir su selección al punto de composición.
Mantener estable `LLMService`, `LLMAskRequest` y `LLMAskResponse` siempre que la
funcionalidad sea equivalente.

### Limitaciones actuales

- El CRUD usa memoria y pierde datos al reiniciar; no equivale a persistencia de
  producción.
- LLM se implementa como una petición de una sola interacción; no hay historial
  ni streaming.
- La llamada externa no tiene reintentos automáticos.
- La API no incorpora todavía autenticación/autorización para consumidores, rate
  limiting ni cuotas.
- La sección 9 debe revisar seguridad, pruebas completas,
  logging/observabilidad, empaquetado y despliegue.

## Arquitectura implementada (secciones 7 y 8)

```mermaid
flowchart TD
    CLIENT[Clients HTTP/JSON<br/>Web · móvil · Python · Java · ML] --> MAIN[app/main.py<br/>Composición FastAPI<br/>sin rutas CRUD]
    MAIN --> ROOT[app/api/root.py<br/>GET /]
    MAIN --> V1[app/api/v1/router.py<br/>prefijo /api/v1]
    V1 --> PROD[app/api/v1/endpoints/products.py<br/>adaptador HTTP del CRUD]
    V1 --> LLM_EP[app/api/v1/endpoints/llm.py<br/>adaptador HTTP del LLM]
    PROD --> SVC[app/services/product_service.py<br/>ProductService<br/>Casos de uso]
    LLM_EP --> LLM_SVC[app/services/llm_service.py<br/>LLMService<br/>Caso de uso]
    SVC --> REPO_PROTO[app/repositories/product_repository.py<br/>Protocolo ProductRepository]
    REPO_PROTO --> REPO_IMPL[app/repositories/in_memory_product_repository.py<br/>Adaptador temporal]
    LLM_SVC --> LLM_PORT[app/services/ports/llm_provider.py<br/>Puerto LLMProvider]
    LLM_PORT --> LLM_ADAPT[app/integrations/llm/openai_compatible.py<br/>Adaptador OpenAI-compatible]
    LLM_ADAPT --> EXT[Proveedor externo<br/>configurado por entorno]

    subgraph DOM["app/domain/"]
        MODELS["models.py<br/>Product · ProductDraft"]
        EXC["exceptions.py<br/>ProductNotFoundError<br/>(sin dependencia HTTP)"]
    end

    subgraph CORE["app/core/"]
        DEPS["dependencies.py<br/>composición servicio + repositorio"]
        ERR["exception_handlers.py<br/>ProductNotFoundError → HTTP 404<br/>+ ErrorResponse"]
        LLM_ERR["exception_handlers.py<br/>errores LLM → HTTP 502/503/504"]
        CONF["config.py<br/>configuración por entorno + SecretStr"]
    end

    PROD --> DEPS
    SVC --> MODELS
    SVC --> EXC
    EXC --> ERR
    REPO_IMPL --> MODELS
    REPO_IMPL --> EXC

    LLM_EP --> DEPS
    LLM_SVC --> CONF
    LLM_SVC --> LLM_PORT
    LLM_ADAPT --> CONF

    style CLIENT fill:#1a202c,stroke:#0d1117,color:#f1f5f9
    style MAIN fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style ROOT fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style V1 fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style PROD fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style LLM_EP fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style SVC fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style LLM_SVC fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style REPO_PROTO fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style REPO_IMPL fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style LLM_PORT fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style LLM_ADAPT fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style EXT fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style MODELS fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style EXC fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style DEPS fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style ERR fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style LLM_ERR fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style CONF fill:#4a5568,stroke:#2d3748,color:#f1f5f9
```

### Responsabilidades y dirección de dependencias

| Capa                           | Responsabilidad                                                                                          | No debe depender de                        |
| ------------------------------ | -------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| `main.py`                    | Crear la aplicación, registrar excepciones e incluir routers                                            | Lógica CRUD concreta                      |
| `app/api/`                   | Routers HTTP (root + v1 + endpoints). Traduce HTTP/JSON a llamadas de servicio y resultados a respuestas | Implementación directa de almacenamiento  |
| `schemas/`                   | Validar solicitudes y definir contratos públicos                                                        | Servicio y persistencia                    |
| `services/`                  | Coordinar casos de uso y reglas de aplicación                                                           | FastAPI, `Response` o SDK de proveedores |
| `domain/`                    | Modelos y excepciones centrales del dominio                                                              | FastAPI, Pydantic y tecnología de datos   |
| `repositories/`              | Contrato y adaptadores de persistencia                                                                   | Rutas HTTP                                 |
| `core/dependencies.py`       | Elegir y entregar implementaciones a la aplicación                                                      | Reglas de negocio                          |
| `core/config.py`             | Cargar y validar variables de entorno, tratando secretos como `SecretStr`                              | Reglas de negocio                          |
| `core/exception_handlers.py` | Traducir errores internos a respuestas HTTP conocidas sin filtrar contenido externo                      | Implementación concreta de proveedores    |
| `integrations/llm/`          | Adaptadores concretos para APIs externas                                                                 | Contratos HTTP públicos del proyecto      |

### Cómo se conectan los routers

`app/main.py` incluye `app.api.root.router` para `GET /` y
`app/api.v1.router.router` para la API versionada. El router v1 aplica `/api/v1`
y agrega los routers de los recursos productos (`/products`) y LLM (`/llm`).
Esta composición conserva los paths publicados.

- `app/api/root.py`: define `GET /` con una respuesta de estado básica.
- `app/api/v1/router.py`: router agregador con prefijo `/api/v1` que incluye
  `app/api/v1/endpoints/products.py` y `app/api/v1/endpoints/llm.py`.
- `app/api/v1/endpoints/products.py`: contiene las operaciones CRUD HTTP
  adaptadas a `ProductService`.
- `app/api/v1/endpoints/llm.py`: contiene la operación HTTP para generación
  de texto, adaptada a `LLMService`.

Para añadir un recurso futuro, se creará otro módulo bajo
`app/api/v1/endpoints/` y se incluirá su router en `app/api/v1/router.py`. Evitar
declarar una misma ruta en más de un módulo.

### Endpoints raíz y versiones

- `GET /`: informa del propósito de la API y enlaza a `/docs`.
- `GET /api/v1/`: redirige a `/api/v1/docs` sin repetir la descripción del servicio.

### Contracts, excepciones y transformaciones

- `schemas/product.py` define los contratos de entrada y salida para el recurso producto.
- `schemas/llm.py` define los contratos de solicitud y respuesta para generación de texto.
- `app/domain/exceptions.py` define las excepciones de dominio (ej. `ProductNotFoundError`), que no contienen lógica HTTP.
- `app/core/exception_handlers.py` transforma excepciones de dominio y del dominio LLM en respuestas HTTP (ej. `ProductNotFoundError → 404 + ErrorResponse`; errores LLM → 502/503/504).

Esta separación mantiene los dominios y servicios agnósticos a HTTP. Los endpoints
HTTP no tratan excepciones de dominio directamente; las dejan al manejador registrado en `app/main.py`.

### Persistencia, servicios y composición

- `app/services/product_service.py` implementa los casos de uso y coordina repositorio y otros adaptadores.
- `app/services/llm_service.py` implementa el caso de uso de generación de texto y coordina el puerto `LLMProvider`.
- `app/repositories/` contiene el protocolo `ProductRepository` y su implementación en memoria.
- `app/core/dependencies.py` une servicio y repositorio para inyección de dependencias en los endpoints.
- `app/api/v1/endpoints/products.py` adapta HTTP/JSON a `ProductService` mediante `Depends(get_product_service)`.
- `app/api/v1/endpoints/llm.py` adapta HTTP/JSON a `LLMService` mediante `Depends(get_llm_service)`.

El servicio no conoce detalles de persistencia y el endpoint solo interactúa con el servicio, lo que facilita el intercambio de mecanismos de almacenamiento.
