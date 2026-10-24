import sys

# Test: media sin extra - bloquear import de python-multipart e imageio_ffmpeg
sys.modules["multipart"] = None
sys.modules["python_multipart"] = None
sys.modules["imageio_ffmpeg"] = None

from app.main import create_app

try:
    app = create_app(enabled=["media"])
    print("ERROR: Debería haber fallado")
except Exception as e:
    print(f"OK: {type(e).__name__}: {e}")