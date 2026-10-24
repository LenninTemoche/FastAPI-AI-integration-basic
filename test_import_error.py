import sys

# Test: ImportError genérico (no ModuleNotFoundError) - no debe reportarse como "desconocido"
sys.modules["httpx"] = None
# Forzar que el import falle con un error distinto a ModuleNotFoundError
class FakeHTTPX:
    class NoExiste:
        pass

sys.modules["httpx"] = FakeHTTPX

from app.main import create_app

try:
    app = create_app(enabled=["llm"])
    print("ERROR: Debería haber fallado")
except Exception as e:
    print(f"OK: {type(e).__name__}: {e}")