"""Configuración externa de la aplicación.

Los secretos se cargan desde variables de entorno o un archivo .env local.
Este módulo nunca imprime ni serializa la API key.
"""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import AnyHttpUrl, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración validada al arrancar la aplicación."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    llm_provider: Literal["openai_compatible"] = "openai_compatible"
    llm_api_key: SecretStr | None = None
    llm_base_url: AnyHttpUrl | None = None
    llm_model: Annotated[str | None, Field(min_length=1, max_length=200)] = None
    llm_timeout_seconds: Annotated[float, Field(gt=0, le=120)] = 30.0
    llm_max_tokens: Annotated[int, Field(ge=1, le=4096)] = 512
    llm_temperature: Annotated[float, Field(ge=0, le=2)] = 0.2

    @model_validator(mode="after")
    def require_secure_external_llm_url(self) -> "Settings":
        """Evita enviar una API key por HTTP a un host remoto sin cifrado."""
        base_url = self.llm_base_url
        if base_url is None or base_url.scheme == "https":
            return self

        local_hosts = {"localhost", "127.0.0.1", "::1"}
        if base_url.host not in local_hosts:
            raise ValueError(
                "LLM_BASE_URL must use HTTPS unless it points to a loopback host."
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelve la configuración cacheada para la aplicación actual."""
    return Settings()
