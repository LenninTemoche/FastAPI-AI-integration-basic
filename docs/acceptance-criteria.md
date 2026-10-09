# Criterios de aceptación

Este archivo diferencia los criterios de la **sección 1** del objetivo final del proyecto. En esta sección se validan documentos y decisiones, no una aplicación ejecutable.

## A. Sección 1 — alcance y arquitectura

- [ ] A1. El README identifica claramente el propósito y el estado actual del proyecto.
- [ ] A2. Se definen objetivos, casos de uso, requisitos funcionales y no funcionales.
- [ ] A3. Se documentan explícitamente los temas fuera de alcance.
- [ ] A4. La arquitectura se representa en un diagrama y se describen las responsabilidades de cada capa.
- [ ] A5. Se aclara que la solución empieza como monolito modular, no como microservicios.
- [ ] A6. Python 3.13 queda registrado como versión objetivo, con compatibilidad de dependencias por comprobar en la sección 2.
- [ ] A7. El proveedor LLM queda abierto y se establece que su clave permanecerá del lado servidor.
- [ ] A8. Se identifica la limitación del almacenamiento en memoria como recurso didáctico, no como persistencia de producción.
- [ ] A9. La documentación indica cómo se organizarán las secciones y los commits manuales.
- [ ] A10. Existe un mensaje sugerido para el primer commit documental.

### Condición para cerrar la sección 1

La sección puede cerrarse cuando los criterios A1–A10 estén revisados, los archivos sean añadidos al repositorio y el primer commit se haya creado manualmente. No es requisito ejecutar FastAPI en esta sección.

## B. Objetivo final — no verificar todavía

- [ ] B1. Instalación reproducible de dependencias en un entorno limpio con Python 3.13.
- [ ] B2. La aplicación arranca localmente y documenta `/docs` y `/openapi.json`.
- [ ] B3. Las rutas implementadas respetan contratos de solicitud y respuesta.
- [ ] B4. El CRUD tiene casos de éxito, validación, recurso inexistente y límites.
- [ ] B5. Las rutas delegan la lógica a servicios y repositorios.
- [ ] B6. Las pruebas automatizadas cubren rutas, servicios y errores relevantes.
- [ ] B7. Las llamadas externas tienen timeout y tratamiento de errores.
- [ ] B8. Los secretos no están versionados ni aparecen en logs.
- [ ] B9. El proveedor LLM se puede configurar sin reescribir routers ni contratos públicos.
- [ ] B10. Hay una guía de integración desde al menos un cliente externo.
- [ ] B11. Las limitaciones de persistencia, rendimiento y despliegue están documentadas.
- [ ] B12. Se realiza una revisión de seguridad antes de considerar el despliegue de producción.
