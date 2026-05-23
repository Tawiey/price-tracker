import os
import sys

# Add project root to path so 'src' and 'config' are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.app import app
except Exception as _err:
    # Surface import errors in the browser instead of getting a silent 404
    from flask import Flask as _Flask
    app = _Flask(__name__)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def _startup_error(path):
        return f"<pre>Startup error:\n{_err}</pre>", 500
