"""Manifiesto del módulo Media."""

from app.core.module import ModuleSpec
from .errors import register_errors
from .router import router

spec = ModuleSpec(
    name="media",
    description="Transcripción de audio y análisis de video por fotogramas",
    router=router,
    register=register_errors,
    requires=("llm",),
)