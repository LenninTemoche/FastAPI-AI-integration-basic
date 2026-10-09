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

Comprueba la versión instalada de FastAPI:

```powershell
python -m pip show fastapi
```

Debe indicar la versión `0.143.0`. Si la instalación falla, guarda el mensaje completo del error para diagnosticarlo antes de cambiar versiones o añadir dependencias.

`requirements.txt` fija la versión principal de FastAPI y usa el extra `standard` para contar con el comando `fastapi` y las herramientas estándar del servidor. Las dependencias transitivas se resolverán durante la instalación. Una vez verificada la instalación local, se podrá generar un archivo de bloqueo con la resolución concreta del entorno.

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
| `http://127.0.0.1:8000/docs` | Swagger UI; debe listar `GET /` y permitir ejecutarlo. |
| `http://127.0.0.1:8000/redoc` | Documentación alternativa generada desde OpenAPI. |
| `http://127.0.0.1:8000/openapi.json` | Documento JSON con metadatos y la ruta `/`. |

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
- [ ] `python -m pip show fastapi` confirma FastAPI `0.143.0`.
- [ ] `fastapi dev` inicia el servidor sin errores.
- [ ] `GET /` devuelve HTTP `200` y el JSON esperado.
- [ ] `/docs`, `/redoc` y `/openapi.json` se abren correctamente.
- [ ] `.venv/` no aparece entre los archivos que se subirán a Git.
- [ ] La documentación se actualiza y el cambio se revisa antes de hacer el commit manual.

Marca las casillas solo después de ejecutar y comprobar cada paso en tu equipo. Los comandos incluidos en esta guía no significan que la instalación local ya haya sido ejecutada.

## Referencias oficiales

- [FastAPI — Primeros pasos](https://fastapi.tiangolo.com/tutorial/first-steps/)
- [FastAPI — Entornos virtuales](https://fastapi.tiangolo.com/virtual-environments/)
- [Python 3.13 — `venv`](https://docs.python.org/es/3.13/library/venv.html)
- [FastAPI en PyPI](https://pypi.org/project/fastapi/)
