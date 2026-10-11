# Criterios de aceptación

Los criterios de las secciones 1–4 se conservan como hitos históricos cerrados según seguimiento del desarrollo del proyecto. Las rutas y los contratos evolucionan en las siguientes secciones: por ejemplo, el endpoint didáctico de validación de la sección 4 se sustituye por el CRUD real en la sección 5. Las casillas de la sección activa solo deben marcarse tras validar localmente.

## A. Sección 1 — alcance y arquitectura

- [X] A1. El README identifica claramente el propósito y el estado actual del proyecto.
- [X] A2. Se definen objetivos, casos de uso, requisitos funcionales y no funcionales.
- [X] A3. Se documentan explícitamente los temas fuera de alcance.
- [X] A4. La arquitectura se representa en un diagrama y se describen las responsabilidades de cada capa.
- [X] A5. Se aclara que la solución empieza como monolito modular, no como microservicios.
- [X] A6. Python 3.13 queda registrado como versión objetivo, con compatibilidad de dependencias por comprobar en la sección 2.
- [X] A7. El proveedor LLM queda abierto y se establece que su clave permanecerá del lado servidor.
- [X] A8. Se identifica la limitación del almacenamiento en memoria como recurso didáctico, no como persistencia de producción.
- [X] A9. La documentación indica cómo se organizarán las secciones y los avances de forma incremental.
- [X] A10. Se prepara el repositorio documental inicial.

## B. Sección 2 — entorno y primer endpoint

- [X] B1. Instalación reproducible de dependencias en un entorno limpio con Python 3.13.
- [X] B2. El entorno virtual `.venv` se crea en la raíz y está excluido por `.gitignore`.
- [X] B3. `pip install -r requirements.txt` termina sin errores.
- [X] B4. La versión instalada de FastAPI es `0.143.0`.
- [X] B5. La aplicación inicia con `fastapi dev` desde la raíz del repositorio.
- [X] B6. `GET /` responde `200 OK` con JSON de estado.
- [X] B7. Swagger UI en `/docs` muestra y ejecuta `GET /`.
- [X] B8. `/redoc` y `/openapi.json` responden correctamente.
- [X] B9. La documentación refleja los pasos verificados.
- [X] B10. Los cambios se confirmaron mediante commit manual, avance incremental.

## C. Sección 3 — rutas y parámetros

Sección 3 completada y verificada localmente. Las respuestas didácticas se sustituyeron por operaciones CRUD, pero los parámetros y restricciones principales se conservan.

- [X] C1. `GET /` sigue respondiendo `200 OK`.
- [X] C2. `GET /api/v1/products/25` devuelve el entero `product_id: 25`.
- [X] C3. `GET /api/v1/products` aplica `limit=10` e `include_desc=false` por defecto.
- [X] C4. `GET /api/v1/products?limit=5&include_desc=true` devuelve los valores tipados `5` y `true`.
- [X] C5. Un `product_id` no entero produce `422`.
- [X] C6. Un `limit` no entero produce `422`.
- [X] C7. Swagger muestra los tres endpoints y documenta los parámetros.
- [X] C8. La guía se revisó y se subió mediante commit manual.

## D. Sección 4 — validación con Pydantic

Hito cerrado según el flujo de trabajo del proyecto. El endpoint demostrativo `POST /api/v1/products/validate` se retiró deliberadamente en la sección 5; `ProductCreate` se conserva y se aplica al CRUD.

- [X] D1. La API sigue arrancando y `GET /` responde `200 OK`.
- [X] D2. `GET /api/v1/products/25` sigue devolviendo `product_id: 25`.
- [X] D3. `GET /api/v1/products?limit=0` y `limit=101` devuelven `422`.
- [X] D4. `GET /api/v1/products/0` devuelve `422`.
- [X] D5. El payload válido de `POST /api/v1/products/validate` devuelve `200` y `valid: true`.
- [X] D6. `name` con menos de 3 caracteres devuelve `422`.
- [X] D7. `price <= 0`, `stock < 0` y los tipos no válidos devuelven `422`.
- [X] D8. Un campo desconocido devuelve `422`.
- [X] D9. Una descripción de más de 500 caracteres devuelve `422`.
- [X] D10. Swagger muestra el esquema del body y las restricciones de campos.
- [X] D11. `docs/pydantic-validation.md` y este documento se revisan.
- [X] D12. Los cambios pasan `git diff --check`, se revisan y se incluyen en un commit manual.

## E. Sección 5 — CRUD de productos (sección activa)

- [ ] E1. La aplicación inicia y `GET /` mantiene su respuesta.
- [ ] E2. `POST /api/v1/products` devuelve `201 Created`, asigna un ID e incluye la representación del producto.
- [ ] E3. Las entradas inválidas en `POST` y `PUT` devuelven `422`.
- [ ] E4. `GET /api/v1/products` devuelve `total`, `skip`, `limit` e `items`.
- [ ] E5. `skip`, `limit` e `include_desc` funcionan; sus valores inválidos devuelven `422`.
- [ ] E6. `GET /api/v1/products/{product_id}` devuelve un producto existente y `404` para uno inexistente.
- [ ] E7. `PUT /api/v1/products/{product_id}` reemplaza los campos editables; un ID inexistente devuelve `404`.
- [ ] E8. `DELETE /api/v1/products/{product_id}` devuelve `204` sin cuerpo y elimina el producto.
- [ ] E9. Los datos desaparecen al reiniciar la aplicación; la limitación en memoria está documentada.
- [ ] E10. Swagger/OpenAPI expone los cinco métodos del recurso.
- [ ] E11. La guía `docs/crud.md` y el README se revisan.
- [ ] E12. `git diff --check` pasa, los cambios se revisan y se realiza el commit/push manual.

### Condición para cerrar la sección 5

Confirmar E1–E12 en el equipo local. No afirmar que el CRUD tiene persistencia durable: el almacenamiento en memoria es deliberadamente temporal. La sección 6 documenta el contrato de errores `404` y cómo se publica en OpenAPI; sus pruebas locales se registran por separado a continuación.


## F. Sección 6 — manejo de errores HTTP (sección activa)

- [ ] F1. GET, PUT y DELETE por ID devuelven `404` para productos inexistentes.
- [ ] F2. La respuesta `404` usa el formato `{"detail": "..."}`.
- [ ] F3. GET, PUT y DELETE por ID documentan `ErrorResponse` para `404` en OpenAPI.
- [ ] F4. La entrada inválida en path o body mantiene la respuesta `422` de FastAPI.
- [ ] F5. Las operaciones correctas del CRUD conservan sus códigos de éxito (`201`, `200` y `204`).
- [ ] F6. Los mensajes de error no revelan secretos, trazas ni detalles internos.
- [ ] F7. `docs/http-errors.md`, `docs/crud.md` y README están actualizados.
- [ ] F8. `git diff --check` pasa, los cambios se revisan y se realiza el commit/push manual.


## G. Objetivo final — avance documental

- [ ] G1. Instalación reproducible y dependencias documentadas/bloqueadas.
- [ ] G2. API versionada bajo `/api/v1`.
- [ ] G3. Contratos de entrada/salida con Pydantic y validaciones probadas.
- [ ] G4. CRUD funcional con manejo coherente de errores HTTP.
- [ ] G5. Routers, servicios y repositorios separados.
- [ ] G6. Pruebas automatizadas de rutas, servicios y errores relevantes.
- [ ] G7. Llamadas externas con timeout y tratamiento de fallos.
- [ ] G8. Secretos fuera del control de versiones y de los logs.
- [ ] G9. Proveedor LLM intercambiable mediante un adaptador.
- [ ] G10. Guía de integración desde al menos un cliente externo.
- [ ] G11. Limitaciones de persistencia, rendimiento y despliegue documentadas.
- [ ] G12. Revisión específica de seguridad antes de considerar el despliegue en producción.
