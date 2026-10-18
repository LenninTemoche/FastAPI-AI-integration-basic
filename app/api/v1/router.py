"""Router agregador de todas las rutas públicas de la versión 1."""

from fastapi import APIRouter

from app.api.v1.endpoints.llm import router as llm_router
from app.api.v1.endpoints.products import router as products_router

router = APIRouter(prefix="/api/v1")
router.include_router(llm_router)
router.include_router(products_router)
