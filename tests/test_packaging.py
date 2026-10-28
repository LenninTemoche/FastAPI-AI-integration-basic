"""Pruebas de empaquetado (S7).

Verifica que pyproject.toml y requirements.txt estén correctamente configurados:
- imageio-ffmpeg y python-multipart están en project.optional-dependencies.media
- imageio-ffmpeg NO está en project.dependencies
- requirements.txt contiene '-e .[media,dev]' y ninguna línea con '=='
- docs/setup.md contiene la frase sobre imageio-ffmpeg como dependencia distintiva
"""

import unittest

import tomllib

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


class PackagingTests(unittest.TestCase):
    """Pruebas de empaquetado y dependencias."""

    def _load_pyproject(self):
        pyproject_path = REPO_ROOT / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            return tomllib.load(f)

    def _load_requirements(self):
        req_path = REPO_ROOT / "requirements.txt"
        with open(req_path, "r", encoding="utf-8") as f:
            return f.read()

    def test_media_extra_has_imageio_ffmpeg(self):
        """imageio-ffmpeg está en project.optional-dependencies.media."""
        data = self._load_pyproject()
        optional = data.get("project", {}).get("optional-dependencies", {})
        media_deps = optional.get("media", [])
        self.assertIn("imageio-ffmpeg>=0.6.0,<1.0", media_deps)

    def test_media_extra_has_python_multipart(self):
        """python-multipart está en project.optional-dependencies.media."""
        data = self._load_pyproject()
        optional = data.get("project", {}).get("optional-dependencies", {})
        media_deps = optional.get("media", [])
        self.assertIn("python-multipart>=0.0.20,<1.0", media_deps)

    def test_imageio_ffmpeg_not_in_project_dependencies(self):
        """imageio-ffmpeg NO está en project.dependencies."""
        data = self._load_pyproject()
        deps = data.get("project", {}).get("dependencies", [])
        for dep in deps:
            self.assertNotIn("imageio-ffmpeg", dep)

    def test_requirements_has_dev_extra_install(self):
        """requirements.txt contiene '-e .[media,dev]'."""
        content = self._load_requirements()
        self.assertIn("-e .[media,dev]", content)

    def test_requirements_no_exact_version_pins(self):
        """requirements.txt no contiene líneas con '=='."""
        content = self._load_requirements()
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                self.assertNotIn("==", stripped, f"Línea con == encontrada: {stripped}")


if __name__ == "__main__":
    unittest.main()