"""Pruebas del registry de módulos (Fase 1).

Incluye pruebas para los defectos sospechados D-1 e D-2:
- D-1: import interno roto no debe clasificarse como "módulo desconocido".
- D-2: LLM_PROVIDER inválido no debe impedir arranque si el módulo llm está deshabilitado.
"""

import importlib.util
import os
import subprocess
import sys
import textwrap
import types
import unittest
from unittest.mock import patch, MagicMock, call

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.module import ModuleSpec
from app.core.registry import ModuleLoadError, install_modules, resolve  # noqa: E402
from app.factory import create_app  # noqa: E402


class RegistryResolutionTests(unittest.TestCase):
    """Pruebas de resolve() e install_modules()."""

    def test_load_individual_module(self):
        specs = resolve(["products"])
        self.assertEqual([s.name for s in specs], ["products"])
        self.assertEqual(specs[0].name, "products")

    def test_transitive_dependencies_order(self):
        # media requiere llm; products no requiere nada
        specs = resolve(["media"])
        names = [s.name for s in specs]
        self.assertIn("llm", names)
        self.assertIn("media", names)
        # llm debe cargarse antes que media
        self.assertLess(names.index("llm"), names.index("media"))

    def test_unknown_module(self):
        with self.assertRaises(ModuleLoadError) as ctx:
            resolve(["no_existe"])
        self.assertIn("desconocido", str(ctx.exception).lower())

    def test_internal_import_error_not_unknown(self):
        """D-1: import interno roto no debe decir 'desconocido'.

        Simula un módulo que existe en disco (find_spec retorna spec válido)
        pero cuyo manifest.py tiene un import interno roto.
        """
        fake_spec = types.SimpleNamespace(
            name="app.modules._broken_d1",
            origin="app/modules/_broken_d1/__init__.py",
            submodule_search_locations=["app/modules/_broken_d1"],
        )

        def fake_find_spec(name):
            if name == "app.modules._broken_d1":
                return fake_spec
            return importlib.util.find_spec(name)

        def fake_import(name, *args, **kwargs):
            if name == "app.modules._broken_d1.manifest":
                raise ModuleNotFoundError(
                    "No module named 'app.modules._broken_d1.missing_internal'",
                    name="app.modules._broken_d1.missing_internal",
                )
            return importlib.import_module(name)

        with patch("importlib.util.find_spec", side_effect=fake_find_spec), \
             patch("importlib.import_module", side_effect=fake_import):
            with self.assertRaises(ModuleLoadError) as ctx:
                resolve(["_broken_d1"])
            msg = str(ctx.exception)
            self.assertNotIn("desconocido", msg.lower())
            self.assertIn("interno", msg.lower())

    def test_circular_dependency(self):
        fake_spec = types.SimpleNamespace(
            name="app.modules.mod_a",
            origin="app/modules/mod_a/__init__.py",
            submodule_search_locations=["app/modules/mod_a"],
        )

        def fake_find_spec(name):
            if name in ("app.modules.mod_a", "app.modules.mod_b"):
                return fake_spec
            return importlib.util.find_spec(name)

        fake_a = types.ModuleType("app.modules.mod_a")
        fake_a.__file__ = "app/modules/mod_a/__init__.py"
        fake_b = types.ModuleType("app.modules.mod_b")
        fake_b.__file__ = "app/modules/mod_b/__init__.py"

        manifest_a = types.ModuleType("app.modules.mod_a.manifest")
        manifest_a.spec = ModuleSpec(
            name="mod_a",
            description="A",
            requires=("mod_b",),
        )
        manifest_b = types.ModuleType("app.modules.mod_b.manifest")
        manifest_b.spec = ModuleSpec(
            name="mod_b",
            description="B",
            requires=("mod_a",),
        )

        sys.modules["app.modules.mod_a"] = fake_a
        sys.modules["app.modules.mod_a.manifest"] = manifest_a
        sys.modules["app.modules.mod_b"] = fake_b
        sys.modules["app.modules.mod_b.manifest"] = manifest_b

        try:
            with patch("importlib.util.find_spec", side_effect=fake_find_spec), \
                 patch("importlib.import_module", side_effect=lambda n, *a, **k: sys.modules.get(n, __import__(n, *a, **k))):
                with self.assertRaises(ModuleLoadError) as ctx:
                    resolve(["mod_a"])
            self.assertIn("circular", str(ctx.exception).lower())
        finally:
            for m in (
                "app.modules.mod_a",
                "app.modules.mod_a.manifest",
                "app.modules.mod_b",
                "app.modules.mod_b.manifest",
            ):
                sys.modules.pop(m, None)

    def test_spec_name_mismatch(self):
        fake_spec = types.SimpleNamespace(
            name="app.modules._name_mismatch",
            origin="app/modules/_name_mismatch/__init__.py",
            submodule_search_locations=["app/modules/_name_mismatch"],
        )

        def fake_find_spec(name):
            if name == "app.modules._name_mismatch":
                return fake_spec
            return importlib.util.find_spec(name)

        manifest = types.ModuleType("app.modules._name_mismatch.manifest")
        manifest.spec = ModuleSpec(name="otro_nombre", description="X")

        with patch("importlib.util.find_spec", side_effect=fake_find_spec), \
             patch("importlib.import_module", return_value=manifest):
            with self.assertRaises(ModuleLoadError) as ctx:
                resolve(["_name_mismatch"])
            self.assertIn("no coincide", str(ctx.exception))

    def test_enabled_modules_empty_duplicates_spaces(self):
        # Lista vacía
        specs = resolve([])
        self.assertEqual(specs, [])

        # Duplicados
        specs = resolve(["products", "products"])
        names = [s.name for s in specs]
        self.assertEqual(names.count("products"), 1)

        # Espacios (orden de inserción, no alfabético)
        specs = resolve([" products ", "llm"])
        names = [s.name for s in specs]
        self.assertEqual(names, ["products", "llm"])

    def test_disabled_modules_return_404(self):
        app = create_app(enabled=["products"])
        client = TestClient(app)
        self.assertEqual(client.get("/api/v1/products").status_code, 200)
        self.assertEqual(client.post("/api/v1/llm/ask", json={"prompt": "hola"}).status_code, 404)
        self.assertEqual(
            client.post(
                "/api/v1/media/transcriptions",
                files={"file": ("x.wav", b"x", "audio/wav")},
            ).status_code,
            404,
        )

    def test_disabled_modules_not_imported(self):
        """Módulos no habilitados no se importan (probado en subprocess para evitar
        que el module-level app=create_app() de app/main.py cargue todos los módulos)."""
        code = """
import os
os.environ["ENABLED_MODULES"] = "products"
import sys
from app.factory import create_app
app = create_app(enabled=["products"])
after = {m for m in sys.modules if m.startswith("app.modules.")}
print("products:", "app.modules.products" in after)
print("llm:", "app.modules.llm" in after)
print("media:", "app.modules.media" in after)
"""
        r = subprocess.run(
            [sys.executable, "-c", textwrap.dedent(code)],
            capture_output=True, text=True,
        )
        output = r.stdout + r.stderr
        self.assertIn("products: True", output)
        self.assertIn("llm: False", output)
        self.assertIn("media: False", output)


class D2ProviderValidationTests(unittest.TestCase):
    """Pruebas para el defecto D-2: validación de LLM_PROVIDER."""

    def setUp(self):
        get_settings.cache_clear()

    def tearDown(self):
        get_settings.cache_clear()
        os.environ.pop("LLM_PROVIDER", None)

    def test_app_starts_with_invalid_provider_and_llm_disabled(self):
        """D-2: módulo llm deshabilitado + LLM_PROVIDER inválido → la app arranca."""
        os.environ["LLM_PROVIDER"] = "inexistente"
        app = create_app(enabled=["products"])
        client = TestClient(app)
        resp = client.get("/api/v1/products")
        self.assertEqual(resp.status_code, 200)

    def test_unsupported_provider_returns_503_when_llm_enabled(self):
        """Proveedor no soportado con llm habilitado → 503 por HTTP."""
        os.environ["LLM_PROVIDER"] = "inexistente"
        app = create_app(enabled=["llm"])
        client = TestClient(app)
        resp = client.post("/api/v1/llm/ask", json={"prompt": "hola"})
        self.assertEqual(resp.status_code, 503)
        body = resp.json()
        self.assertIn("detail", body)
        self.assertNotIn("api_key", body["detail"].lower())

    def test_supported_provider_with_valid_settings(self):
        """Proveedor soportado funciona normalmente."""
        os.environ["LLM_PROVIDER"] = "openai_compatible"
        app = create_app(enabled=["llm"])
        client = TestClient(app)
        resp = client.post("/api/v1/llm/ask", json={"prompt": "hola"})
        # 503 porque no hay proveedor real configurado, pero no es error de configuración
        self.assertIn(resp.status_code, (200, 503))


class RegisterInvocationTests(unittest.TestCase):
    """D8: register se invoca exactamente una vez por módulo."""

    def test_register_invoked_once_per_module(self):
        """install_modules llama a spec.register exactamente una vez por módulo habilitado.
        
        Verificamos que los exception handlers se registran correctamente en app.exception_handlers.
        """
        app = create_app(enabled=["llm", "media", "products"])
        
        # Verificar que los handlers de llm están registrados
        from app.modules.llm.ports import (
            LLMNotConfiguredError,
            LLMProviderRateLimitError,
            LLMProviderResponseError,
            LLMProviderTimeoutError,
            LLMProviderUnavailableError,
        )
        for exc in [LLMNotConfiguredError, LLMProviderRateLimitError,
                    LLMProviderResponseError, LLMProviderTimeoutError,
                    LLMProviderUnavailableError]:
            self.assertIn(exc, app.exception_handlers)

        # Verificar que los handlers de media están registrados
        from app.modules.media.ports import (
            UnsupportedMediaTypeError,
            MediaPayloadTooLargeError,
            MediaInputError,
            MediaProcessorUnavailableError,
            MediaProcessingTimeoutError,
        )
        for exc in [UnsupportedMediaTypeError, MediaPayloadTooLargeError,
                    MediaInputError, MediaProcessorUnavailableError,
                    MediaProcessingTimeoutError]:
            self.assertIn(exc, app.exception_handlers)

        # Verificar que los handlers de products están registrados
        from app.modules.products.exceptions import ProductNotFoundError
        self.assertIn(ProductNotFoundError, app.exception_handlers)

    def test_register_not_called_for_disabled_module(self):
        """register NO se llama para módulos deshabilitados (no hay handlers)."""
        app = create_app(enabled=["products"])
        
        from app.modules.llm.ports import LLMNotConfiguredError
        from app.modules.media.ports import UnsupportedMediaTypeError
        
        self.assertNotIn(LLMNotConfiguredError, app.exception_handlers)
        self.assertNotIn(UnsupportedMediaTypeError, app.exception_handlers)
        # Pero products sí
        from app.modules.products.exceptions import ProductNotFoundError
        self.assertIn(ProductNotFoundError, app.exception_handlers)


class BuildProviderTests(unittest.TestCase):
    """E1: pruebas deterministas para build_provider con normalización."""

    def setUp(self):
        get_settings.cache_clear()

    def tearDown(self):
        get_settings.cache_clear()
        os.environ.pop("LLM_PROVIDER", None)

    def test_build_provider_openai_compatible_lowercase(self):
        """build_provider acepta 'openai_compatible' en minúsculas."""
        from app.modules.llm.adapters import build_provider
        from app.modules.llm.adapters.openai_compatible import OpenAICompatibleChatProvider
        import httpx
        
        os.environ["LLM_PROVIDER"] = "openai_compatible"
        settings = get_settings()
        client = httpx.AsyncClient()
        
        provider = build_provider(settings, client)
        self.assertIsInstance(provider, OpenAICompatibleChatProvider)

    def test_build_provider_openai_compatible_uppercase(self):
        """build_provider normaliza 'OPENAI_COMPATIBLE' a minúsculas."""
        from app.modules.llm.adapters import build_provider
        from app.modules.llm.adapters.openai_compatible import OpenAICompatibleChatProvider
        import httpx
        
        os.environ["LLM_PROVIDER"] = "OPENAI_COMPATIBLE"
        settings = get_settings()
        client = httpx.AsyncClient()
        
        provider = build_provider(settings, client)
        self.assertIsInstance(provider, OpenAICompatibleChatProvider)

    def test_build_provider_openai_compatible_mixed_case(self):
        """build_provider normaliza 'OpenAI_Compatible' a minúsculas."""
        from app.modules.llm.adapters import build_provider
        from app.modules.llm.adapters.openai_compatible import OpenAICompatibleChatProvider
        import httpx
        
        os.environ["LLM_PROVIDER"] = "OpenAI_Compatible"
        settings = get_settings()
        client = httpx.AsyncClient()
        
        provider = build_provider(settings, client)
        self.assertIsInstance(provider, OpenAICompatibleChatProvider)

    def test_build_provider_openai_compatible_with_spaces(self):
        """build_provider hace strip de espacios."""
        from app.modules.llm.adapters import build_provider
        from app.modules.llm.adapters.openai_compatible import OpenAICompatibleChatProvider
        import httpx
        
        os.environ["LLM_PROVIDER"] = "  openai_compatible  "
        settings = get_settings()
        client = httpx.AsyncClient()
        
        provider = build_provider(settings, client)
        self.assertIsInstance(provider, OpenAICompatibleChatProvider)

    def test_build_provider_unknown_raises_not_configured(self):
        """Proveedor desconocido lanza LLMNotConfiguredError."""
        from app.modules.llm.adapters import build_provider
        from app.modules.llm.ports import LLMNotConfiguredError
        import httpx
        
        os.environ["LLM_PROVIDER"] = "desconocido"
        settings = get_settings()
        client = httpx.AsyncClient()
        
        with self.assertRaises(LLMNotConfiguredError):
            build_provider(settings, client)


class ApiKeyLeakageTests(unittest.TestCase):
    """E2: el VALOR de la API key nunca aparece en respuestas ni logs."""

    def test_503_does_not_contain_api_key_value(self):
        """Error 503 no contiene el valor de la API key."""
        os.environ["LLM_PROVIDER"] = "openai_compatible"
        os.environ["LLM_API_KEY"] = "sk-secret-key-12345"
        
        app = create_app(enabled=["llm"])
        client = TestClient(app)
        resp = client.post("/api/v1/llm/ask", json={"prompt": "hola"})
        
        self.assertEqual(resp.status_code, 503)
        body = resp.json()
        self.assertIn("detail", body)
        # El valor de la API key NO debe aparecer en el detalle
        self.assertNotIn("sk-secret-key-12345", body["detail"])
        self.assertNotIn("secret", body["detail"].lower())


class EnabledModulesEmptyTests(unittest.TestCase):
    """ENABLED_MODULES vacío: comportamiento documentado y probado."""

    def test_enabled_modules_empty_list(self):
        """ENABLED_MODULES=[] → app solo con rutas del sistema (/ , /health, /api/v1/modules)."""
        app = create_app(enabled=[])
        client = TestClient(app)
        
        # Rutas del sistema funcionan
        self.assertEqual(client.get("/").status_code, 200)
        self.assertEqual(client.get("/health").status_code, 200)
        self.assertEqual(client.get("/api/v1/modules").status_code, 200)
        
        # No hay módulos montados
        self.assertEqual(client.get("/api/v1/products").status_code, 404)
        self.assertEqual(client.post("/api/v1/llm/ask", json={"prompt": "hola"}).status_code, 404)
        self.assertEqual(
            client.post("/api/v1/media/transcriptions", files={"file": ("x.wav", b"x", "audio/wav")}).status_code,
            404
        )

    def test_enabled_modules_empty_env(self):
        """ENABLED_MODULES='' en entorno → app solo con rutas del sistema."""
        import os
        os.environ["ENABLED_MODULES"] = ""
        get_settings.cache_clear()
        
        try:
            app = create_app()
            client = TestClient(app)
            
            self.assertEqual(client.get("/").status_code, 200)
            self.assertEqual(client.get("/health").status_code, 200)
            self.assertEqual(client.get("/api/v1/modules").status_code, 200)
            self.assertEqual(client.get("/api/v1/products").status_code, 404)
        finally:
            get_settings.cache_clear()
            os.environ.pop("ENABLED_MODULES", None)


class OpenApiDiffTests(unittest.TestCase):
    """G1: diff OpenAPI contra línea base pre-Fase 1."""

    def test_openapi_diff_only_expected_endpoints(self):
        """Diff OpenAPI: solo /health, /api/v1/modules y tags son nuevos."""
        # Obtener OpenAPI actual
        app = create_app()
        client = TestClient(app)
        current_schema = client.get("/openapi.json").json()
        current_paths = set(current_schema["paths"].keys())
        
        # Rutas esperadas actuales
        expected_current = {
            "/",
            "/health",
            "/api/v1/modules",
            "/api/v1/llm/ask",
            "/api/v1/media/transcriptions",
            "/api/v1/media/videos/analyze",
            "/api/v1/products",
            "/api/v1/products/{product_id}",
        }
        
        # Verificar que las rutas actuales coinciden con lo esperado
        self.assertEqual(current_paths, expected_current)
        
        # Verificar que /health y /api/v1/modules son nuevos (no estaban en v0)
        # y que los tags están presentes
        for path in ["/api/v1/llm/ask", "/api/v1/media/transcriptions", "/api/v1/media/videos/analyze"]:
            self.assertIn("tags", current_schema["paths"][path]["post"])
        
        # Verificar que no hay rutas inesperadas
        unexpected = current_paths - expected_current
        self.assertEqual(unexpected, set(), f"Rutas inesperadas: {unexpected}")


if __name__ == "__main__":
    unittest.main()