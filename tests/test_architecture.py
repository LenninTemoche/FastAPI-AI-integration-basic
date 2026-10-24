"""Pruebas de arquitectura (R1/F1).

Verifica reglas de imports mediante AST:
- service, ports, models, repository NO importan fastapi, httpx, starlette
- Imports entre módulos solo si el módulo destino está en requires del manifest
- app.core no importa app.modules
- router, deps, errors, adapters pueden importar FastAPI/HTTPX
"""

import ast
import sys
import tempfile
import unittest
from pathlib import Path


class ArchitectureTest(unittest.TestCase):
    """Pruebas de arquitectura basadas en AST."""

    # Módulos prohibidos para capas internas
    FORBIDDEN_MODULES = {"fastapi", "httpx", "starlette"}

    # Capas que NO deben importar módulos prohibidos
    INTERNAL_LAYERS = {
        "service",
        "ports",
        "models",
        "repository",
    }

    # Módulos permitidos para importar FastAPI/HTTPX
    ALLOWED_HTTP_MODULES = {
        "router",
        "deps",
        "errors",
        "adapters",
    }

    @classmethod
    def setUpClass(cls):
        cls.project_root = Path(__file__).parent.parent
        cls.app_root = cls.project_root / "app"

    def get_module_requires(self, module_name: str) -> set[str]:
        """Obtiene los requires del manifest de un módulo parseando AST."""
        manifest_path = self.app_root / "modules" / module_name / "manifest.py"
        if not manifest_path.exists():
            return set()
        try:
            tree = ast.parse(manifest_path.read_text(encoding="utf-8"))
        except SyntaxError:
            return set()

        # Buscar la instanciación de ModuleSpec y extraer requires
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "ModuleSpec":
                    for kw in node.keywords:
                        if kw.arg == "requires" and isinstance(kw.value, ast.Tuple):
                            return {elt.value for elt in kw.value.elts if isinstance(elt, ast.Constant)}
        return set()

    def get_python_files(self, layer: str, module: str = None) -> list[Path]:
        """Obtiene archivos .py de una capa y módulo opcional."""
        if module:
            base = self.app_root / "modules" / module / layer
        else:
            base = self.app_root / "core" / layer
        if not base.exists():
            return []
        return list(base.rglob("*.py"))

    def check_forbidden_imports(self, file_path: Path, allowed_modules: set = None) -> list[str]:
        """Detecta imports prohibidos en un archivo."""
        allowed = allowed_modules or set()
        violations = []
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
        except SyntaxError:
            return violations

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in self.FORBIDDEN_MODULES:
                        if alias.name.split(".")[0] not in allowed:
                            violations.append(f"{file_path}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] in self.FORBIDDEN_MODULES:
                    if node.module.split(".")[0] not in allowed:
                        violations.append(f"{file_path}: from {node.module} import ...")
        return violations

    def check_cross_module_imports(self, file_path: Path, source_module: str) -> list[str]:
        """Detecta imports entre módulos no permitidos."""
        violations = []
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
        except SyntaxError:
            return violations

        allowed_requires = self.get_module_requires(source_module)

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("app.modules."):
                    parts = node.module.split(".")
                    if len(parts) >= 3:
                        target_module = parts[2]
                        if target_module != source_module and target_module not in allowed_requires:
                            violations.append(
                                f"{file_path}: from app.modules.{target_module} ... (no en requires)"
                            )
        return violations

    def test_service_layer_no_forbidden_imports(self):
        """service NO importa fastapi, httpx, starlette."""
        for module in ["llm", "media", "products"]:
            for file_path in self.get_python_files("service", module):
                violations = self.check_forbidden_imports(file_path)
                self.assertEqual(
                    violations, [],
                    f"service/{module} importa módulos prohibidos: {violations}"
                )

    def test_ports_layer_no_forbidden_imports(self):
        """ports NO importa fastapi, httpx, starlette."""
        for module in ["llm", "media", "products"]:
            for file_path in self.get_python_files("ports", module):
                violations = self.check_forbidden_imports(file_path)
                self.assertEqual(
                    violations, [],
                    f"ports/{module} importa módulos prohibidos: {violations}"
                )

    def test_models_layer_no_forbidden_imports(self):
        """models NO importa fastapi, httpx, starlette."""
        for module in ["llm", "media", "products"]:
            for file_path in self.get_python_files("models", module):
                violations = self.check_forbidden_imports(file_path)
                self.assertEqual(
                    violations, [],
                    f"models/{module} importa módulos prohibidos: {violations}"
                )

    def test_repository_layer_no_forbidden_imports(self):
        """repository NO importa fastapi, httpx, starlette."""
        for module in ["llm", "media", "products"]:
            for file_path in self.get_python_files("repository", module):
                violations = self.check_forbidden_imports(file_path)
                self.assertEqual(
                    violations, [],
                    f"repository/{module} importa módulos prohibidos: {violations}"
                )

    def test_cross_module_imports_only_via_requires(self):
        """Imports entre módulos solo si están en requires del manifest."""
        for module in ["llm", "media", "products"]:
            for layer in ["service", "ports", "models", "repository", "deps", "errors", "adapters"]:
                for file_path in self.get_python_files(layer, module):
                    violations = self.check_cross_module_imports(file_path, module)
                    self.assertEqual(
                        violations, [],
                        f"Import cruzado no permitido: {violations}"
                    )

    def test_core_no_imports_modules(self):
        """app.core no importa app.modules."""
        for file_path in (self.app_root / "core").rglob("*.py"):
            violations = []
            try:
                tree = ast.parse(file_path.read_text(encoding="utf-8"))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith("app.modules."):
                        violations.append(f"{file_path}: from {node.module} import ...")
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("app.modules."):
                            violations.append(f"{file_path}: import {alias.name}")

            self.assertEqual(
                violations, [],
                f"core importa módulos: {violations}"
            )

    def test_allowed_http_imports(self):
        """router, deps, errors, adapters pueden importar FastAPI/HTTPX."""
        for module in ["llm", "media", "products"]:
            for layer in self.ALLOWED_HTTP_MODULES:
                for file_path in self.get_python_files(layer, module):
                    # Solo verificamos que NO fallen por imports HTTP
                    # (la regla es que SÍ pueden importar, no que DEBAN)
                    pass  # Solo documentamos la regla

    def test_sanity_violation_detected(self):
        """Prueba de sanidad: un archivo violador en temp debe ser detectado."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Archivo que viola la regla: service importa fastapi
            violator = tmp_path / "violator.py"
            violator.write_text("import fastapi\n")
            violations = self.check_forbidden_imports(violator)
            self.assertIn("fastapi", " ".join(violations))

    def test_media_requires_llm(self):
        """media declara requires=('llm',) en su manifest."""
        requires = self.get_module_requires("media")
        self.assertIn("llm", requires)

    def test_llm_no_requires(self):
        """llm no tiene requires en su manifest."""
        requires = self.get_module_requires("llm")
        self.assertEqual(requires, set())

    def test_products_no_requires(self):
        """products no tiene requires en su manifest."""
        requires = self.get_module_requires("products")
        self.assertEqual(requires, set())


if __name__ == "__main__":
    unittest.main()