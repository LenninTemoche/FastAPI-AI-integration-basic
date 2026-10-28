# Sección 8 — Integración LLM mediante API key

## Objetivo

Exponer una operación de **generación de texto** reutilizable por HTTP/JSON sin acoplar los endpoints ni el caso de uso a un proveedor comercial específico. La ruta recibe un contrato propio y devuelve una respuesta normalizada; el adaptador traduce ese contrato al protocolo HTTP del proveedor.

> **Nota:** Esta sección cubre solo generación de texto (`POST /api/v1/llm/ask`). Para **transcripción de audio (Whisper)** y **análisis de video** (visión por fotogramas), consulta [`multimodal-media.md`](multimodal-media.md). Esas capacidades usan rutas separadas bajo `/api/v1/media/` y modelos independientes del modelo de chat.

## Decisión de arquitectura

La primera implementación incorpora un **adaptador de protocolo compatible con OpenAI Chat Completions** mediante HTTPX. Esto no obliga a contratar un proveedor concreto: `LLM_BASE_URL`, `LLM_MODEL` y `LLM_API_KEY` se configuran fuera del código. El endpoint del proveedor debe implementar el contrato compatible `POST {base_url}/chat/completions` con autenticación Bearer y el formato de solicitud/respuesta de Chat Completions.

Si el proveedor elegido utiliza otro protocolo (por ejemplo, otro cuerpo JSON, ruta, autenticación o estructura de respuesta), debe añadirse un adaptador que implemente `LLMProvider`; no se debe modificar el endpoint HTTP ni `LLMService` para introducir particularidades del proveedor.

```text
Cliente HTTP/JSON
       |
       v
POST /api/v1/llm/ask  (APIRouter + Pydantic)
       |
       v
LLMService  (caso de uso, sin FastAPI ni HTTPX)
       |
       v
LLMProvider  (puerto / protocolo)
       |
       v
OpenAICompatibleChatProvider  (adaptador HTTPX)
       |
       v
Proveedor externo configurado por entorno
```

## Configuración local en Windows

1. Copiar `.env.example` a `.env` en la raíz del repositorio.
2. Completar los valores con las credenciales y el modelo disponibles en el proveedor escogido.
3. No incluir comillas tipográficas, no guardar la clave en el frontend y no subir `.env` a Git.
4. Instalar las dependencias y arrancar la API desde la raíz del repositorio.

Variables disponibles:

| Variable | Obligatoria para llamar al proveedor | Descripción |
|---|---:|---|
| `LLM_PROVIDER` | Sí | En esta entrega debe ser `openai_compatible`. |
| `LLM_API_KEY` | Sí | Credencial de servidor, tratada como secreto. |
| `LLM_BASE_URL` | Sí | URL base, normalmente termina en `/v1`; se añade `/chat/completions`. |
| `LLM_MODEL` | Sí | Identificador exacto de un modelo habilitado en la cuenta/proveedor. Usado solo para generación de texto y análisis visual; **no** para Whisper (usa `MEDIA_TRANSCRIPTION_MODEL`). |
| `LLM_TIMEOUT_SECONDS` | No | Timeout total; valor predeterminado `30`, rango permitido mayor que 0 y hasta 120. |
| `LLM_MAX_TOKENS` | No | Límite configurado de generación; predeterminado `512`, rango de 1 a 4096. |
| `LLM_TEMPERATURE` | No | Temperatura configurada; predeterminado `0.2`, rango de 0 a 2. |

La aplicación puede iniciarse sin una API key para seguir utilizando el CRUD. Si se llama a la ruta LLM sin configuración suficiente, devuelve `503 Service Unavailable`, sin intentar una llamada externa.

Por seguridad, `LLM_BASE_URL` debe usar **HTTPS** para hosts externos. Se permite HTTP únicamente para loopback (`localhost`, `127.0.0.1` o `::1`) durante pruebas con servidores locales. Así evitamos enviar la credencial a un endpoint remoto sin cifrado.

## Contrato HTTP propio

### Solicitud

`POST /api/v1/llm/ask`

```json
{
  "prompt": "Resume qué problema resuelve una API REST.",
  "system_prompt": "Responde en español y de forma concisa."
}
```

`system_prompt` es opcional. No se acepta el campo `api_key` en el JSON. `prompt` admite entre 1 y 12 000 caracteres después de quitar espacios externos; `system_prompt` admite hasta 4 000 caracteres.

**Confianza en las instrucciones:** `system_prompt` lo envía el consumidor y no debe tratarse como una política de seguridad confiable. Si una aplicación necesita instrucciones del sistema fijas, deberá construirlas del lado servidor o aplicar una lista de instrucciones permitidas.

### Respuesta normalizada

```json
{
  "response": "Una API REST permite ...",
  "provider": "openai_compatible",
  "model": "modelo-configurado",
  "usage": {
    "input_tokens": 18,
    "output_tokens": 42
  }
}
```

Los contadores de `usage` pueden ser `null` si el proveedor no devuelve esa información. No devolvemos el objeto JSON original del proveedor: eso evita que los consumidores queden ligados a la forma de respuesta de una API externa.

## Errores HTTP documentados

| Estado | Significado | Detalle público |
|---|---|---|
| `200` | Generación completada | Objeto `LLMAskResponse`. |
| `422` | Solicitud inválida según Pydantic | Detalles de validación estándar de FastAPI. |
| `502` | Error del proveedor o respuesta incompatible | Mensaje genérico, sin cuerpo externo ni secretos. |
| `503` | Configuración ausente o límite temporal del proveedor | Mensaje genérico. |
| `504` | Se agotó el tiempo de espera | Mensaje genérico. |

Las credenciales incorrectas o errores HTTP del proveedor no se traducen directamente a un `401` del consumidor, porque la credencial de proveedor no es la identidad del cliente de nuestra API.

## Gestión de conexiones y fallos

- Un único `httpx.AsyncClient` se crea y cierra mediante el `lifespan` de FastAPI para reutilizar conexiones.
- Se establece un timeout y límites de conexiones.
- La llamada es asíncrona; no bloquea el event loop con una petición HTTP síncrona.
- No se reintenta automáticamente un `POST`: si el proveedor procesó la solicitud pero la respuesta se perdió, el reintento podría duplicar el consumo/coste.
- Los logs registran solo categorías de fallo y códigos HTTP; no registran la API key, el prompt ni el cuerpo de error externo.
- No hay historial, streaming ni almacenamiento de conversaciones en esta sección; cada solicitud es una generación independiente.

## Pruebas sin API key ni coste

La suite usa `httpx.MockTransport` y un servicio falso. Comprueba el contrato de salida, validación, autenticación Bearer al proveedor simulado, conversión de errores, timeout, configuración ausente y documentación OpenAPI. Estas pruebas no demuestran que una credencial comercial real sea válida; esa comprobación se hace manualmente con un modelo habilitado y una clave local.

Desde la raíz del repositorio:

```powershell
python -m unittest discover -s tests -v
```

## Comprobación manual con el proveedor elegido

1. Verificar que `.env` está completado y sigue sin aparecer en `git status`.
2. Iniciar con `fastapi dev`.
3. Abrir `http://127.0.0.1:8000/docs`.
4. Ejecutar `POST /api/v1/llm/ask` con una pregunta inocua y sin credenciales en el JSON.
5. Confirmar `200` y el contrato normalizado. Probar también configuración ausente y prompt inválido.
6. No publicar la API externamente aún: autenticación, autorización, rate limiting, observabilidad, revisión de costes y despliegue quedan para la sección 9.

## Limitación importante

La autenticación de la API para sus propios consumidores es distinta de `LLM_API_KEY`. Esta entrega no protege el endpoint LLM frente al uso público ni implementa cuota por usuario; no se debe exponer a Internet sin controles de acceso y consumo.

## Documentación relacionada

- [`multimodal-media.md`](multimodal-media.md): transcripción de audio (Whisper) y análisis de video (visión por fotogramas), con modelos y endpoints separados de la generación de texto.
