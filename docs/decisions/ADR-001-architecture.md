# ADR-001: Arquitectura inicial de la API reutilizable

- **Estado:** Aceptada para la fase inicial
- **Fecha:** 2026-10-08
- **Contexto:** Se inicia un repositorio nuevo para una API REST reutilizable, guiada por un tutorial de FastAPI, pero con criterios de mantenibilidad e integración entre proyectos.

## Contexto y problema

La solución debe ser comprensible para un desarrollador que aprende FastAPI y, al mismo tiempo, ofrecer una organización que pueda ampliarse con CRUD, persistencia, inferencia ML y servicios LLM. Debe poder ser consumida por clientes heterogéneos por HTTP/JSON y mantenerse independiente del proveedor LLM.

## Decisiones

1. Utilizar Python 3.13 como versión objetivo.
2. Utilizar FastAPI como framework HTTP y Pydantic para validar y documentar contratos.
3. Usar un monolito modular con separación conceptual entre rutas, esquemas, servicios, repositorios, configuración e integraciones.
4. Mantener el contrato público bajo `/api/v1`.
5. Diseñar la integración LLM detrás de un adaptador; el proveedor concreto y sus versiones se decidirán durante la fase correspondiente.
6. Mantener las credenciales de proveedores en el backend y fuera del control de versiones.
7. Permitir almacenamiento en memoria únicamente como implementación didáctica inicial, sin considerarlo almacenamiento duradero.
8. Aplicar cambios y documentación en secuencia, mediante commits manuales de alcance acotado.

## Alternativas consideradas

### Poner toda la lógica en `main.py`

- **Ventaja:** menos archivos al inicio.
- **Desventaja:** favorece el acoplamiento y dificulta pruebas, mantenimiento y reutilización.
- **Decisión:** no usarlo como arquitectura objetivo; la aplicación mínima de aprendizaje puede existir temporalmente en la sección 2.

### Empezar con microservicios

- **Ventaja:** despliegue y escalado independientes.
- **Desventaja:** añade complejidad de red, despliegue y operación antes de tener necesidades demostradas.
- **Decisión:** empezar con un monolito modular y extraer servicios solo si aparecen requisitos concretos.

### Acoplar los endpoints al SDK de un proveedor LLM

- **Ventaja:** implementación inicial rápida.
- **Desventaja:** el cambio de proveedor contamina routers, contratos y pruebas.
- **Decisión:** aislar el proveedor mediante un adaptador.

## Consecuencias

- Se necesita una separación mínima entre capas y pruebas para preservar sus contratos.
- El primer entregable es documental; aún no hay aplicación ejecutable.
- Algunas abstracciones se crearán más adelante, solo cuando la secuencia lo requiera.
- La compatibilidad de las versiones concretas de dependencias con Python 3.13 debe validarse en la sección 2.
- La elección del proveedor LLM, la persistencia definitiva y la autenticación exacta continúan abiertas.

## Referencias

- FastAPI, primeros pasos: https://fastapi.tiangolo.com/tutorial/first-steps/
- FastAPI, sistema de dependencias: https://fastapi.tiangolo.com/tutorial/dependencies/
- Python 3.13, entornos virtuales: https://docs.python.org/es/3.13/library/venv.html
- HTTPX, soporte asíncrono: https://www.python-httpx.org/async/
