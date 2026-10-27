"""Pruebas de arquitectura (R1/F1).

Verifica reglas de imports mediante AST con descubrimiento real de capas:
- service, ports, models, repository NO importan fastapi, httpx, starlette
- Imports entre módulos solo si el módulo destino está en requires del manifest
- app.core no importa app.modules
- router, deps, errors, adapters pueden importar FastAPI/HTTPX

Limitación declarada: los imports dinámicos (importlib.import_module, __import__)
no se detectan; app/core/registry.py los usa a propósito.
"""

import ast
import importlib.util
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path


class ArchitectureTest(unittest.TestCase):
    """Pruebas de arquitectura basadas en AST."""

    # Módulos prohibidos para capas internas
    FORBIDDEN_MODULES = {"fastapi", "httpx", "starlette"}

    # Capas que NO deben importar módulos prohibidos
    INTERNAL_LAYERS = (
        "service",
        "ports",
        "models",
        "repository",
    )

    # Módulos permitidos para importar FastAPI/HTTPX
    ALLOWED_HTTP_MODULES = (
        "router",
        "deps",
        "errors",
        "adapters",
    )

    @classmethod
    def setUpClass(cls):
        cls.project_root = Path(__file__).parent.parent
        cls.app_root = cls.project_root / "app"

    # ------------------------------------------------------------------
    # Helpers del árbol real (usados por las pruebas sobre app/)
    # ------------------------------------------------------------------

    def get_module_requires(self, module_name: str) -> set[str]:
        """Extrae `requires` de manifest.py parseando AST (acepta tupla o lista)."""
        manifest_path = self.app_root / "modules" / module_name / "manifest.py"
        if not manifest_path.exists():
            return set()
        try:
            tree = ast.parse(manifest_path.read_text(encoding="utf-8"))
        except SyntaxError:
            return set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "ModuleSpec":
                    for kw in node.keywords:
                        if kw.arg == "requires" and isinstance(
                            kw.value, (ast.Tuple, ast.List)
                        ):
                            return {
                                elt.value
                                for elt in kw.value.elts
                                if isinstance(elt, ast.Constant)
                            }
        return set()

    def _relative_posix(self, app_root: Path, path: Path) -> str:
        """Devuelve la ruta POSIX relativa a app_root.parent."""
        return path.relative_to(app_root.parent).as_posix()

    def layer_files(
        self, app_root: Path, module: str, layer: str
    ) -> list[Path]:
        """Devuelve app_root/modules/<module>/<layer>.py si existe, más todos
        los .py bajo app_root/modules/<module>/<layer>/ si ese directorio existe."""
        result: list[Path] = []
        layer_file = app_root / "modules" / module / f"{layer}.py"
        if layer_file.exists():
            result.append(layer_file)
        layer_dir = app_root / "modules" / module / layer
        if layer_dir.is_dir():
            result.extend(layer_dir.rglob("*.py"))
        return sorted(result)

    def module_files(self, app_root: Path, module: str) -> list[Path]:
        """Todos los .py bajo app_root/modules/<module>/."""
        mod_dir = app_root / "modules" / module
        if not mod_dir.is_dir():
            return []
        return sorted(mod_dir.rglob("*.py"))

    def imported_names(self, path: Path, app_root: Path) -> list[tuple[int, str]]:
        """Devuelve tuplas (lineno, nombre_punteado) de importaciones.

        ast.Import: un nombre por cada alias.name.
        ast.ImportFrom: calcula base usando nivel relativo.
        """
        tree = ast.parse(path.read_text(encoding="utf-8"))
        results: list[tuple[int, str]] = []

        # Ruta relativa del archivo respecto a app_root.parent (p. ej. app/modules/media/deps.py)
        rel = path.relative_to(app_root.parent).as_posix()
        parts = rel.split("/")

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name != "*":
                        results.append((node.lineno, alias.name))
            elif isinstance(node, ast.ImportFrom):
                level = node.level or 0
                if level == 0:
                    base_parts = list(node.module.split(".")) if node.module else []
                else:
                    package_parts = parts[:-level] if level <= len(parts) else []
                    if node.module:
                        package_parts += node.module.split(".")
                    base_parts = package_parts
                base = ".".join(base_parts)
                if base:
                    results.append((node.lineno, base))
                for alias in node.names:
                    if alias.name != "*":
                        results.append((node.lineno, f"{base}.{alias.name}"))
        return results

    def requires_of(self, app_root: Path, module: str) -> set[str]:
        """Extrae requires de manifest.py (tupla o lista de constantes)."""
        manifest_path = app_root / "modules" / module / "manifest.py"
        if not manifest_path.exists():
            return set()
        try:
            tree = ast.parse(manifest_path.read_text(encoding="utf-8"))
        except SyntaxError:
            return set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "ModuleSpec":
                    for kw in node.keywords:
                        if kw.arg == "requires" and isinstance(
                            kw.value, (ast.Tuple, ast.List)
                        ):
                            return {
                                elt.value
                                for elt in kw.value.elts
                                if isinstance(elt, ast.Constant)
                            }
        return set()

    # ------------------------------------------------------------------
    # Reglas (cada una devuelve (violaciones, archivos_escaneados))
    # ------------------------------------------------------------------

    def _rule_forbidden_imports(
        self, app_root: Path, module: str
    ) -> tuple[list[str], list[str]]:
        """Capas service, ports, models, repository no importan fastapi/httpx/starlette."""
        violations: list[str] = []
        scanned: list[str] = []
        for layer in self.INTERNAL_LAYERS:
            for file_path in self.layer_files(app_root, module, layer):
                scanned.append(self._relative_posix(app_root, file_path))
                for lineno, name in self.imported_names(file_path, app_root):
                    top = name.split(".")[0]
                    if top in self.FORBIDDEN_MODULES:
                        violations.append(
                            f"{self._relative_posix(app_root, file_path)}:{lineno}: {name}"
                        )
        return violations, scanned

    def _rule_cross_module_imports(
        self, app_root: Path, module: str
    ) -> tuple[list[str], list[str]]:
        """Imports entre módulos solo si el destino está en requires."""
        violations: list[str] = []
        scanned: list[str] = []
        allowed = self.requires_of(app_root, module) | {module}
        for file_path in self.module_files(app_root, module):
            scanned.append(self._relative_posix(app_root, file_path))
            for lineno, name in self.imported_names(file_path, app_root):
                if name.startswith("app.modules."):
                    target = name.split(".")[2] if len(name.split(".")) > 2 else ""
                    if target and target != module and target not in allowed:
                        violations.append(
                            f"{self._relative_posix(app_root, file_path)}:{lineno}: {name}"
                        )
        return violations, scanned

    def _rule_core_no_imports_modules(
        self, app_root: Path
    ) -> tuple[list[str], list[str]]:
        """app.core no importa app.modules (nombre exacto o empieza por app.modules.)."""
        violations: list[str] = []
        scanned: list[str] = []
        core_dir = app_root / "core"
        if not core_dir.is_dir():
            return violations, scanned
        for file_path in sorted(core_dir.rglob("*.py")):
            scanned.append(self._relative_posix(app_root, file_path))
            for lineno, name in self.imported_names(file_path, app_root):
                    if name == "app.modules" or name.startswith("app.modules."):
                        violations.append(
                            f"{self._relative_posix(app_root, file_path)}:{lineno}: {name}"
                        )
        return violations, scanned

    # ------------------------------------------------------------------
    # Pruebas sobre el árbol real
    # ------------------------------------------------------------------

    def test_service_layer_no_forbidden_imports(self):
        violations, scanned = self._rule_forbidden_imports(
            self.app_root, "llm"
        )
        self.assertGreater(len(scanned), 0, "No se escaneó ningún archivo de service/llm")
        self.assertEqual(
            violations,
            [],
            f"service/llm importa módulos prohibidos: {violations}",
        )
        violations, scanned = self._rule_forbidden_imports(
            self.app_root, "media"
        )
        self.assertGreater(len(scanned), 0, "No se escaneó ningún archivo de service/media")
        self.assertEqual(
            violations,
            [],
            f"service/media importa módulos prohibidos: {violations}",
        )
        violations, scanned = self._rule_forbidden_imports(
            self.app_root, "products"
        )
        self.assertGreater(len(scanned), 0, "No se escaneó ningún archivo de service/products")
        self.assertEqual(
            violations,
            [],
            f"service/products importa módulos prohibidos: {violations}",
        )

    def test_ports_layer_no_forbidden_imports(self):
        violations, scanned = self._rule_forbidden_imports(
            self.app_root, "llm"
        )
        self.assertEqual(
            violations,
            [],
            f"ports/llm importa módulos prohibidos: {violations}",
        )
        violations, scanned = self._rule_forbidden_imports(
            self.app_root, "media"
        )
        self.assertEqual(
            violations,
            [],
            f"ports/media importa módulos prohibidos: {violations}",
        )
        violations, scanned = self._rule_forbidden_imports(
            self.app_root, "products"
        )
        self.assertEqual(
            violations,
            [],
            f"ports/products importa módulos prohibidos: {violations}",
        )

    def test_models_layer_no_forbidden_imports(self):
        violations, scanned = self._rule_forbidden_imports(
            self.app_root, "llm"
        )
        self.assertEqual(
            violations,
            [],
            f"models/llm importa módulos prohibidos: {violations}",
        )
        violations, scanned = self._rule_forbidden_imports(
            self.app_root, "media"
        )
        self.assertEqual(
            violations,
            [],
            f"models/media importa módulos prohibidos: {violations}",
        )
        violations, scanned = self._rule_forbidden_imports(
            self.app_root, "products"
        )
        self.assertEqual(
            violations,
            [],
            f"models/products importa módulos prohibidos: {violations}",
        )

    def test_repository_layer_no_forbidden_imports(self):
        violations, scanned = self._rule_forbidden_imports(
            self.app_root, "llm"
        )
        self.assertEqual(
            violations,
            [],
            f"repository/llm importa módulos prohibidos: {violations}",
        )
        violations, scanned = self._rule_forbidden_imports(
            self.app_root, "media"
        )
        self.assertEqual(
            violations,
            [],
            f"repository/media importa módulos prohibidos: {violations}",
        )
        violations, scanned = self._rule_forbidden_imports(
            self.app_root, "products"
        )
        self.assertEqual(
            violations,
            [],
            f"repository/products importa módulos prohibidos: {violations}",
        )

    def test_cross_module_imports_only_via_requires(self):
        for module in ["llm", "media", "products"]:
            violations, scanned = self._rule_cross_module_imports(
                self.app_root, module
            )
            self.assertGreater(
                len(scanned), 0, f"No se escaneó ningún archivo de {module}"
            )
            self.assertEqual(
                violations,
                [],
                f"Import cruzado no permitido en {module}: {violations}",
            )

    def test_core_no_imports_modules(self):
        violations, scanned = self._rule_core_no_imports_modules(self.app_root)
        self.assertGreater(len(scanned), 0, "No se escaneó ningún archivo de core/")
        self.assertEqual(
            violations,
            [],
            f"core importa app.modules: {violations}",
        )

    def test_media_requires_llm(self):
        requires = self.requires_of(self.app_root, "media")
        self.assertIn("llm", requires)

    def test_llm_no_requires(self):
        requires = self.requires_of(self.app_root, "llm")
        self.assertEqual(requires, set())

    def test_products_no_requires(self):
        requires = self.requires_of(self.app_root, "products")
        self.assertEqual(requires, set())

    # ------------------------------------------------------------------
    # Pruebas de sanidad sobre árbol falso
    # ------------------------------------------------------------------

    def _build_fake_tree(self, files: dict[str, str]) -> Path:
        """Crea un árbol falso en tempfile y devuelve app_root."""
        import os

        tmp = Path(tempfile.mkdtemp())
        app_root = tmp / "app"
        app_root.mkdir()
        modules_dir = app_root / "modules"
        modules_dir.mkdir()
        for rel_path, content in files.items():
            p = app_root / rel_path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        return app_root

    def test_sanity_service_imports_httpx(self):
        """foo/service.py con import httpx -> violación."""
        app_root = self._build_fake_tree(
            {"modules/foo/service.py": "import httpx\n"}
        )
        violations, scanned = self._rule_forbidden_imports(app_root, "foo")
        self.assertGreater(len(scanned), 0)
        self.assertTrue(
            any("httpx" in v for v in violations), f"Esperaba httpx en: {violations}"
        )

    def test_sanity_service_from_fastapi(self):
        """foo/service.py con from fastapi import APIRouter -> violación."""
        app_root = self._build_fake_tree(
            {"modules/foo/service.py": "from fastapi import APIRouter\n"}
        )
        violations, scanned = self._rule_forbidden_imports(app_root, "foo")
        self.assertGreater(len(scanned), 0)
        self.assertTrue(
            any("fastapi" in v for v in violations), f"Esperaba fastapi en: {violations}"
        )

    def test_sanity_deps_from_parent_module(self):
        """foo/deps.py con from ..bar import x -> violación."""
        app_root = self._build_fake_tree(
            {"modules/foo/deps.py": "from ..bar import x\n"}
        )
        violations, scanned = self._rule_cross_module_imports(app_root, "foo")
        self.assertGreater(len(scanned), 0)
        self.assertGreater(len(violations), 0, f"Esperaba violación en: {violations}")

    def test_sanity_deps_from_app_modules_bar(self):
        """foo/deps.py con from app.modules import bar -> violación."""
        app_root = self._build_fake_tree(
            {"modules/foo/deps.py": "from app.modules import bar\n"}
        )
        violations, scanned = self._rule_cross_module_imports(app_root, "foo")
        self.assertGreater(len(scanned), 0)
        self.assertGreater(len(violations), 0, f"Esperaba violación en: {violations}")

    def test_sanity_deps_from_parent_import(self):
        """foo/deps.py con from .. import bar -> violación."""
        app_root = self._build_fake_tree(
            {"modules/foo/deps.py": "from .. import bar\n"}
        )
        violations, scanned = self._rule_cross_module_imports(app_root, "foo")
        self.assertGreater(len(scanned), 0)
        self.assertGreater(len(violations), 0, f"Esperaba violación en: {violations}")

    def test_sanity_deps_import_app_modules_bar_service(self):
        """foo/deps.py con import app.modules.bar.service -> violación."""
        app_root = self._build_fake_tree(
            {"modules/foo/deps.py": "import app.modules.bar.service\n"}
        )
        violations, scanned = self._rule_cross_module_imports(app_root, "foo")
        self.assertGreater(len(scanned), 0)
        self.assertTrue(
            any("app.modules.bar.service" in v for v in violations),
            f"Esperaba app.modules.bar.service en: {violations}",
        )

    def test_sanity_adapters_from_parent_import(self):
        """foo/adapters/x.py con from ...bar import x -> violación."""
        app_root = self._build_fake_tree(
            {"modules/foo/adapters/x.py": "from ...bar import x\n"}
        )
        violations, scanned = self._rule_cross_module_imports(app_root, "foo")
        self.assertGreater(len(scanned), 0)
        self.assertGreater(len(violations), 0, f"Esperaba violación en: {violations}")

    def test_sanity_core_imports_app_modules_foo(self):
        """core/x.py con from app.modules import foo -> violación."""
        app_root = self._build_fake_tree(
            {"core/x.py": "from app.modules import foo\n"}
        )
        violations, scanned = self._rule_core_no_imports_modules(app_root)
        self.assertGreater(len(scanned), 0)
        self.assertTrue(
            any("app.modules" in v for v in violations),
            f"Esperaba app.modules en: {violations}",
        )

    def test_sanity_core_from_app_import_modules(self):
        """core/x.py con from app import modules -> violación."""
        app_root = self._build_fake_tree(
            {"core/x.py": "from app import modules\n"}
        )
        violations, scanned = self._rule_core_no_imports_modules(app_root)
        self.assertGreater(len(scanned), 0)
        self.assertTrue(
            any("app.modules" in v for v in violations),
            f"Esperaba app.modules en: {violations}",
        )

    def test_sanity_router_imports_fastapi_ok(self):
        """foo/router.py con from fastapi import APIRouter -> NO violación."""
        app_root = self._build_fake_tree(
            {"modules/foo/router.py": "from fastapi import APIRouter\n"}
        )
        violations, scanned = self._rule_forbidden_imports(app_root, "foo")
        # router no está en INTERNAL_LAYERS, así que no se escanea:
        self.assertEqual(len(scanned), 0)
        self.assertEqual(violations, [])

    def test_sanity_service_from_self_models_ok(self):
        """foo/service.py con from .models import X -> NO violación."""
        app_root = self._build_fake_tree(
            {"modules/foo/service.py": "from .models import X\n"}
        )
        violations, scanned = self._rule_forbidden_imports(app_root, "foo")
        self.assertGreater(len(scanned), 0)
        self.assertEqual(
            violations,
            [],
            f"service/foo no debería reportar .models: {violations}",
        )

    def test_sanity_service_from_core_config_ok(self):
        """foo/service.py con from app.core.config import Settings -> NO violación."""
        app_root = self._build_fake_tree(
            {
                "modules/foo/service.py": "from app.core.config import Settings\n",
                "core/config.py": "class Settings: pass\n",
            }
        )
        violations, scanned = self._rule_forbidden_imports(app_root, "foo")
        self.assertGreater(len(scanned), 0)
        self.assertEqual(
            violations,
            [],
            f"service/foo no debería reportar app.core.config: {violations}",
        )

    def test_sanity_deps_with_requires_ok(self):
        """foo/deps.py con from ..bar import x y requires=("bar",) -> NO violación."""
        app_root = self._build_fake_tree(
            {
                "modules/foo/deps.py": "from ..bar import x\n",
                "modules/foo/manifest.py": "from app.core.module import ModuleSpec\nspec = ModuleSpec(name='foo', description='x', requires=('bar',))\n",
            }
        )
        violations, scanned = self._rule_cross_module_imports(app_root, "foo")
        self.assertGreater(len(scanned), 0)
        self.assertEqual(
            violations,
            [],
            f"foo/deps.py con requires=bar no debería violar: {violations}",
        )

    def test_sanity_module_without_manifest(self):
        """foo sin manifest.py -> requires vacío."""
        app_root = self._build_fake_tree(
            {"modules/foo/service.py": "import httpx\n"}
        )
        requires = self.requires_of(app_root, "foo")
        self.assertEqual(requires, set())


if __name__ == "__main__":
    unittest.main()