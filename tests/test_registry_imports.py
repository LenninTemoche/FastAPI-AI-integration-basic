"""Pruebas de clasificación de errores del registry y fábrica LLM (S6).

Clases: A módulo desconocido; B dependencia externa ausente; C error interno
(ModuleNotFoundError dentro de app.); D otro ImportError. Usa módulos temporales
REALES bajo app/modules (sin parchear importlib).
"""

import asyncio
import importlib
import os
import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

import app.modules
from app.core.config import get_settings
from app.core.registry import ModuleLoadError, resolve
from app.modules.llm import adapters
from app.modules.llm.adapters import build_provider
from app.modules.llm.adapters.openai_compatible import OpenAICompatibleChatProvider
from app.modules.llm.ports import LLMNotConfiguredError

MODS = Path(app.modules.__file__).parent


def _drop_temp_module(name: str) -> None:
    shutil.rmtree(MODS / name, ignore_errors=True)
    prefix = f"app.modules.{name}"
    for key in [k for k in sys.modules if k == prefix or k.startswith(prefix + ".")]:
        del sys.modules[key]
    importlib.invalidate_caches()


def _make_temp_module(name: str, manifest_src: str) -> None:
    _drop_temp_module(name)
    pkg = MODS / name
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "manifest.py").write_text(manifest_src, encoding="utf-8")
    importlib.invalidate_caches()


class ClassificationTests(unittest.TestCase):
    """Cada clase de error produce su marcador y NO los de las otras."""

    def _resolve_error(self, name: str, manifest_src: str | None) -> str:
        if manifest_src is not None:
            self.addCleanup(_drop_temp_module, name)
            _make_temp_module(name, manifest_src)
        with self.assertRaises(ModuleLoadError) as ctx:
            resolve([name])
        return str(ctx.exception)

    def test_class_a_unknown_module(self):
        msg = self._resolve_error("_f1_inexistente_xyz", None)
        self.assertIn("desconocido", msg.lower())
        self.assertNotIn("dependencia no instalada", msg.lower())
        self.assertNotIn("Error interno", msg)

    def test_class_b_missing_external_dependency(self):
        msg = self._resolve_error("_f1_tmp_b", "import paquete_inexistente_xyz\nspec = None\n")
        self.assertIn("necesita una dependencia no instalada: paquete_inexistente_xyz", msg)
        self.assertIn("pip install", msg)
        self.assertNotIn("Error interno", msg)
        self.assertNotIn("desconocido", msg.lower())

    def test_class_c_internal_module_not_found(self):
        msg = self._resolve_error("_f1_tmp_c", "from .faltante_interno import x\nspec = None\n")
        self.assertIn("Error interno", msg)
        self.assertNotIn("dependencia no instalada", msg.lower())
        self.assertNotIn("desconocido", msg.lower())

    def test_class_d_import_error_is_internal(self):
        """ImportError REAL (no ModuleNotFoundError): nombre inexistente en un paquete instalado."""
        msg = self._resolve_error("_f1_tmp_d", "from httpx import NoExiste\nspec = None\n")
        self.assertIn("Error interno", msg)
        self.assertNotIn("dependencia no instalada", msg.lower())
        self.assertNotIn("desconocido", msg.lower())


class BuildProviderTests(unittest.TestCase):
    """build_provider: normalización, proveedor desconocido y KeyError interno."""

    def setUp(self):
        get_settings.cache_clear()
        self.addCleanup(get_settings.cache_clear)

    def _client(self) -> httpx.AsyncClient:
        client = httpx.AsyncClient()
        self.addCleanup(lambda: asyncio.run(client.aclose()))
        return client

    def _settings_for(self, provider_value: str):
        with patch.dict(os.environ, {"LLM_PROVIDER": provider_value}):
            get_settings.cache_clear()
            return get_settings()

    def _build(self, provider_value: str):
        settings = self._settings_for(provider_value)
        return build_provider(settings, self._client())

    def test_build_provider_openai_compatible_lowercase(self):
        self.assertIsInstance(self._build("openai_compatible"), OpenAICompatibleChatProvider)

    def test_build_provider_openai_compatible_uppercase(self):
        self.assertIsInstance(self._build("OPENAI_COMPATIBLE"), OpenAICompatibleChatProvider)

    def test_build_provider_openai_compatible_mixed_case(self):
        self.assertIsInstance(self._build("OpenAI_Compatible"), OpenAICompatibleChatProvider)

    def test_build_provider_openai_compatible_with_spaces(self):
        self.assertIsInstance(self._build("  openai_compatible  "), OpenAICompatibleChatProvider)

    def test_build_provider_unknown_raises_not_configured(self):
        with self.assertRaises(LLMNotConfiguredError):
            self._build("desconocido")

    def test_build_provider_none_factory_raises_not_configured(self):
        with patch.dict(adapters._PROVIDERS, {"openai_compatible": None}):
            with self.assertRaises(LLMNotConfiguredError):
                self._build("openai_compatible")

    def test_build_provider_does_not_swallow_internal_keyerror(self):
        """Un KeyError interno de la construcción NO debe reportarse como proveedor desconocido."""

        def boom(settings, client):
            raise KeyError("x")

        with patch.dict(adapters._PROVIDERS, {"openai_compatible": boom}):
            with self.assertRaises(KeyError) as ctx:
                self._build("openai_compatible")
        self.assertNotIsInstance(ctx.exception, LLMNotConfiguredError)


if __name__ == "__main__":
    unittest.main()