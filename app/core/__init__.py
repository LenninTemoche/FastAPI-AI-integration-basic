"""Configuración transversal de la aplicación."""

from .config import Settings, get_settings
from .module import ModuleSpec
from .registry import ModuleLoadError, install_modules, resolve
from .system import router as system_router

__all__ = [
    "Settings",
    "get_settings",
    "ModuleSpec",
    "ModuleLoadError",
    "install_modules",
    "resolve",
    "system_router",
]