import sys

# Test: media sin imageio-ffmpeg
sys.modules["imageio_ffmpeg"] = None

from app.main import create_app

try:
    app = create_app(enabled=["media"])
    print("ERROR: Debería haber fallado")
except Exception as e:
    print(f"OK: {type(e).__name__}: {e}")