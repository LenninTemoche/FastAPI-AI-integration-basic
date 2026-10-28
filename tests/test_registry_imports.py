"""Pruebas de clasificación de errores del registry y fábrica LLM (S6).

Clasifica errores en cuatro clases:
- A: Módulo desconocido
- B: ModuleNotFoundError de paquete externo ausente
- C: Error interno (ModuleNotFoundError cuyo exc.name empieza por "app.")
- D: Otro ImportError (nombre inexistente en paquete instalado)
"""

import importlib.util
import os
import unittest
from unittest.mock import patch

from app.core.module import ModuleSpec
from app.core.registry import ModuleLoadError, resolve
from app.factory import create_app
from app.modules.llm.adapters import build_provider
from app.modules.llm.adapters.openai_compatible import OpenAICompatibleChatProvider
from app.modules.llm.ports import LLMNotConfiguredError


class ClassificationTests(unittest.TestCase):
    """Clasificación de errores de importación en el registry."""

    def test_class_a_unknown_module(self):
        """A: Módulo desconocido → contiene "desconocido", no "dependencia no instalada" ni "Error interno"."""
        try:
            resolve(["_modulo_inexistente_xyz"])
            self.fail("Debería haber lanzado ModuleLoadError")
        except ModuleLoadError as exc:
            msg = str(exc)
            self.assertIn("desconocido", msg.lower())
            self.assertNotIn("dependencia no instalada", msg.lower())
            self.assertNotIn("Error interno", msg)

    def test_class_b_missing_external_dependency(self):
        """B: manifest.py importa paquete externo inexistente → contiene
        "necesita una dependencia no instalada: paquete_inexistente_xyz" y
        "pip install", no contiene "Error interno" ni "desconocido"."""
        import importlib

        original_find_spec = importlib.util.find_spec
        original_import_module = importlib.import_module

        def fake_find_spec(name):
            if name == "app.modules._test_mod_b":
                return importlib.util.spec_from_loader(
                    name, loader=None, origin="app/modules/_test_mod_b/__init__.py"
                )
            if name == "app.modules._test_mod_b.manifest":
                return importlib.util.spec_from_loader(
                    name, loader=None, origin="app/modules/_test_mod_b/manifest.py"
                )
            return original_find_spec(name)

        def fake_import_module(name, *args, **kwargs):
            if name == "app.modules._test_mod_b.manifest":
                raise ModuleNotFoundError(
                    "No module named 'paquete_inexistente_xyz'",
                    name="paquete_inexistente_xyz",
                )
            return original_import_module(name, *args, **kwargs)

        with patch("importlib.util.find_spec", side_effect=fake_find_spec), \
             patch("importlib.import_module", side_effect=fake_import_module):
            try:
                resolve(["_test_mod_b"])
                self.fail("Debería haber lanzado ModuleLoadError")
            except ModuleLoadError as exc:
                msg = str(exc)
                self.assertIn(
                    "necesita una dependencia no instalada: paquete_inexistente_xyz",
                    msg,
                )
                self.assertIn("pip install", msg)
                self.assertNotIn("Error interno", msg)
                self.assertNotIn("desconocido", msg.lower())

    def test_class_c_internal_import_error(self):
        """C: manifest.py importa módulo interno inexistente → contiene
        "Error interno", no contiene "dependencia no instalada" ni "desconocido"."""
        import importlib

        original_find_spec = importlib.util.find_spec
        original_import_module = importlib.import_module

        def fake_find_spec(name):
            if name == "app.modules._test_mod_c":
                return importlib.util.spec_from_loader(
                    name, loader=None, origin="app/modules/_test_mod_c/__init__.py"
                )
            if name == "app.modules._test_mod_c.manifest":
                return importlib.util.spec_from_loader(
                    name, loader=None, origin="app/modules/_test_mod_c/manifest.py"
                )
            return original_find_spec(name)

        def fake_import_module(name, *args, **kwargs):
            if name == "app.modules._test_mod_c.manifest":
                raise ModuleNotFoundError(
                    "No module named 'app.modules._test_mod_c.faltante_interno'",
                    name="app.modules._test_mod_c.faltante_interno",
                )
            return original_import_module(name, *args, **kwargs)

        with patch("importlib.util.find_spec", side_effect=fake_find_spec), \
             patch("importlib.import_module", side_effect=fake_import_module):
            try:
                resolve(["_test_mod_c"])
                self.fail("Debería haber lanzado ModuleLoadError")
            except ModuleLoadError as exc:
                msg = str(exc)
                self.assertIn("Error interno", msg)
                self.assertNotIn("dependencia no instalada", msg)
                self.assertNotIn("desconocido", msg.lower())

    def test_class_d_import_error_not_module_not_found(self):
        """D: manifest.py importa nombre inexistente de paquete instalado
        (from httpx import NoExiste) → contiene "httpx.NoExiste", no contiene
        "desconocido"."""
        import importlib

        original_find_spec = importlib.util.find_spec
        original_import_module = importlib.import_module

        def fake_find_spec(name):
            if name == "app.modules._test_mod_d":
                return importlib.util.spec_from_loader(
                    name, loader=None, origin="app/modules/_test_mod_d/__init__.py"
                )
            if name == "app.modules._test_mod_d.manifest":
                return importlib.util.spec_from_loader(
                    name, loader=None, origin="app/modules/_test_mod_d/manifest.py"
                )
            return original_find_spec(name)

        def fake_import_module(name, *args, **kwargs):
            if name == "app.modules._test_mod_d.manifest":
                raise ModuleNotFoundError(
                    "No module named 'httpx.NoExiste'",
                    name="httpx.NoExiste",
                )
            return original_import_module(name, *args, **kwargs)

        with patch("importlib.util.find_spec", side_effect=fake_find_spec), \
             patch("importlib.import_module", side_effect=fake_import_module):
            try:
                resolve(["_test_mod_d"])
                self.fail("Debería haber lanzado ModuleLoadError")
            except ModuleLoadError as exc:
                msg = str(exc)
                self.assertIn("httpx.NoExiste", msg)
                self.assertNotIn("desconocido", msg.lower())


class BuildProviderTests(unittest.TestCase):
    """Pruebas deterministas para build_provider con normalización."""

    def setUp(self):
        from app.core.config import get_settings
        get_settings.cache_clear()
        os.environ.pop("LLM_PROVIDER", None)

    def tearDown(self):
        from app.core.config import get_settings
        get_settings.cache_clear()
        os.environ.pop("LLM_PROVIDER", None)

    def test_build_provider_openai_compatible_lowercase(self):
        """build_provider acepta 'openai_compatible' en minúsculas."""
        os.environ["LLM_PROVIDER"] = "openai_compatible"
        from app.core.config import get_settings
        import httpx

        settings = get_settings()
        client = httpx.AsyncClient()
        provider = build_provider(settings, client)
        self.assertIsInstance(provider, OpenAICompatibleChatProvider)

    def test_build_provider_openai_compatible_uppercase(self):
        """build_provider normaliza 'OPENAI_COMPATIBLE' a minúsculas."""
        os.environ["LLM_PROVIDER"] = "OPENAI_COMPATIBLE"
        from app.core.config import get_settings
        import httpx

        settings = get_settings()
        client = httpx.AsyncClient()
        provider = build_provider(settings, client)
        self.assertIsInstance(provider, OpenAICompatibleChatProvider)

    def test_build_provider_openai_compatible_mixed_case(self):
        """build_provider normaliza 'OpenAI_Compatible' a minúsculas."""
        os.environ["LLM_PROVIDER"] = "OpenAI_Compatible"
        from app.core.config import get_settings
        import httpx

        settings = get_settings()
        client = httpx.AsyncClient()
        provider = build_provider(settings, client)
        self.assertIsInstance(provider, OpenAICompatibleChatProvider)

    def test_build_provider_openai_compatible_with_spaces(self):
        """build_provider hace strip de espacios."""
        os.environ["LLM_PROVIDER"] = "  openai_compatible  "
        from app.core.config import get_settings
        import httpx

        settings = get_settings()
        client = httpx.AsyncClient()
        provider = build_provider(settings, client)
        self.assertIsInstance(provider, OpenAICompatibleChatProvider)

    def test_build_provider_unknown_raises_not_configured(self):
        """Proveedor desconocido lanza LLMNotConfiguredError."""
        os.environ["LLM_PROVIDER"] = "desconocido"
        from app.core.config import get_settings
        import httpx

        settings = get_settings()
        client = httpx.AsyncClient()
        with self.assertRaises(LLMNotConfiguredError):
            build_provider(settings, client)

    def test_build_provider_key_error_propagates(self):
        """build_provider lanza LLMNotConfiguredError cuando _PROVIDERS tiene
        una clave con valor None (simulado mediante parcheo)."""
        os.environ["LLM_PROVIDER"] = "openai_compatible"
        from app.core.config import get_settings
        import httpx
        from app.modules.llm import adapters

        settings = get_settings()
        client = httpx.AsyncClient()

        with patch.dict(
            adapters._PROVIDERS, {"openai_compatible": None}
        ):
            with self.assertRaises(LLMNotConfiguredError):
                build_provider(settings, client)


if __name__ == "__main__":
    unittest.main()