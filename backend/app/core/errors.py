from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple
import uuid
import logging

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

log = logging.getLogger(__name__)

# -------- Envelope builder
def _trace_id() -> str:
    # Respect caller-provided correlation id if present.
    return request.headers.get("X-Trace-Id") or str(uuid.uuid4())

def make_error(
    *,
    code: str,
    message: str,
    hint: Optional[str] = None,
    dependency: Optional[str] = None,
    status: int = 400,
    exc: BaseException | None = None,
):
    """
    Build a standardized error response and log it once.
    """
    tid = _trace_id()
    payload = {
        "code": code,
        "message": message,
        "hint": hint,
        "dependency": dependency,
        "trace_id": tid,
    }

    # Structured log; include exception info when present
    if exc is not None:
        log.exception("error code=%s status=%s trace_id=%s dependency=%s hint=%s",
                      code, status, tid, dependency, hint)
    else:
        log.warning("error code=%s status=%s trace_id=%s dependency=%s hint=%s",
                    code, status, tid, dependency, hint)

    return jsonify(payload), status

# Backward-compatible helper (kept for convenience)
def err(code, message, hint=None, dependency=None, status=400):
    return make_error(code=code, message=message, hint=hint, dependency=dependency, status=status)

# -------- First-class API error
@dataclass
class ApiError(Exception):
    code: str
    message: str
    hint: Optional[str] = None
    dependency: Optional[str] = None
    status: int = 400

    def to_response(self) -> Tuple[object, int]:
        return make_error(
            code=self.code,
            message=self.message,
            hint=self.hint,
            dependency=self.dependency,
            status=self.status,
            exc=self,
        )

# -------- Installer

def install_error_handlers(app: Flask) -> None:
    """
    Install a single, consistent error handling stack.
    Call this once in app factory after blueprints are registered.
    """

    @app.errorhandler(ApiError)
    def _handle_api_error(e: ApiError):
        return e.to_response()

    @app.errorhandler(HTTPException)
    def _handle_http_exception(e: HTTPException):
        code_map = {
            400: "bad_request",
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            405: "method_not_allowed",
            408: "request_timeout",
            413: "payload_too_large",
            415: "unsupported_media_type",
            429: "rate_limited",
            500: "internal_error",
            502: "bad_gateway",
            503: "service_unavailable",
            504: "gateway_timeout",
        }
        code = code_map.get(e.code or 500, "internal_error")
        is_5xx = (e.code or 500) >= 500
        message = "Upstream dependency failed" if e.code == 502 else (
            "Unexpected error" if is_5xx else (e.description or e.name)
        )
        dependency = "tmdb" if e.code == 502 else None
        return make_error(code=code, message=message, dependency=dependency, status=e.code or 500, exc=e)

    @app.errorhandler(Exception)
    def _handle_uncaught(e: Exception):
        return make_error(
            code="internal_error",
            message="Unexpected error",
            hint="Try again later",
            status=500,
            exc=e,
        )

# -------- Convenience shortcuts (optional but nice)
def bad_request(message: str, *, hint: str | None = None):
    raise ApiError(code="bad_request", message=message, hint=hint, status=400)

def not_found(message: str = "Resource not found", *, hint: str | None = "Check the URL"):
    raise ApiError(code="not_found", message=message, hint=hint, status=404)

def upstream_failed(message: str = "TMDb error", *, dependency: str = "tmdb", status: int = 502):
    raise ApiError(code="bad_gateway", message=message, dependency=dependency, status=status)
