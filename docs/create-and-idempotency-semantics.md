# Semántica de creación, duplicados e idempotencia

## Resultado de la revisión

Se comprobó que `InMemoryProductRepository.create()` asigna el ID siguiente y
almacena un objeto nuevo en cada llamada. Por eso, enviar varias veces el mismo
JSON a `POST /api/v1/products` produce IDs distintos. Este comportamiento es el
contrato adoptado para el CRUD didáctico; no es un fallo del contador.

## Contrato actual

- Cada POST válido crea un recurso nuevo y devuelve `201 Created`.
- Los IDs los asigna el repositorio y no se incluyen en `ProductCreate`.
- El contenido idéntico no se considera automáticamente identidad de negocio.
- El listado puede incluir registros con atributos iguales y con IDs distintos.
- Un `PUT /api/v1/products/{product_id}` actualiza el recurso identificado y
  conserva el ID.
- El almacenamiento es en memoria: los datos y el contador se reinician cuando
  se reconstruye el repositorio o reinicia el proceso.

## ¿Por qué no rechazamos automáticamente los duplicados?

La igualdad de `name`, `price`, `stock` y `description` no demuestra que se trate
del mismo producto real. Por ejemplo, dos artículos pueden compartir nombre y
precio o representar unidades separadas. Rechazar cuerpos iguales impondría una
regla de negocio implícita y posiblemente incorrecta para proyectos futuros.

Si el dominio requiere unicidad, debe definirse una clave estable (por ejemplo,
`sku`, `external_id` o un código de negocio) y aplicarse en el servicio y en la
persistencia real mediante una restricción de unicidad. No se recomienda usar un
hash de todos los campos como regla universal.

## Reintentos de clientes e idempotencia

Un cliente puede repetir un POST porque hubo un timeout aunque el servidor ya
haya creado el recurso. En ese caso, repetir el mismo JSON por sí solo no permite
distinguir un reintento de una creación intencional nueva.

Si un futuro consumidor necesita reintentos seguros, se debe diseñar un contrato
de idempotencia explícito (por ejemplo, un header `Idempotency-Key`) y guardar la
clave, una huella de la solicitud y la respuesta original con una caducidad y una
política de conflictos documentadas. La clave debe aplicarse en una persistencia
compartida y de forma atómica; un diccionario local no sería suficiente para
varias instancias o procesos.

Esa capacidad queda fuera del alcance de esta sección. No se debe afirmar que la
API actual tiene deduplicación ni idempotencia de POST.

## Prueba de regresión

`tests/test_product_create_semantics.py` envía dos payloads iguales, verifica
`201` en ambas respuestas, IDs diferentes y dos recursos en el listado. También
confirma que PUT mantiene el ID. La prueba convierte el comportamiento actual en
un contrato explícito, para poder cambiarlo más adelante mediante una decisión
arquitectónica y pruebas deliberadas.
