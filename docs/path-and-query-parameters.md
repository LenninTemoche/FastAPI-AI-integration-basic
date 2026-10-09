# Sección 3 — Rutas y parámetros

**FastAPI — Path & Query Parameters:** 

Esta sección introduce parámetros de ruta (*path parameters*) y parámetros de consulta (*query parameters*). Mantiene el alcance didáctico: todavía no implementa Pydantic, almacenamiento, CRUD, routers ni manejo personalizado de errores.

## 1. Parámetros de ruta

Endpoint: `GET /api/v1/products/{product_id}`

El valor entre llaves forma parte de la ruta. FastAPI lo entrega a la función como `product_id`; la anotación `int` permite convertirlo a entero y rechazar entradas no convertibles.

Prueba en navegador o Swagger:

```
http://127.0.0.1:8000/api/v1/products/25
```

Respuesta esperada (`200 OK`):

```
{
  "message": "Parámetro de ruta recibido. La consulta del producto real se implementará en la sección de CRUD.",
  "product_id": 25
}
```

Prueba también `/api/v1/products/abc`. Como `abc` no se puede convertir a entero, FastAPI debe responder `422 Unprocessable Entity` con el detalle de validación predeterminado.

## 2. Parámetros de consulta

Endpoint: `GET /api/v1/products`

Los parámetros de consulta aparecen después de `?` y se separan mediante `&`. En este ejemplo:

- `limit`: entero opcional; su valor por defecto es `10`.
- `include_desc`: booleano opcional; su valor por defecto es `false`.

Prueba los valores por defecto:

```
http://127.0.0.1:8000/api/v1/products
```

Respuesta esperada (`200 OK`):

```
{
  "message": "Parámetros de consulta recibidos. El listado real se implementará en la sección de CRUD.",
  "limit": 10,
  "include_desc": false
}
```

Ahora prueba valores explícitos:

```
http://127.0.0.1:8000/api/v1/products?limit=5&include_desc=true
```

Respuesta esperada (`200 OK`):

```
{
  "message": "Parámetros de consulta recibidos. El listado real se implementará en la sección de CRUD.",
  "limit": 5,
  "include_desc": true
}
```

FastAPI convierte los valores enviados como texto a los tipos declarados cuando la conversión es válida. También reconoce representaciones habituales de booleanos, por ejemplo `true`, `false`, `1` y `0`.

Prueba `?limit=abc`. La conversión a entero fallará y FastAPI responderá `422 Unprocessable Entity` con el formato de validación predeterminado.

## 3. Comprobación en Swagger UI

1. Inicia la aplicación desde la raíz del repositorio con `fastapi dev`.
2. Abre <http://127.0.0.1:8000/docs>.
3. Localiza el grupo **Productos**.
4. Ejecuta `GET /api/v1/products` sin cambiar parámetros; confirma los valores por defecto.
5. Ejecuta la misma ruta con `limit=5` e `include_desc=true`.
6. Ejecuta `GET /api/v1/products/{product_id}` con `product_id=25`.
7. Si deseas comprobar la conversión de tipos, prueba un identificador no entero y un `limit` no numérico.

## 4. Decisiones de alcance

- Se usa el prefijo `/api/v1` desde esta etapa, acorde con el objetivo de versionar el contrato HTTP.
- Los endpoints **no** leen ni modifican un almacén de productos. Solo devuelven los parámetros recibidos; el CRUD se implementará en la sección 5.
- Los errores `422` son la respuesta automática de FastAPI. No se personalizan todavía.
- No se añaden restricciones como `limit > 0` o un máximo de resultados. Se evaluarán en la sección 4, dedicada a la validación más explícita.
- Las rutas siguen temporalmente en `app/main.py`. La extracción mediante `APIRouter` corresponde a la sección 7.

## Criterios de aceptación de esta sección

- [ ] `GET /` sigue respondiendo `200 OK`.
- [ ] `GET /api/v1/products/25` devuelve el entero `product_id: 25`.
- [ ] `GET /api/v1/products` aplica `limit=10` e `include_desc=false` cuando no se envían parámetros.
- [ ] `GET /api/v1/products?limit=5&include_desc=true` devuelve los valores tipados `5` y `true`.
- [ ] Un `product_id` no entero produce `422`.
- [ ] Un `limit` no entero produce `422`.
- [ ] Swagger muestra las tres operaciones y sus parámetros.
- [ ] La documentación está revisada y los cambios se guardan en un commit manual.

## Referencias


- [FastAPI — Parámetros de consulta](https://fastapi.tiangolo.com/tutorial/
query-params/)

- [FastAPI — Path & Query Parameters](https://youtu.be/P-G85qN-88w?t=778)
