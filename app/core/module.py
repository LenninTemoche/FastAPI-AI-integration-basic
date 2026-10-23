from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import Callable

from fastapi import APIRouter, FastAPI


@dataclass(frozen=True)
class ModuleSpec:
    """Descripción de un módulo. Cada app/modules/<name>/manifest.py exporta `spec`."""

    name: str                                   # Debe coincidir con el nombre de la carpeta
    description: str
    version: str = "1.0.0"
    router: APIRouter | None = None
    prefix: str | None = None                   # Por defecto: /api/v1/<name>
    requires: tuple[str, ...] = ()              # Otros módulos que deben cargarse antes
    register: Callable[[FastAPI], None] | None = None   # Manejadores de error, middleware...
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]] | None = None