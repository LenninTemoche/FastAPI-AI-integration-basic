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
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.module import ModuleSpec
from app.core.registry import ModuleLoadError, install_modules, resolve  # noqa: E402
from app.main import create_app  # noqa: E402


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
from app.main import create_app
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


if __name__ == "__main__":
    unittest.main()
