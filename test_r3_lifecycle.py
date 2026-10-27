"""Verificación R3 con TestClient (que ejecuta lifespan)."""

from fastapi.testclient import TestClient
from app.main import create_app

# Test 1: Con llm habilitado, cliente HTTP creado
with TestClient(create_app(enabled=["llm"])) as client:
    app = client.app
    print(f"Test 1 - llm enabled: http_client exists = {hasattr(app.state, 'http_client')}")
    if hasattr(app.state, 'http_client'):
        print(f"  client type: {type(app.state.http_client)}")
        print(f"  client closed: {app.state.http_client.is_closed}")

# Test 2: Con media habilitado, cliente HTTP creado
with TestClient(create_app(enabled=["media"])) as client:
    app = client.app
    print(f"Test 2 - media enabled: http_client exists = {hasattr(app.state, 'http_client')}")

# Test 3: Con products solo, NO cliente HTTP
with TestClient(create_app(enabled=["products"])) as client:
    app = client.app
    print(f"Test 3 - products only: http_client exists = {hasattr(app.state, 'http_client')}")

# Test 4: Con none, NO cliente HTTP
with TestClient(create_app(enabled=[])) as client:
    app = client.app
    print(f"Test 4 - none: http_client exists = {hasattr(app.state, 'http_client')}")

# Test 5: Verificar que el cliente se cierra correctamente
import asyncio

async def test_client_lifecycle():
    app = create_app(enabled=["llm"])
    async with TestClient(app) as client:
        app = client.app
        client_obj = app.state.http_client
        print(f"During lifespan: client.is_closed = {client_obj.is_closed}")
    
    # Después del TestClient, el cliente debería estar cerrado
    print(f"After TestClient: client.is_closed = {app.state.http_client.is_closed}")

asyncio.run(test_client_lifecycle())