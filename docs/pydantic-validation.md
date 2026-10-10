# Sección 4 — Validación de datos con Pydantic

En esta sección se definen contratos de entrada y salida reutilizables con Pydantic. FastAPI utiliza estos modelos para validar el cuerpo JSON, generar el esquema OpenAPI y devolver automáticamente `422 Unprocessable Entity` cuando los datos no cumplen las restricciones declaradas.

## 1. Modelo `ProductCreate`

Archivo: `app/schemas/product.py`.

| Campo           | Obligatorio | Regla                                                                |
| --------------- | ----------- | -------------------------------------------------------------------- |
| `name`        | Sí         | Cadena de 3 a 100 caracteres después de eliminar espacios externos. |
| `price`       | Sí         | Número mayor que cero; no permite`NaN` ni infinito.               |
| `stock`       | Sí         | Entero mayor o igual que cero.                                       |
| `description` | No          | Cadena opcional, máximo 500 caracteres; por defecto`null`.        |

El modelo declara `extra="forbid"`, por lo que los campos no definidos también producen un error de validación. `str_strip_whitespace=True` elimina espacios al inicio y al final de los campos de texto antes de validar sus restricciones.

Las anotaciones de tipo y `Field` describen los límites. La API no debe confiar en que un cliente web, aplicación móvil u otro servicio valide por su cuenta: el backend valida de nuevo cada entrada.

## 2. Endpoint didáctico de validación

`POST /api/v1/products/validate`

Esta ruta permite probar el modelo en Swagger sin adelantarnos al CRUD. Recibe el objeto, lo valida y devuelve una vista previa. **No crea, no identifica y no guarda un producto.** En la sección 5 se añadirá `POST /api/v1/products` para implementar la creación real, reutilizando `ProductCreate` y definiendo un esquema de salida apropiado para el recurso persistido.

Payload válido de ejemplo:

```json
{
  "name": "Router Wi-Fi",
  "price": 129.9,
  "stock": 15,
  "description": "Router de doble banda"
}
```

Respuesta esperada (`200 OK`):

```json
{
  "valid": true,
  "message": "El payload cumple las reglas de validación. No se ha creado ni almacenado un producto.",
  "product": {
    "name": "Router Wi-Fi",
    "price": 129.9,
    "stock": 15,
    "description": "Router de doble banda"
  }
}
```

Si se omite `description`, el modelo permite el valor por defecto `null`.

## 3. Pruebas en Swagger UI

1. Inicia la API desde la raíz del repositorio con `fastapi dev`.
2. Abre [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
3. Abre `POST /api/v1/products/validate`, selecciona **Try it out**, introduce el payload válido y ejecuta la operación.
4. Repite las pruebas inválidas que aparecen a continuación y confirma el código `422`.
5. Prueba también `GET /api/v1/products` y `GET /api/v1/products/{product_id}` para verificar los límites incorporados a sus parámetros.

### Matriz de validación

| Caso                         | Ejemplo                                                | Resultado esperado                           |
| ---------------------------- | ------------------------------------------------------ | -------------------------------------------- |
| Payload válido              | Nombre`Router Wi-Fi`, precio `129.9`, stock `15` | `200 OK`; respuesta con `valid: true`.   |
| Nombre demasiado corto       | `name: "TV"`                                         | `422`; incumple `min_length=3`.          |
| Precio igual a cero          | `price: 0`                                           | `422`; el precio debe ser mayor que cero.  |
| Precio negativo              | `price: -2`                                          | `422`.                                     |
| Stock negativo               | `stock: -1`                                          | `422`; el stock debe ser cero o positivo.  |
| Descripción demasiado larga | Más de 500 caracteres                                 | `422`.                                     |
| Campo desconocido            | Añadir`category` al JSON                            | `422`; los campos extra están prohibidos. |
| Límite fuera de rango       | `GET /api/v1/products?limit=0` o `limit=101`       | `422`; `limit` debe estar entre 1 y 100. |
| Identificador no positivo    | `GET /api/v1/products/0`                             | `422`; `product_id` debe ser al menos 1. |
| Error de tipo                | `price: "caro"` o `stock: "muchos"`                | `422`.                                     |

Las ubicaciones y los mensajes concretos dentro de `detail` pueden variar según el campo inválido. En esta sección se conserva el formato de validación predeterminado de FastAPI: no se implementan todavía manejadores personalizados de errores.

## 4. Decisiones y límites de alcance

- Se usa `BaseModel`, `ConfigDict` y `Field` de Pydantic.
- El esquema de entrada se separa de `main.py` y queda en `app/schemas/product.py` para poder reutilizarlo desde endpoints y servicios futuros.
- Se aprovecha la sección para añadir restricciones explícitas a los parámetros existentes: `product_id >= 1` y `1 <= limit <= 100`.
- `POST /api/v1/products/validate` es temporal y didáctico; no es una operación CRUD ni persiste datos. Se documenta para evitar que un consumidor lo confunda con una creación.
- No se incorporan base de datos, almacenamiento en memoria, `POST /api/v1/products` de creación real, actualizaciones ni eliminaciones. Eso corresponde a la sección 5.
- No se personaliza el manejo de `422` ni de otros errores HTTP; eso corresponde a la sección 6.
- Los routers se mantienen en `app/main.py` temporalmente; la modularización corresponde a la sección 7.

## Criterios de aceptación

- [ ] El endpoint `GET /` sigue funcionando.
- [ ] Los endpoints de la sección 3 mantienen sus respuestas válidas.
- [ ] `GET /api/v1/products?limit=0` y `limit=101` devuelven `422`.
- [ ] `GET /api/v1/products/0` devuelve `422`.
- [ ] El payload válido de `POST /api/v1/products/validate` devuelve `200` y una vista previa con los campos esperados.
- [ ] `name` con menos de 3 caracteres devuelve `422`.
- [ ] `price <= 0`, `stock < 0`, tipos inválidos y campos extra devuelven `422`.
- [ ] Swagger documenta el cuerpo de petición y los límites de los parámetros.
- [ ] La guía y los criterios de aceptación se revisan y se incluyen en un commit manual.

## Referencias oficiales

- [FastAPI — Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- [FastAPI — Body Fields y validaciones con `Field`](https://fastapi.tiangolo.com/tutorial/body-fields/)
- [FastAPI — Validaciones numéricas de parámetros](https://fastapi.tiangolo.com/tutorial/path-params-numeric-validations/)
- [Pydantic — Fields](https://docs.pydantic.dev/latest/concepts/fields/)
- [Video de referencia](https://www.youtube.com/watch?v=WrnFtgGLO38)
