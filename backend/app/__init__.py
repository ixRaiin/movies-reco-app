from flask import Flask, request, jsonify
from flask_cors import CORS
from .core.config import load_config
from .core.errors import install_error_handlers
from .api.routes import register_routes
from .core.ratelimit import is_allowed

def create_app() -> Flask:
    app = Flask(__name__)
    load_config(app)
    CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})
    install_error_handlers(app)
    register_routes(app)

    @app.before_request
    def _check_rate_limit():
        ip = request.remote_addr or "unknown"
        ok, remaining = is_allowed(ip)
        if not ok:
            return jsonify({
                "code": "rate_limited",
                "message": "Too many requests, slow down.",
                "hint": f"Limit is {60} requests per {60} seconds",
            }), 429
        request.remaining = remaining

    return app
