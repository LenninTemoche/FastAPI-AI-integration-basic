"""Utilidades para el cliente HTTP compartido."""

from typing import Annotated, Optional

import httpx
from fastapi import Request

HTTP_CLIENT_STATE_KEY = "http_client"


def get_shared_http_client(request: Request) -> httpx.AsyncClient | None:
    """Devuelve el cliente HTTP compartido del estado de la aplicación, o None si no existe."""
    return getattr(request.app.state, HTTP_CLIENT_STATE_KEY, None)