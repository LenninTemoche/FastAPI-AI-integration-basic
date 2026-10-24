"""Punto de entrada principal para desarrollo y producción.

Reexporta la fábrica de la aplicación para compatibilidad con `fastapi dev`
y permite ejecutar directamente con `python -m app.main`.
"""

from app.factory import create_app

# Instancia de la aplicación para `fastapi dev` y `uvicorn app.main:app`
app = create_app()