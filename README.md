# FastAPI AI Integration Basic

API REST reutilizable con FastAPI, orientada a integraciones con aplicaciones web y móviles mediante HTTP/JSON, servicios Java/Python, proyectos de análisis de datos, modelos de Machine Learning y proveedores de IA generativa.

> **Estado:** secciones 1–7 cerradas según las validaciones realizadas durante el desarrollo. La sección 8 (integración LLM por adaptador y API key) está pendiente. El CRUD demostrativo sigue usando almacenamiento en memoria, y la API aún no está lista para producción.

## Objetivo

Construir una API modular y documentada que pueda integrarse en distintos proyectos mediante HTTP/JSON, manteniendo desacopladas la capa HTTP, la lógica de negocio, la persistencia y las integraciones externas.

## Alcance de la primera versión

- Aplicación REST basada en FastAPI.
- Contratos de entrada y salida definidos mediante Pydantic.
- API versionada bajo `/api/v1`.
- Recurso CRUD demostrativo para aprender y validar los contratos.
- Capa de repositorio que permitan cambiar el almacenamiento, para no acoplar la lógica de negocio a una tecnología concreta.
- Integración LLM mediante un adaptador de proveedor, seleccionado por configuración.
- Autenticación y manejo seguro de secretos antes de exponer servicios a consumidores no confiables.
- Pruebas automatizadas y documentación para consumidores humanos y agentes de programación.

La primera iteración didáctica podrá utilizar almacenamiento en memoria. Eso servirá para aprender, pero no se considerará persistencia apta para producción.No contiene todavía autenticación, persistencia duradera ni integración de IA.

Se utiliza un **monolito modular**: las capas comparten el despliegue inicial, pero exponen responsabilidades e interfaces explícitas. No implica que ya exista una arquitectura de microservicios.

## Arquitectura actual

```mermaid
flowchart TD
    CLIENT[Clients<br/>Web · móvil · Python · Java] --> MAIN[app/main.py<br/>Composición FastAPI<br/>sin rutas CRUD]
    MAIN --> ROOT[app/api/root.py<br/>GET /]
    MAIN --> V1[app/api/v1/router.py<br/>prefijo /api/v1]
    V1 --> PROD[app/api/v1/endpoints/products.py<br/>adaptador HTTP del CRUD]
    PROD --> SVC[app/services/product_service.py<br/>ProductService<br/>Casos de uso]
    SVC --> REPO_PROTO[app/repositories/product_repository.py<br/>ProductRepository<br/>Protocolo]
    REPO_PROTO --> REPO_IMPL[app/repositories/in_memory_product_repository.py<br/>InMemoryProductRepository<br/>Adaptador temporal]

    subgraph DOM["app/domain/"]
        MODELS["models.py<br/>Product / ProductDraft<br/>Sin dependencia HTTP"]
        EXC["exceptions.py<br/>ProductNotFoundError"]
    end

    subgraph CORE["app/core/"]
        DEPS["dependencies.py<br/>Punto de Composición<br/>(servicio + repositorio)"]
        ERR["exception_handlers.py<br/>ProductNotFoundError → HTTP 404<br/>+ ErrorResponse"]
    end

    PROD --> DEPS
    SVC --> MODELS
    SVC --> EXC
    EXC --> ERR
    REPO_IMPL --> MODELS
    REPO_IMPL --> EXC

    style CLIENT fill:#1a202c,stroke:#4a5568,color:#f1f5f9
    style MAIN fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style ROOT fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style V1 fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style PROD fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style SVC fill:#2d3748,stroke:#1a202c,color:#f1f5f9
    style REPO_PROTO fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style REPO_IMPL fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style MODELS fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style EXC fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style ERR fill:#4a5568,stroke:#2d3748,color:#f1f5f9
    style DEPS fill:#4a5568,stroke:#2d3748,color:#f1f5f9
```

La sección 7 separó las rutas HTTP en routers `APIRouter` bajo `app/api/`. La arquitectura completa y las limitaciones están en [`docs/architecture.md`](docs/architecture.md).

## Casos de uso previstos

- Exponer resultados de modelos de Machine Learning por HTTP/JSON.
- Integrar una aplicación React, Angular u otra interfaz web.
- Consumir la API desde una aplicación Java/Spring Boot, Python o móvil.
- Añadir servicios de IA generativa a través de un proveedor configurable.
- Reutilizar la estructura en proyectos de análisis de datos y automatización.

## Tecnologías y entorno

- Python 3.13.
- FastAPI `0.143.0`, instalado con el extra `standard` para disponer del CLI de desarrollo.
- Pydantic 2 (instalado como dependencia de FastAPI; se validará la versión concreta del entorno local).
- Desarrollo local en Windows con PowerShell y VS Code o IDE equivalente.
- `pyproject.toml` registra el punto de entrada `app.main:app` para el CLI y las herramientas compatibles.

La dependencia directa de FastAPI está fijada en `requirements.txt`. Tras validar una instalación limpia conviene guardar la resolución completa de dependencias para mejorar la reproducibilidad.

## Inicio rápido — Windows / PowerShell

Desde la raíz del repositorio:

- py -3.13 -m venv .venv
- .\\.venv\Scripts\Activate.ps1
- python -m pip install --upgrade pip
- python -m pip install -r requirements.txt
- fastapi dev

Si ya existe `.venv`, actívalo y omite el comando de creación.
Guía detallada: [`docs/setup.md`](docs/setup.md).

Direcciones locales:

- `GET /` — estado básico.
- `GET /docs` — Swagger UI.
- `GET /redoc` — ReDoc.
- `GET /openapi.json` — contrato OpenAPI.

Ejecutar pruebas desde la raíz del repositorio:

```powershell
python -m unittest discover -s tests -v
```

Con el servidor activo, abre:

- Inicio: http://127.0.0.1:8000/
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

## Endpoints disponibles



| Método | Ruta                              | Descripción                                     |
| ------- | --------------------------------- | ------------------------------------------------ |
| `GET`   | `/`                               | Estado básico de la API                          |
| `POST`  | `/api/v1/products`              | Crear un producto (`201`)                      |
| `GET`   | `/api/v1/products`              | Listar con `skip`, `limit` e `include_desc` |
| `GET`   | `/api/v1/products/{product_id}` | Consultar por ID                                 |
| `PUT`   | `/api/v1/products/{product_id}` | Actualizar y conservar el ID                     |
| `DELETE`| `/api/v1/products/{product_id}` | Eliminar (`204`, sin cuerpo)                   |

Las rutas versionadas se agrupan mediante `app/api/v1/router.py`. Las operaciones HTTP viven en `app/api/v1/endpoints/products.py`; los casos de uso están en `app/services/product_service.py`, el dominio en `app/domain/` y la persistencia detrás de `ProductRepository`.

Un ID de producto inexistente en GET/PUT/DELETE devuelve `404`:

```json
{
  "detail": "Product with id 999999 not found"
}
```

Las entradas que no cumplen tipos o restricciones siguen devolviendo `422` con los detalles estructurados de FastAPI/Pydantic. El esquema `ErrorResponse` corresponde al error de recurso inexistente; no representa el formato de validación `422`.

#### ¿Por qué un POST repetido genera otro ID?

Cada solicitud válida `POST /api/v1/products` crea un recurso nuevo. Si se envía dos o tres veces el mismo JSON, se obtienen IDs distintos; es el contrato actual de creación, no un error del contador. El API no deduplica por igualdad de campos, porque esos campos no identifican universalmente la identidad de un producto. Consulta `docs/create-and-idempotency-semantics.md` para diferenciar unicidad de negocio e idempotencia de reintentos.

## Capas y directorios clave

- `app/main.py`: capa HTTP; crea la aplicación, instala manejadores de excepciones e incluye routers. No contiene operaciones CRUD.
- `app/api/root.py`: `GET /` de estado básico.
- `app/api/v1/router.py`: router agregador con prefijo `/api/v1`.
- `app/api/v1/endpoints/products.py`: endpoints HTTP del CRUD adaptados a `ProductService`.
- `app/schemas/`: contratos de entrada y salida HTTP.
- `app/domain/`: `Product`, `ProductDraft` y excepciones sin dependencia de FastAPI.
- `app/services/`: casos de uso de producto y regla de recurso inexistente.
- `app/repositories/product_repository.py`: protocolo de persistencia.
- `app/repositories/in_memory_product_repository.py`: implementación demostrativa en memoria.
- `app/core/dependencies.py`: punto para sustituir la implementación de repositorio.
- `app/core/exception_handlers.py`: traducción de la excepción de dominio a la respuesta HTTP documentada.
- `tests/`: pruebas de contrato HTTP y de servicio.

## Limitaciones y seguridad

- El repositorio por defecto es en memoria: los datos desaparecen al reiniciar y no se comparten entre procesos/instancias. No se debe usar como persistencia real.
- No se incluye autenticación, autorización, rate limiting, logging estructurado ni despliegue de producción.
- El proveedor LLM está pendiente. Su credencial deberá permanecer en backend, fuera de Git y fuera de respuestas/logs.
- Los errores controlados no revelan trazas ni secretos. No convertir errores imprevistos en mensajes técnicos públicos.

## Documentación del proyecto

- [Alcance y requisitos del proyecto](docs/project-scope.md)
- [Arquitectura actual](docs/architecture.md)
- [Criterios de aceptación](docs/acceptance-criteria.md)
- [Instalación y primer endpoint](docs/setup.md)
- [Rutas y parámetros](docs/path-and-query-parameters.md)
- [Validación con Pydantic](docs/pydantic-validation.md)
- [CRUD](docs/crud.md)
- [Manejo de errores HTTP y capas](docs/http-errors.md)
- [Modularización con APIRouter](docs/api-routing.md)
- [Creación repetida e idempotencia](docs/create-and-idempotency-semantics.md)
- [Manifiesto de archivos de sección 7](docs/section-07-manifest.md)
- [Reglas para agentes de programación](AGENTS.md)

## Roadmap por secciones

| Sección | Tema                                               | Estado                           |
| -------- | -------------------------------------------------- | -------------------------------- |
| 1        | Introducción, alcance y arquitectura              | Completada                       |
| 2        | Entorno de desarrollo y primer endpoint            | Completada                       |
| 3        | Rutas y parámetros                                | Completada                       |
| 4        | Validación con Pydantic                           | Completada                       |
| 5        | CRUD                                               | Completada                       |
| 6        | Manejo de errores HTTP y separación de capas      | Completada                       |
| 7        | Modularización con `APIRouter`                  | Completada                       |
| 8        | Integración con proveedor LLM mediante API key    | Activa                        |
| 9        | Pruebas, seguridad y preparación para producción | Pendiente                        |

## Flujo de trabajo

1. Implementar únicamente la sección activa.
2. Ejecutar los comandos de validación en el equipo local.
3. Revisar con `git status`, `git diff --check` y `git diff`.
4. Actualizar la documentación para reflejar los resultados reales.
5. Crear manualmente commits acotados y subirlos a GitHub.
6. Avanzar a la siguiente sección después de confirmar el resultado.

## Seguridad y limitaciones

No subir `.venv`, `.env`, tokens, API keys u otras credenciales. La clave del proveedor de IA deberá permanecer en el backend; no será enviada al navegador ni incluida en el control de versiones. La autenticación de consumidores de esta API será una responsabilidad independiente de la credencial del proveedor LLM.

No presentar como lista para producción hasta verificar autenticación, persistencia, límites de consumo, observabilidad, pruebas, despliegue y operación.

## Decisiones iniciales

- Python 3.13 como versión objetivo.
- FastAPI para la capa HTTP.
- Pydantic para contratos y validación de datos.
- HTTPX para llamadas HTTP salientes asíncronas cuando corresponda.
- Arquitectura modular dentro de una sola aplicación; no empezaremos con microservicios.
- Proveedor LLM pendiente de elección; los routers y servicios no deberán depender directamente del SDK de un proveedor.
- Desarrollo local en Windows con VS Code o un IDE equivalente.
- Cambios organizados por sección, con validación local y commits manuales.

La compatibilidad exacta de las dependencias y las versiones se comprobará en la sección 2, antes de fijar el entorno. La documentación actual de FastAPI indica Python 3.10 o superior para el ejemplo mínimo. Consulte las referencias al final de este README.

## Estado y limitaciones

La sección 6 consolida la separación de capas (HTTP, servicios, dominio y protocolo de repositorio con adaptador en memoria) e introduce el manejo desacoplado de errores HTTP (`404` documentado con `ErrorResponse`). Las rutas continúan en `app/main.py` y se modularizarán con `APIRouter` en la sección 7.

El almacenamiento actual en memoria es didáctico y no persiste: los productos se pierden al reiniciar la aplicación o cambiar de proceso. La API aún no está lista para producción; faltan autenticación, configuración segura, persistencia duradera, límites de consumo, observabilidad, pruebas de integración completas y despliegue.

## Referencias oficiales

- [FastAPI — Primeros pasos](https://fastapi.tiangolo.com/tutorial/first-steps/)
- [FastAPI — Entornos virtuales](https://fastapi.tiangolo.com/virtual-environments/)
- [FastAPI en PyPI](https://pypi.org/project/fastapi/)
- [FastAPI es increíble! Apréndelo ahora! gratis!](https://www.youtube.com/watch?v=WrnFtgGLO38)
- [FastAPI — Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Python 3.13 — Entornos virtuales](https://docs.python.org/es/3.13/library/venv.html)
- [HTTPX — Soporte asíncrono](https://www.python-httpx.org/async/)
