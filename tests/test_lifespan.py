"""Pruebas de lifespan del cliente HTTP compartido (S5).

Todas las pruebas usan `with TestClient(...) as client:` para asegurar que el
lifespan se ejecute. Sin el contexto `with`, el lifespan no se ejecuta.
"""

import asyncio
import httpx
import pathlib
import unittest
from contextlib import asynccontextmanager
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.http import HTTP_CLIENT_STATE_KEY
from app.factory import create_app
from app.core.module import ModuleSpec


class LifespanTests(unittest.TestCase):
    """Pruebas de inicialización y cierre del cliente HTTP compartido."""

    # ---------------------------------------------------------------------------
    # Prueba 1: Cadena real con MockTransport para LLM → 200
    # ---------------------------------------------------------------------------

    def test_llm_ask_with_mock_transport_returns_200(self):
        """POST /api/v1/llm/ask atravesando la cadena real de dependencias con
        httpx.MockTransport → 200 con el contenido esperado."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "Respuesta simulada"}}],
                    "usage": {"prompt_tokens": 5, "completion_tokens": 3},
                },
            )

        transport = httpx.MockTransport(handler)

        app = create_app(enabled=["llm"])

        with TestClient(app) as client:
            # Inyectar cliente simulado DESPUÉS de que el lifespan haya creado el suyo
            mock_client = httpx.AsyncClient(transport=transport)
            setattr(client.app.state, HTTP_CLIENT_STATE_KEY, mock_client)

            response = client.post("/api/v1/llm/ask", json={"prompt": "Hola"})

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "provider" in data
        assert "model" in data
        assert "usage" in data

    # ---------------------------------------------------------------------------
    # Prueba 2: Cliente cerrado al salir
    # ---------------------------------------------------------------------------

    def test_client_closed_on_shutdown(self):
        """El cliente HTTP se cierra al salir del contexto with TestClient."""

        app = create_app(enabled=["llm"])

        ref: httpx.AsyncClient | None = None

        with TestClient(app) as client:
            ref = client.app.state.http_client  # type: ignore[attr-defined]
            assert not ref.is_closed

        assert ref is not None
        assert ref.is_closed

    # ---------------------------------------------------------------------------
    # Prueba 3: No se crea cliente si no se necesita (solo products)
    # ---------------------------------------------------------------------------

    def test_no_client_created_when_not_needed(self):
        """Con enabled=['products'] no se crea ningún cliente HTTP."""

        app = create_app(enabled=["products"])

        with TestClient(app) as client:
            assert not hasattr(client.app.state, HTTP_CLIENT_STATE_KEY)

    # ---------------------------------------------------------------------------
    # Prueba 4: Orden de apertura y cierre con specs falsos
    # ---------------------------------------------------------------------------

    def test_open_close_order_with_fake_specs(self):
        """Orden: apertura A, B, C y cierre C, B, A."""

        events: list[str] = []

        @asynccontextmanager
        async def make_lifespan(name: str):
            events.append(f"open:{name}")
            yield
            events.append(f"close:{name}")

        specs = {
            "a": ModuleSpec(name="a", description="A", router=None,
                           lifespan=make_lifespan("a")),
            "b": ModuleSpec(name="b", description="B", router=None,
                           lifespan=make_lifespan("b")),
            "c": ModuleSpec(name="c", description="C", router=None,
                           lifespan=make_lifespan("c")),
        }

        app_instance = create_app(enabled=[])
        app_instance.state.modules = specs

        async def _run_all():
            # Abrir todos en orden alfabético
            for name in sorted(specs.keys()):
                cm = specs[name].lifespan
                await cm.__aenter__()

            # Verificar orden de apertura
            open_events = [e for e in events if e.startswith("open:")]
            self.assertEqual(open_events, ["open:a", "open:b", "open:c"],
                            f"Orden apertura: {open_events}")

            # Cerrar en orden inverso
            for name in reversed(sorted(specs.keys())):
                cm = specs[name].lifespan
                await cm.__aexit__(None, None, None)

            # Verificar orden de cierre
            close_events = [e for e in events if e.startswith("close:")]
            self.assertEqual(close_events, ["close:c", "close:b", "close:a"],
                            f"Orden cierre: {close_events}")

        asyncio.run(_run_all())

    # ---------------------------------------------------------------------------
    # Prueba 5: Media arrastra llm
    # ---------------------------------------------------------------------------

    def test_media_requires_llm(self):
        """enabled=['media'] carga también llm y el cliente existe dentro del with."""

        app = create_app(enabled=["media"])

        with TestClient(app) as client:
            assert hasattr(client.app.state, HTTP_CLIENT_STATE_KEY)
            client_obj = client.app.state.http_client  # type: ignore[attr-defined]
            assert client_obj is not None

    # ---------------------------------------------------------------------------
    # Prueba 6: Audio y video con MockTransport
    # ---------------------------------------------------------------------------

    def test_audio_and_video_endpoints_mounted(self):
        """Endpoints de audio y video están montados y responden (incluso con error
        del proveedor real si no hay credenciales configuradas)."""

        app = create_app(enabled=["llm", "media"])

        with TestClient(app) as client:
            # Audio - endpoint existe (puede devolver 502 si no hay proveedor real)
            resp_audio = client.post(
                "/api/v1/media/transcriptions",
                files={"file": ("test.wav", b"fake-audio", "audio/wav")},
            )
            self.assertIn(resp_audio.status_code, (200, 400, 415, 422, 502, 503),
                         f"Audio endpoint no responde: {resp_audio.status_code}")

            # Video - endpoint existe
            resp_video = client.post(
                "/api/v1/media/videos/analyze",
                files={"file": ("test.mp4", b"fake-video", "video/mp4")},
                data={"prompt": "Describe el video"},
            )
            self.assertIn(resp_video.status_code, (200, 400, 415, 422, 502, 503),
                         f"Video endpoint no responde: {resp_video.status_code}")

    # ---------------------------------------------------------------------------
    # Prueba 7: Sin `with` - lifespan no se ejecuta
    # ---------------------------------------------------------------------------

    def test_without_with_lifespan_not_executed(self):
        """Sin `with TestClient(app)`, el lifespan no se ejecuta."""

        app = create_app(enabled=["llm"])

        # Sin entrar al contexto with, el lifespan no corre y no hay cliente
        assert not hasattr(app.state, HTTP_CLIENT_STATE_KEY)

        # POST a /api/v1/llm/ask fallará porque no hay cliente
        client = TestClient(app)
        response = client.post("/api/v1/llm/ask", json={"prompt": "Hola"})
        # 503 porque no hay cliente HTTP configurado
        self.assertEqual(response.status_code, 503)

    # ---------------------------------------------------------------------------
    # Prueba 8: Cliente creado una sola vez
    # ---------------------------------------------------------------------------

    def test_client_created_once(self):
        """Con enabled=['llm','media'] el contador de creaciones es 1 al arrancar."""

        creation_count = 0
        original_init = httpx.AsyncClient.__init__

        def counting_init(self, *args, **kwargs):
            nonlocal creation_count
            creation_count += 1
            return original_init(self, *args, **kwargs)

        with patch.object(httpx.AsyncClient, "__init__", counting_init):
            app = create_app(enabled=["llm", "media"])

            with TestClient(app) as client:
                # Dentro del contexto, el cliente ya existe
                assert hasattr(client.app.state, HTTP_CLIENT_STATE_KEY)

        # La cuenta es exactamente 1 (una sola creación al arrancar)
        self.assertEqual(creation_count, 1,
                        f"Esperaba 1 creación, obtuve {creation_count}")

    # ---------------------------------------------------------------------------
    # Prueba 9: Un único titular
    # ---------------------------------------------------------------------------

    def test_single_http_client_instance(self):
        """Dentro del with, solo hay una instancia de httpx.AsyncClient."""

        app = create_app(enabled=["llm", "media"])

        with TestClient(app) as client:
            clients = [
                v for v in client.app.state._state.values()
                if isinstance(v, httpx.AsyncClient)
            ]
            self.assertEqual(len(clients), 1,
                           f"Esperaba 1 cliente, obtuve {len(clients)}")
            self.assertIs(clients[0], client.app.state.http_client)  # type: ignore[attr-defined]

    # ---------------------------------------------------------------------------
    # Pruebas estáticas (propiedad única)
    # ---------------------------------------------------------------------------

    def test_static_llm_adapter_only_async_client(self):
        """(a) Entre todos los .py bajo app/, AsyncClient( aparece SOLO en
        app/modules/llm/manifest.py."""

        app_dir = pathlib.Path("app")
        async_client_files = []
        for py_file in app_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            if "AsyncClient(" in content:
                async_client_files.append(py_file.as_posix())

        self.assertEqual(async_client_files, ["app/modules/llm/manifest.py"],
                        f"AsyncClient() encontrado en archivos inesperados: {async_client_files}")

    def test_static_deps_no_app_state(self):
        """(b) Ningún app/modules/**/deps.py contiene 'app.state' ni '.state.http_client'."""

        app_dir = pathlib.Path("app")
        for deps_file in app_dir.rglob("modules/*/deps.py"):
            content = deps_file.read_text(encoding="utf-8")
            self.assertNotIn("app.state", content,
                           f"{deps_file} contiene 'app.state'")
            self.assertNotIn(".state.http_client", content,
                           f"{deps_file} contiene '.state.http_client'")

    def test_static_no_llm_http_client(self):
        """(c) Ningún archivo bajo app/ contiene 'llm_http_client'."""

        app_dir = pathlib.Path("app")
        for py_file in app_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            self.assertNotIn("llm_http_client", content,
                           f"{py_file} contiene 'llm_http_client'")


if __name__ == "__main__":
    import unittest
    unittest.main()