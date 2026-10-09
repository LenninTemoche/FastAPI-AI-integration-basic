# Alcance del proyecto

## 1. Propósito

Definir una base de API REST en Python que pueda incorporarse a proyectos independientes sin arrastrar dependencias innecesarias ni obligar a todos los consumidores a utilizar la misma tecnología interna.

La API expone capacidades mediante HTTP/JSON. Los clientes no necesitan conocer la implementación interna, el lenguaje en que está construido otro componente ni el proveedor de IA conectado.

## 2. Problema que buscamos resolver

Los proyectos de análisis de datos, Machine Learning y aplicaciones suelen implementar APIs con estructuras distintas, documentación incompleta y lógica acoplada a proveedores o almacenamiento. Esto dificulta reutilizar componentes, probarlos y cambiarlos.

La solución será una base modular, con contratos claros, responsabilidad separada y un proceso incremental de cambios pequeños y verificables.

## 3. Objetivos de la primera versión

1. Proporcionar una API REST basada en FastAPI.
2. Definir y validar contratos HTTP/JSON con Pydantic.
3. Usar versionado de rutas desde `/api/v1`.
4. Implementar un CRUD demostrativo con operaciones y errores bien definidos.
5. Separar endpoints, lógica de negocio y repositorios.
6. Encapsular llamadas a proveedores LLM detrás de una interfaz/adaptador.
7. Proteger secretos y separar la autenticación de clientes de las credenciales del proveedor.
8. Incorporar pruebas automatizadas, documentación OpenAPI y una guía de integración.
9. Mantener la solución lo bastante simple para aprenderla, ejecutarla localmente y extenderla.

## 4. Fuera de alcance por ahora

- Construcción de una plataforma distribuida o arquitectura de microservicios.
- Selección definitiva de un proveedor LLM.
- Entrenamiento de modelos de ML dentro de la API.
- Base de datos de producción o migraciones en la sección inicial.
- Autenticación empresarial con OAuth/OIDC, roles complejos o gestión multi-tenant.
- Streaming de respuestas, WebSockets, colas de tareas o procesamiento distribuido.
- Despliegue cloud y garantías de alta disponibilidad.
- Publicación inmediata como paquete instalable en PyPI.

Estos temas podrán añadirse si un caso de uso concreto lo justifica.

## 5. Consumidores previstos

- Frontends web: React, Angular y tecnologías equivalentes.
- Aplicaciones móviles.
- Backends Java/Spring Boot, Python y otros lenguajes compatibles con HTTP/JSON.
- Pipelines de análisis de datos.
- Servicios que exponen inferencia de modelos ML ya entrenados.
- Aplicaciones que requieren un proveedor LLM externo.
- Agentes de programación que deban leer la documentación y proponer cambios acotados.

## 6. Requisitos funcionales previstos

- RF-01: exponer una respuesta de estado de servicio.
- RF-02: exponer operaciones CRUD para un recurso demostrativo.
- RF-03: validar tipos, campos, límites y formatos de las solicitudes.
- RF-04: devolver códigos HTTP coherentes y respuestas de error documentadas.
- RF-05: documentar automáticamente las rutas con OpenAPI.
- RF-06: integrar un proveedor LLM configurable a través de un adaptador.
- RF-07: mantener el contrato público independiente del SDK del proveedor.
- RF-08: posibilitar módulos opcionales para inferencia ML sin imponerlos a cada instalación.

Los requisitos anteriores describen el objetivo del proyecto; no implican que ya estén implementados.

## 7. Requisitos no funcionales

- RNF-01 — Mantenibilidad: los módulos deben tener responsabilidades claras.
- RNF-02 — Reutilización: los clientes acceden por HTTP/JSON y contratos documentados.
- RNF-03 — Seguridad: los secretos no se almacenan en Git; se valida el acceso a rutas protegidas.
- RNF-04 — Testabilidad: la lógica de negocio puede probarse sin requerir llamadas reales a un proveedor.
- RNF-05 — Portabilidad: entorno reproducible en Windows y adaptable a Linux/contendedores más adelante.
- RNF-06 — Interoperabilidad: el contrato OpenAPI debe servir como referencia para clientes y agentes.
- RNF-07 — Evolución: los cambios incompatibles deben planificarse bajo una versión de API nueva.
- RNF-08 — Simplicidad: comenzar como aplicación modular única y evitar complejidad prematura.

## 8. Tecnologías objetivo

| Área | Decisión inicial | Nota |
|---|---|---|
| Lenguaje | Python 3.13 | Versión objetivo del proyecto |
| API HTTP | FastAPI | Verificar versiones instalables en la sección 2 |
| Esquemas | Pydantic | Contratos de solicitud/respuesta y validación |
| HTTP saliente | HTTPX | Usar cliente asíncrono para llamadas externas asíncronas |
| IA generativa | Proveedor pendiente | Se seleccionará después de definir necesidades y credenciales |
| Desarrollo | Windows + VS Code o IDE equivalente | Entorno principal |
| Control de versiones | Git + GitHub | Commits y push manuales por sección |

Las versiones exactas de paquetes no se fijan en esta etapa. Se comprobarán y documentarán al preparar el entorno en la sección 2.

## 9. Riesgos y mitigaciones

| Riesgo | Mitigación prevista |
|---|---|
| Incompatibilidad entre dependencias y Python 3.13 | Probar instalación limpia y pruebas básicas antes de fijar versiones |
| Acoplamiento al proveedor LLM | Introducir una interfaz/adaptador y pruebas con respuestas simuladas |
| Exposición accidental de claves | `.env` ignorado por Git, `.env.example` sin secretos y revisión de cambios |
| Confundir CRUD en memoria con persistencia | Documentar la limitación y dejar repositorio intercambiable |
| Crecimiento excesivo de la arquitectura | Incorporar módulos solo cuando una sección los requiera |
| Cambios de agentes de IDE fuera del alcance | Instrucciones explícitas, revisión del diff y commits pequeños |

## 10. Método de trabajo

Cada sección seguirá este ciclo:

1. Definir objetivo y archivos afectados.
2. Aplicar solo los cambios de esa sección.
3. Ejecutar las verificaciones definidas.
4. Revisar documentación y diferencias de Git.
5. Crear commit manual.
6. Confirmar el resultado antes de avanzar.

## 11. Criterio de cierre del proyecto

El proyecto se podrá considerar listo para una primera versión utilizable cuando los criterios de `acceptance-criteria.md` estén implementados y verificados. Cualquier declaración de preparación para producción requiere además una revisión específica de seguridad, persistencia, observabilidad, límites, despliegue y operación.
