# Sección 5 — CRUD de productos

Extensión del alcance CRUD para incluir actualización.

Esta sección sustituye las respuestas didácticas de la sección 3 por operaciones reales sobre un pequeño almacén en memoria. Reutiliza Pydantic para validar entradas y describir respuestas.

> **Limitación importante:** el almacén vive en la memoria del proceso. Los datos se pierden al reiniciar la aplicación o recargar el servidor de desarrollo. Tampoco se comparte entre procesos o instancias. Esto permite aprender el contrato REST, pero no es persistencia adecuada para producción.

## 1. Endpoints

| Método | Ruta | Éxito | Errores habituales |
|---|---|---|---|
| POST | `/api/v1/products` | `201 Created` + producto | `422` si el cuerpo no es válido |
| GET | `/api/v1/products` | `200 OK` + lista paginada | `422` si `skip` o `limit` no son válidos |
| GET | `/api/v1/products/{product_id}` | `200 OK` + producto | `404` si no existe; `422` si el ID es inválido |
| PUT | `/api/v1/products/{product_id}` | `200 OK` + producto actualizado | `404` si no existe; `422` si el ID o cuerpo no es válido |
| DELETE | `/api/v1/products/{product_id}` | `204 No Content`, sin cuerpo | `404` si no existe; `422` si el ID es inválido |


## 2. Esquema de entrada

`ProductCreate` se declara en `app/schemas/product.py` y se usa tanto para crear como para actualizar completamente los campos editables:

| Campo           | Regla                                                                      |
| --------------- | -------------------------------------------------------------------------- |
| `name`        | Obligatorio, entre 3 y 100 caracteres después de quitar espacios externos |
| `price`       | Obligatorio, mayor que cero; no admite`NaN` ni infinito                  |
| `stock`       | Obligatorio, entero mayor o igual que cero                                 |
| `description` | Opcional, hasta 500 caracteres; valor por defecto`null`                  |

Los campos no declarados se rechazan. Los errores de validación predeterminados de FastAPI son `422 Unprocessable Entity`.

## Flujo de responsabilidades

- `app/main.py`: declara endpoints, valida parámetros con FastAPI/Pydantic y traduce las representaciones.
- `app/services/product_service.py`: coordina las operaciones y decide cuándo un producto no existe.
- `app/domain/models.py`: contiene las entidades y datos de producto propios del dominio.
- `app/repositories/product_repository.py`: define el protocolo de persistencia.
- `app/repositories/in_memory_product_repository.py`: implementación temporal utilizada para aprendizaje.

El endpoint no mantiene un diccionario de productos. Para cambiar almacenamiento se reemplaza el adaptador en `app/core/dependencies.py` siempre que respete `ProductRepository`.

## Probar en Swagger

1. Ejecuta `fastapi dev` desde la raíz del repositorio y abre <http://127.0.0.1:8000/docs>.
2. Crea un producto con `POST`.
3. Copia el `id` y consulta con `GET`.
4. Lista con `skip`, `limit` e `include_desc`.
5. Actualiza el mismo producto con `PUT`.
6. Elimínalo con `DELETE` y confirma el `204` sin contenido.
7. Prueba un ID inexistente en GET, PUT y DELETE para validar el contrato de error `404`.

## Restricciones

El almacenamiento en memoria no persiste después de reiniciar el proceso ni se comparte entre varios workers. No debe considerarse una base de datos. Su propósito es demostrar los contratos HTTP y mantener intercambiable la capa de persistencia.

Consulta [Manejo de errores HTTP](http-errors.md) para las respuestas y los casos `404`/`422`.
