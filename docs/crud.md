# Sección 5 — CRUD de productos

Extensión del alcance CRUD para incluir actualización.

Esta sección sustituye las respuestas didácticas de la sección 3 por operaciones reales sobre un pequeño almacén en memoria. Reutiliza Pydantic para validar entradas y describir respuestas.

> **Limitación importante:** el almacén vive en la memoria del proceso. Los datos se pierden al reiniciar la aplicación o recargar el servidor de desarrollo. Tampoco se comparte entre procesos o instancias. Esto permite aprender el contrato REST, pero no es persistencia adecuada para producción.

## 1. Endpoints

| Método    | Ruta                              | Función                            | Respuesta normal                  |
| ---------- | --------------------------------- | ----------------------------------- | --------------------------------- |
| `POST`   | `/api/v1/products`              | Crear un producto y asignarle un ID | `201 Created` + producto        |
| `GET`    | `/api/v1/products`              | Listar productos con paginación    | `200 OK` + listado              |
| `GET`    | `/api/v1/products/{product_id}` | Consultar un producto               | `200 OK` + producto             |
| `PUT`    | `/api/v1/products/{product_id}` | Reemplazar los campos editables     | `200 OK` + producto actualizado |
| `DELETE` | `/api/v1/products/{product_id}` | Eliminar un producto                | `204 No Content`                |

Para un ID positivo que no existe, las operaciones de consulta, actualización y eliminación devuelven `404 Not Found`. Este comportamiento mínimo es necesario para que el CRUD sea utilizable; el tratamiento de errores HTTP se revisará de forma más amplia en la sección 6.

## 2. Esquema de entrada

`ProductCreate` se declara en `app/schemas/product.py` y se usa tanto para crear como para actualizar completamente los campos editables:

| Campo           | Regla                                                                      |
| --------------- | -------------------------------------------------------------------------- |
| `name`        | Obligatorio, entre 3 y 100 caracteres después de quitar espacios externos |
| `price`       | Obligatorio, mayor que cero; no admite`NaN` ni infinito                  |
| `stock`       | Obligatorio, entero mayor o igual que cero                                 |
| `description` | Opcional, hasta 500 caracteres; valor por defecto`null`                  |

Los campos no declarados se rechazan. Los errores de validación predeterminados de FastAPI son `422 Unprocessable Entity`.

## 3. Crear un producto

En Swagger UI, ejecuta `POST /api/v1/products` con:

```json
{
  "name": "Router Wi-Fi",
  "price": 129.9,
  "stock": 15,
  "description": "Router de doble banda"
}
```

Resultado esperado: `201 Created` y un producto con ID asignado por el servidor. En una aplicación recién iniciada, normalmente será `1`.

Ejemplo de respuesta (el orden de las propiedades JSON no es significativo):

```json
{
  "name": "Router Wi-Fi",
  "price": 129.9,
  "stock": 15,
  "description": "Router de doble banda",
  "id": 1
}
```

Crea un segundo producto para practicar paginación.

## 4. Listar productos y paginar

- `GET /api/v1/products`: `skip=0`, `limit=10`, `include_desc=false` por defecto.
- `GET /api/v1/products?skip=0&limit=1`: devuelve como máximo un elemento.
- `GET /api/v1/products?skip=1&limit=10&include_desc=true`: omite el primer producto e incluye su descripción en cada elemento.

La respuesta incluye `total`, `skip`, `limit` e `items`. `total` corresponde al total de productos disponibles antes de aplicar la paginación. `limit` debe estar entre 1 y 100; `skip` debe ser cero o mayor. Los valores fuera de rango devuelven `422`.

Cuando `include_desc=false`, el campo `description` se omite de los elementos del listado. La consulta individual siempre devuelve la representación completa, incluida `description` cuando corresponda.

## 5. Consultar, actualizar y eliminar

Usa el ID devuelto por el `POST` anterior (no supongas que siempre será 1 si ya creaste productos durante esta ejecución).

### Consultar

`GET /api/v1/products/1` devuelve el producto con ese ID. Si no existe, responde `404`.

### Actualizar con PUT

`PUT /api/v1/products/1` recibe el conjunto completo de campos editables:

```json
{
  "name": "Router Wi-Fi Pro",
  "price": 159.9,
  "stock": 12,
  "description": "Modelo actualizado de doble banda"
}
```

`PUT` reemplaza los campos editables. Si no se envía `description`, su valor se restablece a `null`. Si se requiere actualización parcial, se diseñará un `PATCH` separado más adelante; no se mezclan aquí las dos semánticas.

### Eliminar

`DELETE /api/v1/products/1` devuelve `204 No Content` sin cuerpo. Una consulta posterior al mismo ID devuelve `404`.

## 6. Validación manual en Swagger UI

1. Inicia la API desde la raíz del repositorio: `fastapi dev`.
2. Abre [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
3. Crea dos productos con `POST` y guarda los IDs de las respuestas.
4. Comprueba el listado normal, la paginación y `include_desc=true`.
5. Consulta uno de los IDs, actualízalo con `PUT` y confirma el cambio con `GET`.
6. Elimina el segundo producto y confirma que la respuesta sea `204`.
7. Prueba un ID válido que no exista con `GET`, `PUT` y `DELETE`: cada operación debe devolver `404`.
8. Envía un nombre demasiado corto o un precio cero a `POST` o `PUT`: debe devolver `422`.
9. Prueba `GET /api/v1/products?limit=0`, `limit=101` y `skip=-1`: cada uno debe devolver `422`.
10. Reinicia la aplicación para comprobar la limitación didáctica: los productos en memoria ya no estarán.

## 7. Qué no se incluye todavía

- Base de datos o almacenamiento persistente.
- Separación de rutas con `APIRouter`, servicios y repositorios; corresponde a la sección 7.
- Manejadores globales o formato estandarizado de errores; corresponde a la sección 6. El `404` de recurso inexistente es la respuesta mínima necesaria del CRUD.
- Autenticación, autorización o integración con LLM.
- Pruebas automatizadas completas, Docker o despliegue a producción.

## Criterios de aceptación

- [ ] La API inicia y `GET /` mantiene su respuesta.
- [ ] `POST /api/v1/products` devuelve `201`, un ID y un objeto conforme a `ProductRead`.
- [ ] El payload inválido devuelve `422`.
- [ ] `GET /api/v1/products` devuelve un listado con `total`, `skip`, `limit` e `items`.
- [ ] `skip`, `limit` e `include_desc` funcionan; los valores fuera de rango devuelven `422`.
- [ ] `include_desc=false` omite `description`; `true` la incluye.
- [ ] `GET /api/v1/products/{id}` obtiene un producto existente y devuelve `404` para uno inexistente.
- [ ] `PUT /api/v1/products/{id}` reemplaza los campos de un producto existente y devuelve `404` para uno inexistente.
- [ ] `DELETE /api/v1/products/{id}` devuelve `204` sin cuerpo y elimina el registro; ID inexistente devuelve `404`.
- [ ] Swagger/OpenAPI documenta todos los métodos y sus esquemas.
- [ ] La limitación de almacenamiento en memoria queda explicada en README y esta guía.
- [ ] Se revisan los cambios y se realiza commit/push manual solo después de validar localmente.

## Referencias oficiales

- [FastAPI — Body / Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- [FastAPI — Response Status Code](https://fastapi.tiangolo.com/tutorial/response-status-code/)
- [FastAPI — Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)
- [FastAPI — Query Parameters](https://fastapi.tiangolo.com/tutorial/query-params/)
- [Pydantic — Fields](https://docs.pydantic.dev/latest/concepts/fields/)
- [Video de referencia](https://www.youtube.com/watch?v=WrnFtgGLO38)
