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
- [x] B4. La versión instalada de FastAPI es `0.143.0`.
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

**En las secciones siguientes se trabajará en la separación de capas y la integración con IA**

## F. Sección 6 — manejo de errores HTTP y separación en capas 

- [x] F1 El servicio no importa FastAPI y las entidades de dominio no dependen de HTTP.
- [x] F2 El servicio depende del protocolo `ProductRepository`.
- [x] F3 GET/PUT/DELETE por ID inexistente devuelven `404` con formato `{"detail":"..."}`.
- [x] F4 Validaciones siguen devolviendo `422`; DELETE correcto devuelve `204` sin cuerpo.
- [x] F5 Se documenta `ErrorResponse` en OpenAPI.


## Sección 7 — modularización con APIRouter (activa)

- [ ] G1 `app/main.py` solo compone la aplicación, maneja el registro de routers y los manejadores HTTP.
- [ ] G2 `GET /` se conserva en un router general.
- [ ] G3 El CRUD se mueve a `app/api/v1/endpoints/products.py`.
- [ ] G4 `app/api/v1/router.py` agrega routers bajo `/api/v1`.
- [ ] G5 Se conservan exactamente los métodos y paths públicos existentes.
- [ ] G6 Se conservan respuestas 200, 201, 204, 404 y 422, esquemas y parámetros.
- [ ] G7 Swagger/OpenAPI enumera cada endpoint solo una vez y mantiene el esquema `ErrorResponse` para los 404.
- [ ] G8 Las pruebas existentes y `tests/test_product_create_semantics.py` pasan.
- [ ] G9 Dos POST con payloads idénticos crean dos recursos con IDs distintos; este contrato está documentado, no se trata como deduplicación.
- [ ] G10 `docs/api-routing.md`, `docs/create-and-idempotency-semantics.md` y referencias relacionadas están actualizadas.
- [ ] G11 `git diff --check` pasa, el diff revisado y el commit/push manual queda realizado.


## Objetivos globales pendientes

- [ ] H1 Proveedor LLM desacoplado detrás de un adaptador, llamado mediante API key en el servidor.
- [ ] H2 Autenticación de consumidores, límites de consumo y secretos gestionados correctamente.
- [ ] H3 Persistencia durable y configuración por entorno.
- [ ] H4 Pruebas de integración para llamadas externas, timeout y errores del proveedor.
- [ ] H5 Documentación de integración para Python, Java/Spring Boot y clientes web.
- [ ] H6 Preparación para Docker, CI y despliegue.

## Condición de cierre de la sección 7

Marcar G1-G11 solo tras revisar cambios y confirmar funcionalidad de modularización y que no hayan errores. No declarar la API lista para producción en esta sección.
