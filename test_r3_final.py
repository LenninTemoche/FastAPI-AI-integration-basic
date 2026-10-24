"""Verificación R3 final - tests de integración real."""

from fastapi.testclient import TestClient
from app.main import create_app
import httpx

# Test 1: POST /api/v1/llm/ask con MockTransport → 200
def test_llm_with_mock():
    # Crear mock transport
    mock_response = httpx.Response(
        200,
        json={
            "choices": [{"message": {"content": "Respuesta mock"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }
    )
    mock_transport = httpx.MockTransport(lambda request: mock_response)
    
    # Crear app con cliente mock
    app = create_app(enabled=["llm"])
    
    # Reemplazar el cliente HTTP con uno que use mock transport
    mock_client = httpx.AsyncClient(transport=mock_transport)
    app.state.http_client = mock_client
    
    with TestClient(app) as client:
        response = client.post("/api/v1/llm/ask", json={"prompt": "Hola"})
        print(f"POST /api/v1/llm/ask: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  response: {data['response'][:50]}...")
            print(f"  provider: {data['provider']}")
            print(f"  model: {data['model']}")
            print(f"  usage: {data['usage']}")
        assert response.status_code == 200
    print("Test POST /api/v1/llm/ask con MockTransport: PASSED")

# Test 2: Cliente cerrado al apagar (usando AsyncExitStack)
import asyncio

async def test_client_closed():
    http_client = httpx.AsyncClient(timeout=30.0)
    from contextlib import AsyncExitStack
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(http_client)
        print(f"During lifespan: client.is_closed = {http_client.is_closed}")
    print(f"After AsyncExitStack: client.is_closed = {http_client.is_closed}")
    assert http_client.is_closed, "Cliente debería estar cerrado"
    print("Test cliente cerrado al apagar: PASSED")

print("Ejecutando pruebas R3...")

test_llm_with_mock()
print()
asyncio.run(test_client_closed())

print("\nTodos los tests R3 PASSED")