"""Manifiesto del módulo Products."""

from app.core.module import ModuleSpec
from .errors import register_errors
from .router import router

spec = ModuleSpec(
    name="products",
    description="CRUD de demostración (almacenamiento en memoria)",
    router=router,
    register=register_errors,
)