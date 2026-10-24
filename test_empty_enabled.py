import os
os.environ["ENABLED_MODULES"] = ""

from app.main import create_app

try:
    app = create_app(enabled=[])
    print(f"OK: App creada con enabled=[] - modules: {list(app.state.modules.keys())}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")