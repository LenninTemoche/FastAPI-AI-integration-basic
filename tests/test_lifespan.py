"""Pruebas de lifespan del cliente HTTP compartido (S5).

Todas usan `with TestClient(...)` (sin `with` el lifespan NO se ejecuta) y aíslan
la configuración del entorno: NO dependen del `.env` local.
"""

import os
import pathlib
import unittest
from contextlib import asynccontextmanager
from unittest.mock import patch

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.http import HTTP_CLIENT_STATE_KEY
from app.core.module import ModuleSpec
from app.factory import create_app, lifespan
from app.modules.media.ports import ExtractedVideoMedia

LLM_OK_BODY = {
    "choices": [{"message": {"content": "Respuesta simulada"}}],
    "usage": {"prompt_tokens": 5, "completion_tokens": 3},
}

AUDIO_OK_BODY = {"text": "  Hola mundo  "}

VISION_OK_BODY = {
    "model": "vision-returned",
    "choices": [{
        "message": {
            "content": None,
            "reasoning_content": "Análisis visual",
        }
    }],
    "usage": {"prompt_tokens": 22, "completion_tokens": 9},
}

AUDIO_FILES = {
    "file": ("audio.mp3", b"fake-audio-bytes", "audio/mpeg"),
}
AUDIO_KEYS = ("text", "provider", "model")

VIDEO_FILES = {
    "file": ("video.mp4", b"fake-video-bytes", "video/mp4"),
}

VIDEO_DATA = {"prompt": "Describe el video"}
VIDEO_KEYS = (
    "analysis",
    "provider",
    "model",
    "frames_analyzed",
    "transcript_status",
)


class FakeVideoProcessor:
    """Procesador falso async para pruebas de servicio."""

    def __init__(self, settings):
        self.frames = (b"frame1", b"frame2")
        self.audio_mp3 = None

    async def extract(
        self,
        *,
        content: bytes,
        filename: str,
        content_type: str = "video/mp4",
        max_frames: int = 8,
        max_duration_seconds: int = 120,
        frame_interval_seconds: int = 5,
        processing_timeout_seconds: float = 60.0,
        include_audio: bool = True,
    ) -> ExtractedVideoMedia:
        return ExtractedVideoMedia(
            frames=self.frames,
            audio_mp3=self.audio_mp3,
            frame_interval_seconds=frame_interval_seconds,
        )


class LifespanTests(unittest.TestCase):
    def setUp(self):
        self._env = patch.dict(os.environ, {
            "LLM_PROVIDER": "openai_compatible",
            "LLM_BASE_URL": "http://127.0.0.1:9/v1",
            "LLM_API_KEY": "k",
            "LLM_MODEL": "m",
            "MEDIA_TRANSCRIPTION_MODEL": "w",
        })
        self._env.start()
        self.addCleanup(self._env.stop)
        get_settings.cache_clear()
        self.addCleanup(get_settings.cache_clear)

    def _patched_client(self, handler, calls):
        """Hace que el cliente CREADO POR EL LIFESPAN use MockTransport (la prueba depende del lifespan)."""
        real = httpx.AsyncClient

        def respond(request):
            calls.append(request)
            return handler(request)

        def factory(*args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(respond)
            return real(*args, **kwargs)

        return patch("app.modules.llm.manifest.httpx.AsyncClient", side_effect=factory)

    # 1) Cadena real: el cliente lo crea el lifespan
    def test_llm_ask_goes_through_lifespan_client(self):
        calls = []
        handler = lambda request: httpx.Response(200, json=LLM_OK_BODY)
        with self._patched_client(handler, calls):
            with TestClient(create_app(enabled=["llm"])) as client:
                response = client.post("/api/v1/llm/ask", json={"prompt": "Hola"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        for key in ("response", "provider", "model", "usage"):
            self.assertIn(key, body)
        self.assertEqual(len(calls), 1)

    # 2) Se cierra al salir
    def test_client_closed_on_shutdown(self):
        with TestClient(create_app(enabled=["llm"])) as client:
            ref = getattr(client.app.state, HTTP_CLIENT_STATE_KEY)
            self.assertFalse(ref.is_closed)
        self.assertTrue(ref.is_closed)

    # 3) No se crea sin necesitarlo
    def test_no_client_created_when_not_needed(self):
        with TestClient(create_app(enabled=["products"])) as client:
            self.assertFalse(hasattr(client.app.state, HTTP_CLIENT_STATE_KEY))

    # 4) Orden con el lifespan REAL de app.factory
    def test_open_close_order_uses_real_lifespan(self):
        events = []

        def make(name):
            @asynccontextmanager
            async def _ls(app):
                events.append(f"open:{name}")
                yield
                events.append(f"close:{name}")
            return _ls

        app = FastAPI(lifespan=lifespan)
        app.state.modules = {
            n: ModuleSpec(name=n, description=n, lifespan=make(n)) for n in ("a", "b", "c")
        }
        with TestClient(app):
            self.assertEqual(events, ["open:a", "open:b", "open:c"])
        self.assertEqual(
            events, ["open:a", "open:b", "open:c", "close:c", "close:b", "close:a"]
        )

    # 5) media arrastra llm
    def test_media_requires_llm(self):
        with TestClient(create_app(enabled=["media"])) as client:
            self.assertTrue(hasattr(client.app.state, HTTP_CLIENT_STATE_KEY))
            self.assertIn("llm", client.app.state.modules)

    # 6a) Audio por el cliente compartido (hermético)
    def test_audio_goes_through_shared_client(self):
        self.assertIsNotNone(AUDIO_OK_BODY, "Completa AUDIO_OK_BODY (COPIAR-DE)")
        self.assertTrue(AUDIO_KEYS, "Completa AUDIO_KEYS (COPIAR-DE)")
        self.assertIsNotNone(AUDIO_FILES, "Completa AUDIO_FILES (COPIAR-DE)")
        calls = []
        handler = lambda request: httpx.Response(200, json=AUDIO_OK_BODY)
        with self._patched_client(handler, calls):
            with TestClient(create_app(enabled=["llm", "media"])) as client:
                response = client.post("/api/v1/media/transcriptions", files=AUDIO_FILES)
        self.assertEqual(response.status_code, 200)
        for key in AUDIO_KEYS:
            self.assertIn(key, response.json())
        self.assertGreaterEqual(len(calls), 1)

    # 6b) Video por el cliente compartido (hermético; FFmpeg simulado)
    def test_video_goes_through_shared_client(self):
        self.assertIsNotNone(AUDIO_OK_BODY, "Completa AUDIO_OK_BODY (COPIAR-DE)")
        self.assertIsNotNone(VISION_OK_BODY, "Completa VISION_OK_BODY (COPIAR-DE)")
        self.assertTrue(VIDEO_KEYS, "Completa VIDEO_KEYS (COPIAR-DE)")
        self.assertIsNotNone(VIDEO_FILES, "Completa VIDEO_FILES (COPIAR-DE)")
        calls = []

        def handler(request):
            body = AUDIO_OK_BODY if request.url.path.endswith("/audio/transcriptions") else VISION_OK_BODY
            return httpx.Response(200, json=body)

        with patch("app.modules.media.deps.FFmpegVideoProcessor", FakeVideoProcessor):
            with self._patched_client(handler, calls):
                with TestClient(create_app(enabled=["llm", "media"])) as client:
                    response = client.post(
                        "/api/v1/media/videos/analyze", files=VIDEO_FILES, data=VIDEO_DATA or {}
                    )
        self.assertEqual(response.status_code, 200)
        for key in VIDEO_KEYS:
            self.assertIn(key, response.json())
        self.assertGreaterEqual(len(calls), 1)

    # 7) Sin `with` el lifespan no corre
    def test_without_with_lifespan_not_executed(self):
        app = create_app(enabled=["llm"])
        self.assertFalse(hasattr(app.state, HTTP_CLIENT_STATE_KEY))
        response = TestClient(app).post("/api/v1/llm/ask", json={"prompt": "Hola"})
        self.assertEqual(response.status_code, 503)

    # 8) Se crea una sola vez
    def test_client_created_once(self):
        count = 0
        original_init = httpx.AsyncClient.__init__

        def counting_init(self_, *args, **kwargs):
            nonlocal count
            count += 1
            return original_init(self_, *args, **kwargs)

        with patch.object(httpx.AsyncClient, "__init__", counting_init):
            with TestClient(create_app(enabled=["llm", "media"])) as client:
                self.assertTrue(hasattr(client.app.state, HTTP_CLIENT_STATE_KEY))
        self.assertEqual(count, 1, f"Esperaba 1 creación, obtuve {count}")

    # 9) Un único titular en app.state
    def test_single_http_client_instance(self):
        with TestClient(create_app(enabled=["llm", "media"])) as client:
            clients = [
                v for v in client.app.state._state.values() if isinstance(v, httpx.AsyncClient)
            ]
            self.assertEqual(len(clients), 1)
            self.assertIs(clients[0], getattr(client.app.state, HTTP_CLIENT_STATE_KEY))

    # Estáticas (propiedad única)
    def test_static_only_llm_manifest_creates_async_client(self):
        found = [
            p.as_posix() for p in pathlib.Path("app").rglob("*.py")
            if "AsyncClient(" in p.read_text(encoding="utf-8")
        ]
        self.assertEqual(found, ["app/modules/llm/manifest.py"], found)

    def test_static_deps_do_not_touch_app_state(self):
        for deps_file in pathlib.Path("app").rglob("modules/*/deps.py"):
            content = deps_file.read_text(encoding="utf-8")
            self.assertNotIn("app.state", content, str(deps_file))
            self.assertNotIn(".state.http_client", content, str(deps_file))

    def test_static_no_legacy_state_key(self):
        for py_file in pathlib.Path("app").rglob("*.py"):
            self.assertNotIn("llm_http_client", py_file.read_text(encoding="utf-8"), str(py_file))


if __name__ == "__main__":
    unittest.main()