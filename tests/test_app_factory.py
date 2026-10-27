"""Pruebas para la fábrica de la aplicación (S3)."""

import unittest

from app.main import create_app as create_app_main
from app.factory import create_app as create_app_factory


class AppFactoryTests(unittest.TestCase):
    """Pruebas para la fábrica de la aplicación."""

    def test_single_create_app(self) -> None:
        """La función create_app debe ser la misma en main y factory."""
        from app.main import create_app as a
        from app.factory import create_app as b
        self.assertIs(a, b)

    def test_no_legacy_state_key(self) -> None:
        """Ningún archivo .py bajo app/ contiene el texto llm_http_client."""
        import os
        for root, dirs, files in os.walk("app"):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        self.assertNotIn("llm_http_client", content,
                            f"Encontrado llm_http_client en {path}")


if __name__ == "__main__":
    unittest.main()