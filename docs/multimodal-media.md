# Guía de audio y video — Sección 8 (extensión multimodal)

Esta guía documenta las capacidades de **transcripción de audio** (Whisper) y **análisis de video** (visión por fotogramas) añadidas a la sección 8. Estas capacidades usan rutas HTTP separadas y modelos independientes de la generación de texto (`POST /api/v1/llm/ask`).

## Separación de modelos y endpoints

| Capacidad | Variable de entorno | Endpoint HTTP | Endpoint del proveedor | Modelo ejemplo |
|---|---|---|---|---|
| Texto / chat | `LLM_MODEL` | `POST /api/v1/llm/ask` | `/chat/completions` | `gpt-4o-mini` |
| Audio / transcripción (Whisper) | `MEDIA_TRANSCRIPTION_MODEL` | `POST /api/v1/media/transcriptions` | `/audio/transcriptions` | `whisper-large-v3` |
| Video / análisis visual | `LLM_MODEL` (visión) | `POST /api/v1/media/videos/analyze` | `/chat/completions` con `image_url` | `gpt-4o` |

**Regla clave:** Whisper **no es un modelo de chat**. No acepta mensajes `system`/`user` ni usa `/chat/completions`. Si configuras `LLM_MODEL=whisper-large-v3` y llamas a `POST /api/v1/llm/ask`, recibirás un error (típicamente `HTTP 404` o una respuesta de formato incompatible). Para Whisper debes usar `MEDIA_TRANSCRIPTION_MODEL` y `POST /api/v1/media/transcriptions`.

## Configuración `.env`

Copia `.env.example` a `.env` y completa los valores de tu proveedor:

```ini
# --- Texto / chat ---
LLM_PROVIDER=openai_compatible
LLM_API_KEY=tu-api-key-aqui
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini

# --- Audio / transcripción (Whisper) ---
# Modelo independiente del modelo de chat. Requerido solo si usas /api/v1/media/transcriptions.
MEDIA_TRANSCRIPTION_MODEL=whisper-large-v3
# Alternativa más rápida y económica:
# MEDIA_TRANSCRIPTION_MODEL=whisper-large-v3-turbo

# Límites de audio y video (ajusta según recursos y política de costes)
MEDIA_MAX_AUDIO_MB=25
MEDIA_MAX_VIDEO_MB=50
MEDIA_VIDEO_MAX_DURATION_SECONDS=120
MEDIA_VIDEO_MAX_FRAMES=8
MEDIA_VIDEO_FRAME_INTERVAL_SECONDS=5
MEDIA_PROCESSING_TIMEOUT_SECONDS=60
```

## 1. Transcripción de audio (Whisper)

### Endpoint

`POST /api/v1/media/transcriptions`

### Solicitud (multipart/form-data)

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `file` | archivo | Sí | Archivo de audio admitido (`.flac`, `.mp3`, `.mp4`, `.mpeg`, `.mpga`, `.m4a`, `.ogg`, `.wav`, `.webm`). Límite: `MEDIA_MAX_AUDIO_MB`. |
| `language` | texto | No | Código de idioma opcional (p. ej. `es`, `en`). |

### Ejemplo con curl

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/media/transcriptions ^
  -F "file=@audio.mp3" ^
  -F "language=es"
```

### Respuesta

```json
{
  "text": "Transcripción del contenido de audio...",
  "provider": "openai_compatible",
  "model": "whisper-large-v3"
}
```

### Errores comunes

| Código | Causa |
|---|---|
| `404` | `MEDIA_TRANSCRIPTION_MODEL` no es un modelo de transcripción válido para el proveedor, o el endpoint `/audio/transcriptions` no existe. |
| `413` | El archivo excede `MEDIA_MAX_AUDIO_MB` (por defecto 25 MB). |
| `415` | Extensión de archivo no admitida para audio. |
| `422` | Archivo vacío o dañado. |
| `503` | `MEDIA_TRANSCRIPTION_MODEL`, `LLM_API_KEY` o `LLM_BASE_URL` no configurados. |
| `504` | Timeout de la llamada al proveedor. |

## 2. Análisis de video (visión por fotogramas)

### Endpoint

`POST /api/v1/media/videos/analyze`

### Solicitud (multipart/form-data)

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `file` | archivo | Sí | Archivo de video (`.mp4`, `.mov`, `.webm`, `.mkv`, `.m4v`, `.avi`). Límite: `MEDIA_MAX_VIDEO_MB`. |
| `prompt` | texto | Sí | Pregunta o instrucción sobre el video (máx. 4000 caracteres). |
| `system_prompt` | texto | No | Instrucción de contexto opcional (máx. 2000 caracteres). |
| `include_transcript` | booleano | No | Si `true` (por defecto), intenta transcribir la pista de audio con `MEDIA_TRANSCRIPTION_MODEL`. |

### Ejemplo con curl

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/media/videos/analyze ^
  -F "file=@video.mp4" ^
  -F "prompt=Describe lo que ocurre en el video" ^
  -F "include_transcript=true"
```

### Respuesta

```json
{
  "analysis": "El video muestra ...",
  "provider": "openai_compatible",
  "model": "gpt-4o",
  "frames_analyzed": 8,
  "transcript": "Transcripción opcional del audio...",
  "transcript_status": "completed",
  "usage": { "input_tokens": 1200, "output_tokens": 150 }
}
```

### Cómo se procesa el video

1. FFmpeg extrae hasta `MEDIA_VIDEO_MAX_FRAMES` (por defecto 8) fotogramas JPEG muestreados aproximadamente cada `MEDIA_VIDEO_FRAME_INTERVAL_SECONDS` segundos, limitando la duración a `MEDIA_VIDEO_MAX_DURATION_SECONDS` (por defecto 120 s).
2. Si hay pista de audio y `include_transcript=true`, se extrae el audio y se transcribe por separado con `MEDIA_TRANSCRIPTION_MODEL`.
3. Los fotogramas y (opcionalmente) la transcripción se envían al modelo de visión (`LLM_MODEL`) mediante `/chat/completions` con `image_url`.
4. La API **no** envía el archivo de video crudo al endpoint de chat; solo los fotogramas muestreados.

### Errores comunes

| Código | Causa |
|---|---|
| `404` | `LLM_MODEL` no es un modelo de visión válido para el proveedor. |
| `413` | El archivo excede `MEDIA_MAX_VIDEO_MB` (por defecto 50 MB). |
| `415` | Extensión de archivo no admitida para video. |
| `422` | Archivo vacío, dañado o sin contenido de video decodificable. |
| `502` | El proveedor devolvió un error o respuesta incompatible. |
| `503` | Proveedor no configurado (`LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`) o `MEDIA_TRANSCRIPTION_MODEL` no configurado cuando se pide transcripción. |
| `504` | Timeout del proveedor o del procesamiento local (FFmpeg). |

## Limitaciones

- **Video:** no hay comprensión nativa continua del archivo completo. Solo se analizan fotogramas muestreados; eventos entre frames pueden perderse.
- **Audio:** la transcripción depende de que el contenedor (p. ej. MP4) incluya una pista de audio compatible y que el proveedor la admita.
- **No streaming:** cada solicitud es una generación independiente; no hay transmisión en tiempo real.
- **No reintentos automáticos:** si un POST al proveedor falla por timeout, no se reintenta (podría duplicar el consumo/coste).
- **FFmpeg:** el análisis de video requiere `imageio-ffmpeg` (ya en `requirements.txt`). Si no está disponible, el endpoint devuelve `503`.

## Arquitectura

```
Cliente HTTP/JSON
       |
       v
POST /api/v1/media/transcriptions  --> AudioTranscriptionService --> OpenAICompatibleAudioTranscriber --> /audio/transcriptions (Whisper)

POST /api/v1/media/videos/analyze   --> VideoAnalysisService --> FFmpeg (frames + audio)
                                                |                                      |
                                                v                                      v
                                         OpenAICompatibleVisionProvider   OpenAICompatibleAudioTranscriber
                                                |                                      |
                                                v                                      v
                                         /chat/completions (frames)              /audio/transcriptions (opcional)
```

## ¿Cuándo usar cada capacidad?

| Escenario | Endpoint | Modelo |
|---|---|---|
| Preguntar algo al modelo por texto | `/api/v1/llm/ask` | `LLM_MODEL` (chat) |
| Transcribir un archivo de audio a texto | `/api/v1/media/transcriptions` | `MEDIA_TRANSCRIPTION_MODEL` (Whisper) |
| Analizar un video (qué ocurre, describir escenas) | `/api/v1/media/videos/analyze` | `LLM_MODEL` (visión) + opcionalmente `MEDIA_TRANSCRIPTION_MODEL` |