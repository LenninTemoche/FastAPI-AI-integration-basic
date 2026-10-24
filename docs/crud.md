# Sección 5 — CRUD de productos

Extensión del alcance CRUD para incluir actualización.

Esta guía describe el contrato CRUD que se mantiene después de la separación de
rutas realizada en la sección 7. Los endpoints HTTP viven ahora en
`app/modules/products/router.py`; el registro lo gestiona `app/core/registry.py`.
La lógica permanece en `ProductService` y el almacenamiento detrás de
`ProductRepository`.


> **Limitación importante:** el almacén vive en la memoria del proceso. Los datos se pierden al reiniciar la aplicación o recargar el servidor de desarrollo. Tampoco se comparte entre procesos o instancias. Esto permite aprender el contrato REST, es una implementación didáctica, no persistencia de producción.


## 1. Endpoints

| Método | Ruta | Éxito | Errores habituales |
|---|---|---|---|
| POST | `/api/v1/products` | `201 Created` + producto | `422` si el body no es válido |
| GET | `/api/v1/products` | `200 OK` + lista paginada | `422` si `skip`/`limit` no es válido |
| GET | `/api/v1/products/{product_id}` | `200 OK` + producto | `404` si no existe; `422` si ID inválido |
| PUT | `/api/v1/products/{product_id}` | `200 OK` + producto actualizado | `404` si no existe; `422` si body/ID inválido |
| DELETE | `/api/v1/products/{product_id}` | `204 No Content`, sin body | `404` si no existe; `422` si ID inválido |


## 2. Esquema de entrada

`ProductCreate` se declara en `app/modules/products/schemas.py` y se usa tanto para crear como para actualizar completamente los campos editables:

| Campo           | Regla                                                                      |
| --------------- | -------------------------------------------------------------------------- |
| `name`        | Obligatorio, entre 3 y 100 caracteres después de quitar espacios externos |
| `price`       | Obligatorio, mayor que cero; no admite `NaN` ni infinito                  |
| `stock`       | Obligatorio, entero mayor o igual que cero                                 |
| `description` | Opcional, hasta 500 caracteres; valor por defecto `null`                  |

Los campos no declarados se rechazan. Los errores de validación predeterminados de FastAPI son `422 Unprocessable Entity`.

## Identificadores, solicitudes repetidas y persistencia

Cada `POST` crea un nuevo recurso y el repositorio asigna el ID. En consecuencia,
repetir el mismo JSON produce otro ID y añade otro registro; el contenido idéntico
no se deduplica automáticamente. Esto es intencional y está probado en
`tests/test_product_create_semantics.py`. Para entender las implicaciones y las
posibles alternativas, consulte `docs/create-and-idempotency-semantics.md`.

`PUT` actualiza el recurso existente y conserva su identificador. El ID lo asigna
la API, no el cliente. Si el dominio futuro requiere identidad única (p. ej. SKU)
o reintentos idempotentes, la regla debe diseñarse explícitamente y respaldarse
con una persistencia apropiada.

## Test

```
python -m unittest discover -s tests -v
fastapi dev
```

## Probar en Swagger

1. Ejecuta `fastapi dev` desde la raíz del repositorio y abre <http://127.0.0.1:8000/docs>.
2. Crea un producto con `POST`.
3. Copia el `id` y consulta con `GET`.
4. Lista con `skip`, `limit` e `include_desc`.
5. Actualiza el mismo producto con `PUT`.
6. Elimínalo con `DELETE` y confirma el `204` sin contenido.
7. Prueba un ID inexistente en GET, PUT y DELETE para validar el contrato de error `404`.


En Swagger UI (`/docs`), crear un producto, crear de nuevo exactamente el mismo
payload, listar y confirmar dos IDs distintos. Después probar consulta, actualización
y eliminación. Para una validación reproducible, cada test de API usa un repositorio
nuevo mediante `app.dependency_overrides`

## Restricciones

El almacenamiento en memoria no persiste después de reiniciar el proceso ni se comparte entre varios workers. No debe considerarse una base de datos. Su propósito es demostrar los contratos HTTP y mantener intercambiable la capa de persistencia.

Consulta [Manejo de errores HTTP](http-errors.md) para las respuestas y los casos `404`/`422`.