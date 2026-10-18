"""Caso de uso de generación de texto, independiente del proveedor concreto."""

from app.services.ports.llm_provider import LLMGenerationResult, LLMProvider


class LLMService:
    """Coordina una generación y devuelve un resultado neutral para la API."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def ask(
        self,
        *,
        prompt: str,
        system_prompt: str | None = None,
    ) -> LLMGenerationResult:
        """Ejecuta el caso de uso usando el proveedor inyectado."""
        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            # La API también lo valida con Pydantic; esta comprobación protege
            # llamadas internas que pudieran invocar el servicio directamente.
            raise ValueError("prompt must not be empty")

        normalized_system_prompt = (
            system_prompt.strip() if system_prompt and system_prompt.strip() else None
        )
        return await self._provider.generate(
            prompt=normalized_prompt,
            system_prompt=normalized_system_prompt,
        )
