from __future__ import annotations
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from .core.config import load_config
from .core.errors import install_error_handlers, err
from .api.routes import bp as api_bp
from .core.ratelimit import is_allowed
from .clients.tmdb import refresh_tmdb_auth_from_env

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "60"))
RATE_WINDOW = int(os.getenv("RATE_WINDOW", "60"))  # seconds

def create_app() -> Flask:
    app = Flask(__name__)
    load_config(app)
    refresh_tmdb_auth_from_env() 

    # CORS only for API routes
    CORS(app, resources={r"/api/*": {"origins": FRONTEND_ORIGIN}})

    # Consistent errors everywhere
    install_error_handlers(app)

    # Mount API at /api
    app.register_blueprint(api_bp, url_prefix="/api")

    # Simple health (optional, helpful for probes)
    @app.get("/health")
    def _health():
        return jsonify({"status": "ok"})

    # Rate limiting (uniform envelope on 429)
    @app.before_request
    def _check_rate_limit():
        # Skip rate limit for health checks if you want
        if request.path == "/health":
            return None
        ip = request.remote_addr or "unknown"
        ok, remaining = is_allowed(ip)
        if not ok:
            return err(
                "rate_limited",
                "Too many requests, slow down.",
                hint=f"Limit is {RATE_LIMIT} requests per {RATE_WINDOW} seconds",
                status=429,
            )
        # Stash remaining for response headers
        request.remaining = remaining
        return None

    @app.after_request
    def _rate_limit_headers(resp):
        # Best-effort: only attach headers for API paths
        if request.path.startswith("/api"):
            resp.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
            resp.headers["X-RateLimit-Remaining"] = str(getattr(request, "remaining", RATE_LIMIT))
        return resp

    return app
