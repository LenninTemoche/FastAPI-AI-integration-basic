# Sección 6 — Manejo de errores HTTP

**Referencia del video:** 34:24–36:18.

**Objetivo:** que los clientes de la API reciban códigos HTTP apropiados y respuestas de error documentadas y previsibles.

Esta sección conserva el CRUD en memoria de la sección 5. No introduce routers, persistencia, autenticación ni proveedores de IA.

## 1. Principio de diseño

Para detener una operación y devolver un error HTTP controlado, se utiliza `raise HTTPException(...)`, no `return`. En este proyecto, `_get_product_or_404()` centraliza la comprobación de existencia y se reutiliza al consultar, actualizar o eliminar un producto.

Ejemplo simplificado:

```python
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=f"Product with id {product_id} not found",
)
```

`detail` debe ser un mensaje breve y seguro. No se deben incluir tokens, claves, rutas locales, trazas de ejecución ni otros datos internos.

## 2. Contrato para producto inexistente

Los endpoints siguientes documentan una respuesta `404` con el esquema `ErrorResponse`:

- `GET /api/v1/products/{product_id}`
- `PUT /api/v1/products/{product_id}`
- `DELETE /api/v1/products/{product_id}`

Cuerpo de ejemplo:

```json
{
  "detail": "Product with id 999999 not found"
}
```

El código HTTP real es `404 Not Found`. `ErrorResponse` documenta el contrato de respuesta en OpenAPI; no reemplaza el manejador estándar de `HTTPException` de FastAPI.

## 3. Códigos HTTP que debemos distinguir

| Código | Cuándo aparece en esta API | Significado para el cliente |
|---|---|---|
| `201 Created` | `POST /api/v1/products` correcto | El producto fue creado. |
| `204 No Content` | `DELETE /api/v1/products/{product_id}` correcto | La operación terminó sin cuerpo de respuesta. |
| `404 Not Found` | ID de producto inexistente en GET, PUT o DELETE | No existe el recurso solicitado. |
| `405 Method Not Allowed` | Se usa un método no admitido por una ruta existente | La ruta existe, pero no acepta ese método. |
| `422 Unprocessable Entity` | Cuerpo, path o query no cumple tipos o restricciones | Corregir los datos enviados. |
| `500 Internal Server Error` | Excepción inesperada no controlada | Error del servidor; no exponer detalles internos al cliente. |

No inventamos respuestas `400`, `401`, `403` o `409` en esta sección: todavía no hay reglas de negocio, autenticación o conflictos de persistencia que las requieran. Se introducirán cuando la funcionalidad correspondiente exista.

## 4. Validación manual en Swagger UI

1. Activa el entorno virtual y arranca el servidor desde la raíz del repositorio:

   ```powershell
   fastapi dev
   ```

2. Abre <http://127.0.0.1:8000/docs>.
3. Ejecuta `GET /api/v1/products/999999`. Debe devolver `404` y el objeto JSON de ejemplo.
4. Ejecuta `PUT /api/v1/products/999999` con un cuerpo válido. Debe devolver `404`, no `200`.
5. Ejecuta `DELETE /api/v1/products/999999`. Debe devolver `404`, no `204`.
6. Crea un producto y confirma que consultarlo con su ID produce `200`.
7. Ejecuta `GET /api/v1/products/0` y `GET /api/v1/products/abc`. Ambos deben devolver `422`: `0` infringe la restricción `ge=1` y `abc` no puede convertirse a entero.
8. Envía un cuerpo inválido a `POST /api/v1/products`. Debe seguir devolviendo `422` con los detalles de validación de FastAPI.
9. En Swagger, despliega las respuestas de GET, PUT y DELETE por ID. Debe aparecer el esquema `ErrorResponse` para `404`.

También puedes revisar el contrato OpenAPI en <http://127.0.0.1:8000/openapi.json>.

## 5. Validación por PowerShell (opcional)

Con el servidor activo, `curl.exe` permite ver tanto el código HTTP como el cuerpo de la respuesta:

```powershell
curl.exe -i http://127.0.0.1:8000/api/v1/products/999999
```

Busca `404` en la primera línea de la respuesta y verifica que el cuerpo contenga `detail` con un mensaje claro.

## 6. Alcance y decisiones

- Se conserva el formato de error predeterminado de FastAPI para `HTTPException` (`{"detail": "..."}`).
- No se sobrescribe globalmente el manejador de `HTTPException` ni el de errores de validación. Mantener `422` evita introducir un formato diferente solo para algunos errores.
- `ErrorResponse` se usa en `responses` para que OpenAPI documente el `404` de los endpoints que buscan un producto.
- Una URL inexistente que no coincide con ninguna ruta también puede devolver `404`, pero es un error de enrutamiento y no necesariamente contiene el mismo mensaje de dominio.
- El almacenamiento continúa en memoria: un `404` significa que el identificador no está presente en el proceso actual, no que se consultó una base de datos durable.

## Criterios de aceptación de esta sección

- [ ] El CRUD sigue funcionando para datos válidos.
- [ ] GET, PUT y DELETE por ID devuelven `404` si el producto no existe.
- [ ] Los errores `404` tienen `{"detail": "..."}` y no exponen datos internos.
- [ ] Los valores path y los cuerpos inválidos conservan `422`.
- [ ] Swagger/OpenAPI documenta el esquema `ErrorResponse` para el `404` de GET, PUT y DELETE por ID.
- [ ] `git diff --check` pasa, los cambios se revisan y se realiza commit/push manual.

## Referencias

- [FastAPI — Manejo de errores](https://fastapi.tiangolo.com/es/tutorial/handling-errors/)
- [FastAPI — Referencia de excepciones HTTP](https://fastapi.tiangolo.com/reference/exceptions/)
- [Video de referencia](https://www.youtube.com/watch?v=WrnFtgGLO38)
