# Sección 6 — Manejo de errores HTTP

**Objetivo del proyecto:** una API reutilizable mediante HTTP/JSON que mantenga separadas la capa HTTP, la lógica de aplicación, la persistencia y las integraciones externas.

Esta entrega separa las rutas en `app/api/` mediante routers `APIRouter` (sección 7),
introduce una excepción de dominio, un manejador HTTP, un servicio de productos y un
contrato de repositorio. `app/main.py` se limita a componer la aplicación e instalar los
manejadores de excepciones.

## 1. Qué se separó en esta sección

| Capa | Archivo | Responsabilidad | Dependencia que debe evitar |
|---|---|---|---|
| HTTP | `app/api/v1/endpoints/products.py`, `app/api/root.py` | Rutas, parámetros, validación Pydantic, códigos y respuestas HTTP | No contiene la implementación de persistencia ni las reglas de existencia del producto |
| Router agregador | `app/api/v1/router.py` | Prefijo `/api/v1` y composición de routers de recursos | No contiene operaciones HTTP concretas |
| Composición FastAPI | `app/main.py` | Crea la aplicación, instala manejadores e incluye routers | No contiene lógica CRUD ni rutas por recurso |
| Esquemas HTTP | `app/schemas/product.py`, `app/schemas/errors.py` | Contratos JSON de entrada/salida y documentación OpenAPI | No acceden a repositorios ni llaman proveedores externos |
| Servicio | `app/services/product_service.py` | Casos de uso CRUD y regla de producto inexistente | No importa FastAPI ni construye `Response` |
| Dominio | `app/domain/models.py`, `app/domain/exceptions.py` | Entidad, datos de producto y excepción de dominio | No depende de HTTP, Pydantic ni almacenamiento concreto |
| Contrato de persistencia | `app/repositories/product_repository.py` | Define operaciones que debe ofrecer cualquier repositorio | No elige una base de datos específica |
| Persistencia de ejemplo | `app/repositories/in_memory_product_repository.py` | Implementación temporal en memoria | No se utiliza como almacenamiento de producción |
| Composición y errores HTTP | `app/core/dependencies.py`, `app/core/exception_handlers.py` | Selecciona el servicio y traduce la excepción de dominio a HTTP | No contiene las reglas CRUD del servicio |

## Recorrido de un error de producto inexistente

```text
Solicitud HTTP
  -> app/api/v1/endpoints/products.py
  -> ProductService
  -> ProductNotFoundError (dominio, sin conocimiento de HTTP)
  -> app/core/exception_handlers.py
  -> 404 + {"detail": "Product with id N not found"}
```

`ProductService` no importa FastAPI. `ProductNotFoundError` pertenece al dominio,
mientras que el manejador en `app/core/exception_handlers.py` traduce esa
excepción al formato HTTP público. Se conserva el contrato `{"detail": "..."}`
para no romper clientes creados en secciones anteriores.

## 2. Contrato público de errores

Una solicitud a un producto inexistente recibe:

```http
HTTP/1.1 404 Not Found
Content-Type: application/json
```

```json
{
  "detail": "Product with id 999999 not found"
}
```

Se mantiene el formato `{"detail": "..."}` para no romper los clientes creados durante las secciones anteriores. `ErrorResponse` documenta la forma en OpenAPI; el manejador valida su contenido con Pydantic antes de serializarlo.

## Códigos de respuesta

| Código | Uso |
|---|---|
| `200 OK` | Consulta, listado o actualización correcta. |
| `201 Created` | Producto creado. |
| `204 No Content` | Producto eliminado, sin cuerpo. |
| `404 Not Found` | El ID del producto no existe en el repositorio activo. |
| `405 Method Not Allowed` | Método no admitido por una ruta existente. |
| `422 Unprocessable Entity` | Parámetros o cuerpo no cumplen el contrato. |
| `500 Internal Server Error` | Fallo inesperado; no se deben filtrar trazas ni secretos. |

No se añaden `401`, `403` o `409` de manera artificial; autenticación, autorización
y reglas de conflicto de negocio todavía no forman parte del CRUD de ejemplo.

## 3. Diferencia entre dos errores 404

- **Producto inexistente:** el camino de la ruta existe y el servicio no encuentra el ID. Se responde con `ErrorResponse` y un mensaje identificativo.
- **Ruta inexistente:** FastAPI no encuentra una ruta que coincida, por ejemplo `/ruta-que-no-existe`. Conserva el error estándar `{"detail": "Not Found"}`.

Ambos producen `404`, pero representan situaciones distintas y no se deben confundir.

## 4. Errores de validación 422

No se sobrescribe el manejador predeterminado de validación. De este modo, un cliente recibe los errores estructurados de FastAPI/Pydantic (normalmente `detail` como una lista de fallos), por ejemplo:

- `/api/v1/products/abc`: no se puede convertir `abc` a un entero.
- `/api/v1/products/0`: el identificador debe ser mayor o igual a uno.
- `/api/v1/products?limit=0`: el límite debe estar entre 1 y 100.
- `POST /api/v1/products` con `name="TV"` o con un campo no permitido: `422`.

El cuerpo de error de validación no es `ErrorResponse`, porque `ErrorResponse.detail` es una cadena y el formato estándar de FastAPI utiliza una lista de problemas. Esa diferencia queda deliberadamente documentada.

## 5. Pruebas automatizadas

Se incorporaron pruebas con `unittest` y `TestClient`, sin requerir un framework de pruebas adicional.

Desde la raíz del repositorio, con el entorno `.venv` activado:

```powershell
python -m unittest discover -s tests -v
```

Las pruebas comprueban:

- `404` para GET, PUT y DELETE de un ID inexistente.
- `201`, `200` y `204` en operaciones CRUD correctas, incluido el cuerpo vacío del `204`.
- `422` para parámetros y payloads inválidos.
- Paginación e inclusión/omisión de `description`.
- La referencia de esquema `ErrorResponse` en OpenAPI para las tres operaciones por ID.
- La lógica del servicio sin utilizar un cliente HTTP, demostrando que la regla de producto inexistente no depende de FastAPI.

Para comprobar solo el contrato HTTP:

```powershell
python -m unittest tests.test_http_errors -v
```

Para comprobar solo el servicio:

```powershell
python -m unittest tests.test_product_service -v
```
### Verificación tras la modularización

Los tests de contrato comprueban que `GET`, `PUT` y `DELETE` por ID mantienen su
respuesta 404 documentada en OpenAPI y que `DELETE` correcto devuelve 204 sin
contenido. Ejecutar 

```powershell
python -m unittest discover -s tests -v
```

## 6. Validación manual con Swagger

1. Inicia el servidor con `fastapi dev`.
2. Abre <http://127.0.0.1:8000/docs>.
3. Prueba GET, PUT y DELETE para `/api/v1/products/999999`: los tres deben responder `404` con el contrato `ErrorResponse`.
4. Crea un producto y comprueba GET, PUT y DELETE con el ID retornado.
5. Prueba `/api/v1/products/abc`, `/api/v1/products/0` y `?limit=0`: deben responder `422`.
6. Inspecciona <http://127.0.0.1:8000/openapi.json> y confirma el esquema de las respuestas `404`.

## 7. Límites que permanecen

- La persistencia predeterminada sigue siendo en memoria: se pierde al reiniciar y no se comparte entre procesos o instancias. El bloqueo del repositorio evita colisiones locales del/countador, pero no lo convierte en una base de datos distribuida.
- Esta sección crea el límite servicio/repositorio y el adaptador de errores. Las rutas están en `app/api/` mediante `APIRouter` (sección 7).
- No se incluye autenticación, autorización, rate limiting, observabilidad de producción ni proveedor LLM todavía.
- No se atrapan excepciones genéricas para devolver mensajes técnicos al cliente. Los errores inesperados deben dejarse bajo el control de FastAPI/ASGI y registrarse de manera segura en el entorno de operación.

## Criterios de aceptación de la sección 6

- [ ] El CRUD conserva sus contratos y resultados correctos.
- [ ] El servicio no importa FastAPI y las excepciones de dominio no dependen de HTTP.
- [ ] GET, PUT y DELETE por un ID inexistente devuelven `404` con `ErrorResponse`.
- [ ] Los parámetros y cuerpos inválidos siguen produciendo `422`.
- [ ] `204 No Content` no tiene cuerpo.
- [ ] OpenAPI declara `ErrorResponse` para `404` en las tres operaciones por ID.
- [ ] Las pruebas automatizadas pasan en el entorno del usuario.
- [ ] La arquitectura y sus limitaciones están documentadas y el cambio se revisa antes del commit manual.

## Referencias

- [FastAPI — Manejo de errores](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [FastAPI — Manejo de errores (español)](https://fastapi.tiangolo.com/es/tutorial/handling-errors/)
- [FastAPI — Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pydantic — Models](https://docs.pydantic.dev/latest/concepts/models/)
- [Video de referencia](https://www.youtube.com/watch?v=WrnFtgGLO38)