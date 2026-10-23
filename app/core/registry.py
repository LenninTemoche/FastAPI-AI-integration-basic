from __future__ import annotations

import importlib
import logging

from fastapi import FastAPI

from .module import ModuleSpec

log = logging.getLogger(__name__)


class ModuleLoadError(RuntimeError):
    pass


def _load_spec(name: str) -> ModuleSpec:
    path = f"app.modules.{name}.manifest"
    try:
        spec = importlib.import_module(path).spec
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith(f"app.modules.{name}"):
            raise ModuleLoadError(f"Módulo desconocido: '{name}'") from exc
        raise ModuleLoadError(
            f"El módulo '{name}' necesita una dependencia no instalada: {exc.name}"
        ) from exc
    if spec.name != name:
        raise ModuleLoadError(f"spec.name '{spec.name}' no coincide con la carpeta '{name}'")
    return spec


def resolve(enabled: list[str]) -> list[ModuleSpec]:
    """Devuelve los módulos en orden de carga, incluyendo dependencias."""
    ordered: dict[str, ModuleSpec] = {}
    visiting: set[str] = set()

    def visit(name: str) -> None:
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