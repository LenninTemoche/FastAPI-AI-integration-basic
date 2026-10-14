# Sección 7 — Modularización de rutas con APIRouter

## Objetivo

Separar la definición de rutas de `app/main.py` manteniendo estables los paths,
métodos, contratos Pydantic, códigos HTTP y formato de errores que ya consumen
los clientes.

## Nueva organización

```text
app/
├── main.py                       # composición de la aplicación
└── api/
    ├── root.py                   # GET /
    └── v1/
        ├── router.py             # agrupa la API versionada
        └── endpoints/
            └── products.py       # CRUD HTTP de productos
```

`app/main.py` crea `FastAPI`, registra los manejadores de excepciones e incluye
dos routers. `app/api/v1/router.py` declara el prefijo `/api/v1` y agrega el router
de productos, cuyo prefijo es `/products`. FastAPI combina ambos prefijos, de modo
que el endpoint resultante conserva `/api/v1/products`.

## Límites de responsabilidad

- `main.py`: composición del proceso HTTP; no define operaciones de negocio.
- `api/root.py`: endpoint general `GET /`.
- `api/v1/router.py`: registro central de routers versionados.
- `api/v1/endpoints/products.py`: parámetros HTTP, modelos de petición/respuesta,
  códigos de estado y conversión entre esquemas HTTP y tipos del dominio.
- `ProductService`: casos de uso; no importa FastAPI.
- `ProductRepository`: contrato de persistencia.
- `InMemoryProductRepository`: almacenamiento temporal de demostración.

## Compatibilidad que se debe conservar

| Método | Ruta |
|---|---|
| GET | `/` |
| POST | `/api/v1/products` |
| GET | `/api/v1/products` |
| GET | `/api/v1/products/{product_id}` |
| PUT | `/api/v1/products/{product_id}` |
| DELETE | `/api/v1/products/{product_id}` |

Los códigos `200`, `201`, `204`, `404` y `422`, la paginación `skip`/`limit`,
`include_desc`, la excepción de dominio y el esquema `ErrorResponse` se mantienen.
No se deben importar funciones endpoint desde `main.py` ni duplicar rutas en ambos
módulos.

## Comprobaciones

1. Ejecutar `python -m unittest discover -s tests -v`.
2. Arrancar `fastapi dev` desde la raíz del repo.
3. Verificar `/`, `/docs`, `/redoc` y `/openapi.json`.
4. En Swagger, comprobar que los endpoints de productos aparecen agrupados bajo
   `Productos` y que el conjunto de paths se mantiene.
5. Probar CRUD, parámetros inválidos, los `404` y el `204` sin cuerpo.
6. Probar dos solicitudes POST idénticas y confirmar el contrato documentado en
   `docs/create-and-idempotency-semantics.md`.
