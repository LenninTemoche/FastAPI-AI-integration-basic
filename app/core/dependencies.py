"""Punto de composición para servicios y adaptadores de infraestructura."""

from fastapi import Request

from app.core.config import get_settings
from app.integrations.llm.openai_compatible import OpenAICompatibleChatProvider
from app.repositories.in_memory_product_repository import InMemoryProductRepository
from app.services.llm_service import LLMService
from app.services.ports.llm_provider import LLMNotConfiguredError
from app.services.product_service import ProductService


# La implementación por defecto es temporal y local. Para usar otra persistencia,
# se sustituye este enlace por un repositorio compatible con ProductRepository.
_product_repository = InMemoryProductRepository()
_product_service = ProductService(_product_repository)


def get_product_service() -> ProductService:
    """Proporciona el servicio de productos a los endpoints de FastAPI."""
    return _product_service

def get_llm_service(request: Request) -> LLMService:
    """Compone el servicio LLM sin que los endpoints conozcan el proveedor.

    Para cambiar a un proveedor con un protocolo distinto, se añade un adaptador
    que implemente el puerto LLMProvider y se selecciona aquí por configuración.
    """
    settings = get_settings()
    client = getattr(request.app.state, "llm_http_client", None)
    if client is None:
        # Normalmente la vida útil HTTPX la gestiona el lifespan de la aplicación.
        # Esta protección permite devolver un fallo controlado si alguien monta
        # la dependencia fuera del ciclo de vida esperado.
        raise LLMNotConfiguredError

    if settings.llm_provider == "openai_compatible":
        provider = OpenAICompatibleChatProvider(settings=settings, client=client)
        return LLMService(provider=provider)

    # La configuración restringe el valor a los adaptadores implementados.
    raise LLMNotConfiguredError
