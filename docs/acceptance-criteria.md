# Criterios de aceptación

Este archivo diferencia los criterios de las secciones implementadas, empezando por la **sección 1** con comprobaciones confirmadas, **sección 2** los criterios de la sección activa y los objetivos finales aún no verificados. A medida que se completen las secciones se irán confirmando los criterios.

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

No se han dado por completados por generar los archivo, verificar localmente y luego marcar los criterios.

- [ ] C1. `GET /` sigue respondiendo `200 OK`.
- [ ] C2. `GET /api/v1/products/25` devuelve el entero `product_id: 25`.
- [ ] C3. `GET /api/v1/products` aplica `limit=10` e `include_desc=false` cuando no se envían parámetros.
- [ ] C4. `GET /api/v1/products?limit=5&include_desc=true` devuelve `limit=5` e `include_desc=true` con sus tipos correspondientes.
- [ ] C5. Un `product_id` no entero produce `422`.
- [ ] C6. Un `limit` no entero produce `422`.
- [ ] C7. Swagger muestra los tres endpoints y documenta los parámetros.
- [ ] C8. La guía `docs/path-and-query-parameters.md` se revisa y los cambios se incluyen en un commit manual.

### Condición para cerrar la sección 3

Confirmar C1–C8 en el entorno local. Los endpoints de productos solo reflejan los parámetros recibidos; no realizan operaciones contra datos reales. La validación de restricciones adicionales se abordará en la sección 4 y el CRUD en la sección 5.

## D. Objetivo final — avnace docmuental

- [ ] D1. Instalación reproducible y dependencias documentadas/bloqueadas.
- [ ] D2. API versionada bajo `/api/v1`.
- [ ] D3. Contratos de entrada/salida con Pydantic y validaciones probadas.
- [ ] D4. CRUD con manejo coherente de errores HTTP.
- [ ] D5. Routers, servicios y repositorios separados.
- [ ] D6. Pruebas automatizadas de rutas, servicios y errores relevantes.
- [ ] D7. Llamadas externas con timeout y tratamiento de fallos.
- [ ] D8. Secretos fuera del control de versiones y de los logs.
- [ ] D9. Proveedor LLM intercambiable mediante un adaptador.
- [ ] D10. Guía de integración desde al menos un cliente externo.
- [ ] D11. Limitaciones de persistencia, rendimiento y despliegue documentadas.
- [ ] D12. Revisión específica de seguridad antes de considerar el despliegue en producción.

