# Instrucciones para agentes de programación

Estas reglas se aplican a los agentes de IDE y asistentes de código que trabajen en este repositorio.

## Antes de modificar archivos

1. Lee `README.md`, `docs/project-scope.md`, `docs/architecture.md` y `docs/acceptance-criteria.md`.
2. Identifica la sección activa del roadmap y los criterios que se deben cumplir.
3. Inspecciona el estado actual del repositorio y los cambios locales antes de proponer modificaciones.
4. No asumas que una característica está implementada porque esté descrita en la documentación.

## Trabajar por secciones

- Implementa exclusivamente la sección solicitada por la persona responsable.
- No adelantes endpoints, instalación de dependencias, CRUD, autenticación o integraciones si no pertenecen a la sección activa.
- Antes de editar, enumera brevemente los archivos que propones crear o modificar y justifica por qué.
- Prefiere cambios pequeños que puedan verificarse y revisarse manualmente.
- No hagas `git commit`, `git push`, merges ni cambios remotos sin una solicitud explícita.
- No sobrescribas cambios locales que no formen parte de la tarea.

## Principios de arquitectura

- Mantén la API como monolito modular hasta que un requisito demuestre la necesidad de separar servicios.
- Separa contratos HTTP, esquemas, lógica de negocio, repositorios e integraciones externas cuando se implementen.
- Mantén la integración LLM independiente del proveedor y no filtres detalles innecesarios del SDK al contrato público.
- Mantén el versionado inicial bajo `/api/v1` una vez que se implemente la capa HTTP.
- No agregues una dependencia nueva si la biblioteca estándar o una dependencia existente resuelven adecuadamente la necesidad.
- No conviertas almacenamiento en memoria en una promesa de persistencia duradera.

## Seguridad

- Nunca escribas claves, tokens, contraseñas ni credenciales reales en archivos versionados, documentación de ejemplo, pruebas o logs.
- Usa placeholders en ejemplos y mantén los secretos del proveedor en el backend.
- No confundas la autenticación de consumidores de esta API con la clave usada para llamar a un proveedor LLM.
- No expongas trazas, credenciales ni detalles internos en mensajes de error dirigidos al cliente.

## Calidad y validación

- Añade o actualiza pruebas cuando una sección ya tenga código ejecutable.
- No declares las pruebas como exitosas si no se ejecutaron realmente.
- Actualiza documentación si cambian contratos, configuración, instrucciones de uso o decisiones arquitectónicas.
- Explica los comandos de verificación, su resultado real y cualquier limitación pendiente.
- No afirmes que la API está lista para producción sin una revisión específica de seguridad, persistencia, límites, observabilidad y despliegue.

## Convenciones de colaboración

- Usa español para la documentación del proyecto, salvo nombres técnicos o convenciones estándar.
- Respeta los nombres y contratos existentes; propone cambios incompatibles antes de aplicarlos.
- Al terminar, presenta el resumen de archivos modificados, validaciones ejecutadas, riesgos y el mensaje de commit sugerido. La persona responsable realizará el commit y el push manualmente.
