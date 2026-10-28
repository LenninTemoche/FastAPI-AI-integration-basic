# Sección 2 — Entorno de desarrollo y primer endpoint

Esta guía prepara el entorno local para **Python 3.13 en Windows** y ejecuta la primera aplicación FastAPI.

> Alcance de esta sección: instalación del entorno, una ruta `GET /` y comprobación de la documentación automática. Los parámetros, esquemas Pydantic, CRUD, routers de dominio y la integración LLM se implementarán en las secciones correspondientes.

## 1. Requisitos

- Windows 10/11.
- Python 3.13 instalado.
- Git.
- VS Code o un IDE equivalente.
- Una terminal PowerShell abierta en la raíz del repositorio.

Comprueba que el lanzador de Python identifica la versión requerida:

```powershell
py -3.13 --version
```

El resultado debe comenzar con `Python 3.13`. Si el comando falla, instala Python 3.13 desde [python.org](https://www.python.org/downloads/) y vuelve a comprobarlo. No continúes usando una versión distinta sin actualizar primero la decisión del proyecto.

## 2. Crear el entorno virtual

Desde la raíz de `FastAPI-AI-integration-basic`:

```powershell
py -3.13 -m venv .venv
```

Activa el entorno:

```powershell
.\.venv\Scripts\Activate.ps1
```

En caso de que PowerShell bloquee la activación por la política de ejecución, puedes ejecutar la siguiente instrucción **solo para la sesión actual**, si las políticas del equipo lo permiten, y volver a activar el entorno:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

La activación no es imprescindible para invocar el intérprete del entorno, pero sí facilita los siguientes comandos. Alternativamente, usa siempre `.\.venv\Scripts\python.exe` (sin el espacio inicial) en lugar de `python`.

Verifica qué intérprete se ejecuta:

```powershell
python --version
python -c "import sys; print(sys.executable)"
```

La ruta que se muestra debe apuntar al directorio `.venv` del repositorio.

## 3. Instalar dependencias

Actualiza `pip` dentro del entorno e instala la dependencia definida por el proyecto:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`requirements.txt` es derivado de `pyproject.toml` (fuente única) y contiene:
```
-e .[media,dev]
```

Esto instala el paquete en modo editable con los extras `media` (para `imageio-ffmpeg` y `python-multipart`) y `dev` (para pruebas). `python-multipart` se declara en el extra `media` porque el módulo `media` lo usa directamente (`UploadFile`/`Form`). Hoy también llega con `fastapi[standard]` (dependencia base), por lo que ya está presente en una instalación base; el único paquete cuya ausencia distingue una instalación mínima es `imageio-ffmpeg`.

Para una instalación mínima sin extras:

```powershell
python -m pip install .
```

Comprueba la versión instalada de FastAPI:

```powershell
python -m pip show fastapi
```

Debe indicar la versión `0.161.1`. Si la instalación falla, guarda el mensaje completo del error para diagnosticarlo antes de cambiar versiones o añadir dependencias.

**Importante:** `imageio-ffmpeg` se importa de forma perezosa en `app/modules/media/adapters/ffmpeg_video_processor.py` (dentro de `_extract_sync`). Por tanto `create_app(enabled=["media"])` funciona sin el extra; solo el análisis de video devuelve `503` cuando se invoca. Para usar el análisis de video, instala el extra: `pip install ".[media]"` o usa `ENABLED_MODULES=products` para evitar cargar el módulo `media`.

## Archivo de restricciones (constraints.txt)

Para reproducir exactamente el entorno de validación, se incluye `constraints.txt` en la raíz del repositorio, generado con `pip freeze` desde un entorno limpio (Windows + Python 3.13):

```powershell
python -m pip install -c constraints.txt -r requirements.txt
```

Límites (V7): son 64 pines generados en Windows con Python 3.13; incluye `colorama` y omite `uvloop`, por lo que no es un lock multiplataforma. Úsalo solo para reproducir el entorno de validación en la misma plataforma.

## Ejecutar la suite de pruebas

Desde la raíz del repositorio, con el entorno virtual activado:

```powershell
python -m pytest -q
```

Resultado real medido en esta sesión (Python 3.13.9, `fix/fase1-cierre`, HEAD `16dab3b` en el momento de medir): **172 passed, 0 failed, 0 skipped** en 27.99s, con `LLM_API_KEY`, `LLM_BASE_URL` y `LLM_MODEL` definidas. Sin ellas falla 1 test (ver `docs/phase1-closure.md`, V4 y P1).

Recuento por comando de recolección:

```powershell
python -m pytest --collect-only -q
```
→ `172 tests collected`

**Nota importante (V4):** la suite no es hermética. Sin `LLM_API_KEY`, `LLM_BASE_URL` y `LLM_MODEL` configurados, `test_lifespan.py::LifespanTests::test_llm_ask_with_mock_transport_returns_200` falla (recibe `503`, espera `200`) porque `get_settings()` lee el entorno. Pendiente: hacer la suite hermética para que pase sin credenciales.

## 4. Estructura creada en esta sección

```text
FastAPI-AI-integration-basic/
├── app/
│   ├── __init__.py
│   └── main.py
├── docs/
│   └── setup.md
├── pyproject.toml
├── requirements.txt
├── README.md
└── ...documentación de la sección 1
```

`app/main.py` es el punto de entrada de esta aplicación mínima. `app/__init__.py` hace explícito que `app` es un paquete Python. No se han creado routers ni capas de servicio todavía porque pertenecen a etapas posteriores.

**Importar `app.main` con dependencias mínimas:**

Con la instalación mínima (`. ` sin extras), `import app.main` funciona correctamente: `app/main.py` importa `app.factory`, que a su vez importa `app.core.system`, `app.core.config` y `app.core.registry`; ninguno de ellos depende de `imageio-ffmpeg`. Al importar `app.main` se ejecuta `app = create_app()` a nivel de módulo (se cargan los módulos de `ENABLED_MODULES`), pero el import de `imageio_ffmpeg` sigue siendo perezoso.

> Ver [Arquitectura Fase 1](architecture.md#1-estilo-arquitectónico).

> **Nota:** En la Fase 1 (arquitectura modular), la estructura evoluciona a:
> ```text
> app/
> ├── main.py                 # create_app(enabled=...)
> ├── core/                   # config, module, registry, system, schemas
> └── modules/
>     ├── llm/                # Generación de texto
>     ├── media/              # Audio + Video
>     └── products/           # CRUD demo
> ```
> Ver [Arquitectura Fase 1](architecture.md#1-estilo-arquitectónico).

## 5. Ejecutar la API

Asegúrate de estar en la raíz del repositorio y de tener el entorno virtual activado. El `pyproject.toml` registra `app.main:app` como punto de entrada para que las herramientas puedan localizar la aplicación. Inicia el servidor con:

```powershell
fastapi dev
```

El servidor de desarrollo suele quedar disponible en `http://127.0.0.1:8000`. Mantén esa terminal abierta mientras pruebas la API. Para detenerlo, utiliza `Ctrl+C`.

Si PowerShell no encuentra el comando `fastapi`, verifica que `.venv` está activado y que la instalación terminó correctamente. Como alternativa, invoca el ejecutable del entorno:

```powershell
.\.venv\Scripts\fastapi.exe dev
```

No expongas el servidor de desarrollo a Internet; en esta etapa se ejecuta solo en el equipo local.

## 6. Validar en el navegador

Con el servidor activo, abre estas direcciones:

| URL | Resultado esperado |
|---|---|
| `http://127.0.0.1:8000/` | JSON con `message`, `status` y `version`. |
| `http://127.0.0.1:8000/health` | `{"status":"ok"}` — health check. |
| `http://127.0.0.1:8000/api/v1/modules` | Lista módulos activos. |
| `http://127.0.0.1:8000/docs` | Swagger UI; debe listar endpoints y permitir ejecutarlos. |
| `http://127.0.0.1:8000/redoc` | Documentación alternativa generada desde OpenAPI. |
| `http://127.0.0.1:8000/openapi.json` | Documento JSON con metadatos y todas las rutas. |

La respuesta de `GET /` debe ser similar a:

```json
{
  "message": "FastAPI AI Integration Basic está funcionando.",
  "status": "ok",
  "version": "0.1.0"
}
```

En Swagger UI, pulsa `GET /`, luego **Try it out** y **Execute**. Confirma que la respuesta HTTP sea `200`.

## 7. Criterios de cierre de la sección 2

- [ ] `py -3.13 --version` confirma Python 3.13.
- [ ] La instalación de `requirements.txt` termina correctamente dentro de `.venv`.
- [ ] `python -m pip show fastapi` confirma FastAPI `0.161.1`.
- [ ] `fastapi dev` inicia el servidor sin errores.
- [ ] `GET /` devuelve HTTP `200` y el JSON esperado.
- [ ] `GET /health` devuelve HTTP `200` con `{"status":"ok"}`.
- [ ] `GET /api/v1/modules` devuelve lista de módulos activos.
- [ ] `/docs`, `/redoc` y `/openapi.json` se abren correctamente.
- [ ] `.venv/` no aparece entre los archivos que se subirán a Git.
- [ ] La documentación se actualiza y el cambio se revisa antes de hacer el commit manual.

Marca las casillas solo después de ejecutar y comprobar cada paso en tu equipo. Los comandos incluidos en esta guía no significan que la instalación local ya haya sido ejecutada.

## Referencias oficiales

- [FastAPI — Primeros pasos](https://fastapi.tiangolo.com/tutorial/first-steps/)
- [FastAPI — Entornos virtuales](https://fastapi.tiangolo.com/virtual-environments/)
- [Python 3.13 — `venv`](https://docs.python.org/es/3.13/library/venv.html)
- [FastAPI en PyPI](https://pypi.org/project/fastapi/)