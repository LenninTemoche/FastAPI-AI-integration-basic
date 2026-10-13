# Criterios de aceptación

Los criterios de las secciones 1–4 se conservan como hitos históricos cerrados según seguimiento del desarrollo del proyecto. Las rutas y los contratos evolucionan en las siguientes secciones: por ejemplo, el endpoint didáctico de validación de la sección 4 se sustituye por el CRUD real en la sección 5. Las casillas de la sección activa solo deben marcarse tras validar localmente.

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

- [x] Crear (`POST`), listar (`GET`), consultar (`GET` por ID), actualizar (`PUT`) y eliminar (`DELETE`).
- [x] Paginación `skip`/`limit` y opción `include_desc`.
- [x] Estados `201`, `200` y `204` documentados.
- [x] Limitación de almacenamiento en memoria documentada.

## F. Sección 6 — manejo de errores HTTP y separación en capas (sección activa)

- [x] F1. CRUD validado localmente después del refactor.
- [x] F2. `ProductService` no importa FastAPI y contiene los casos de uso.
- [x] F3. El dominio define `Product`, `ProductDraft` y `ProductNotFoundError` sin dependencias HTTP.
- [x] F4. El servicio depende del protocolo `ProductRepository`, no de una base de datos concreta.
- [x] F5. La implementación en memoria está fuera de `main.py` y se describe como temporal.
- [x] F6. GET, PUT y DELETE por ID inexistente devuelven `404` con `{"detail": "..."}`.
- [x] F7. La validación automática de FastAPI/Pydantic sigue devolviendo `422`.
- [x] F8. DELETE correcto devuelve `204` sin cuerpo.
- [x] F9. OpenAPI documenta `ErrorResponse` en GET, PUT y DELETE por ID.
- [x] F10. Todas las pruebas automatizadas pasan con `python -m unittest discover -s tests -v`.
- [x] F11. `git diff --check` pasa y se revisa el diff completo.
- [ ] F12. Commit y push manual realizados.

## G. Objetivo global — avance documental pendientes

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
- [ ] G13. Rutas organizadas con `APIRouter` sin cambiar contratos públicos.
- [ ] G14. Servicio, dominio y persistencia desacoplados de la capa HTTP.
- [ ] G15. Integración LLM intercambiable mediante un adaptador; la API key permanece en el backend.
- [ ] G16. Clientes externos integrados por HTTP/JSON con contratos y errores documentados.
- [ ] G17. Autenticación, autorización, límites de consumo y observabilidad cuando el uso lo requiera.
- [ ] G18. Pruebas ampliadas y revisión de seguridad antes de producción.
- [ ] G19. Estrategia de persistencia durable definida y probada si se requiere conservar datos.
- [ ] G20. Docker y despliegue reproducible verificados si forman parte del alcance.

## Condición de cierre de la sección 6

Marcar F1–F12 solo tras instalar/usar el entorno del proyecto, ejecutar las pruebas, probar las rutas en Swagger, revisar cambios y confirmar el commit manual. No declarar la API lista para producción en esta sección.
