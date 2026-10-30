from __future__ import annotations

import importlib
import importlib.util
import logging

from fastapi import FastAPI

from .module import ModuleSpec

log = logging.getLogger(__name__)


class ModuleLoadError(RuntimeError):
    pass


def _load_spec(name: str) -> ModuleSpec:
    path = f"app.modules.{name}.manifest"
    # 1. Si el paquete del módulo no existe, es "módulo desconocido".
    package_path = f"app.modules.{name}"
    try:
        pkg_spec = importlib.util.find_spec(package_path)
    except ValueError:
        pkg_spec = None
    if pkg_spec is None:
        raise ModuleLoadError(f"Módulo desconocido: '{name}'")
    try:
        spec = importlib.import_module(path).spec
    except ModuleNotFoundError as exc:
        exc_name = exc.name or ""
        # 2. Si el nombre del módulo faltante está dentro de app., es un error
        # interno del módulo (import roto), nunca "desconocido".
        if exc_name.startswith("app."):
            raise ModuleLoadError(
                f"Error interno del módulo '{name}': {exc_name}"
            ) from exc
        # 3. Si está fuera de app., es una dependencia Python no instalada.
        raise ModuleLoadError(
            f"El módulo '{name}' necesita una dependencia no instalada: {exc.name}. "
            f"Instala las dependencias del proyecto (p. ej. pip install '.[media]')"
        ) from exc
    except ImportError as exc:
        # 4. Si es otro ImportError (p. ej. “No existe”), también es un error interno
        # y no debe pasar como “dependencia no instalada”.
        raise ModuleLoadError(
            f"Error interno del módulo '{name}': {exc}"
        ) from exc
    
    if spec.name != name:
        raise ModuleLoadError(f"spec.name '{spec.name}' no coincide con la carpeta '{name}'")
    return spec


def resolve(enabled: list[str]) -> list[ModuleSpec]:
    """Devuelve los módulos en orden de carga, incluyendo dependencias."""
    ordered: dict[str, ModuleSpec] = {}
    visiting: set[str] = set()

    def visit(name: str) -> None:
        name = name.strip()
        if not name:
            return
        if name in ordered:
            return
        if name in visiting:
            raise ModuleLoadError(f"Dependencia circular en '{name}'")
        visiting.add(name)
        spec = _load_spec(name)
        for dep in spec.requires:
            visit(dep)
        visiting.discard(name)
        ordered[name] = spec

    for name in enabled:
        visit(name)
    return list(ordered.values())


def install_modules(app: FastAPI, enabled: list[str]) -> list[ModuleSpec]:
    specs = resolve(enabled)
    for spec in specs:
        if spec.register:
            spec.register(app)
        if spec.router:
            app.include_router(
                spec.router,
                prefix=spec.prefix or f"/api/v1/{spec.name}",
                tags=[spec.name],
            )
        log.info("Módulo cargado: %s v%s", spec.name, spec.version)
    app.state.modules = {s.name: s for s in specs}
    return specs