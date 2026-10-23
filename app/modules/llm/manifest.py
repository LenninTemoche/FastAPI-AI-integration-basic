"""Manifiesto del módulo LLM."""

from app.core.module import ModuleSpec
from .errors import register_errors
from .router import router

spec = ModuleSpec(
    name="llm",
    description="Generación de texto con proveedor LLM configurable (local o API key)",
    router=router,
    register=register_errors,
)