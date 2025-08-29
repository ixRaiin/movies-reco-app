from __future__ import annotations
from dataclasses import dataclass, asdict
from flask import Flask, jsonify

@dataclass
class ApiError(Exception):
    code: str
    message: str
    hint: str | None = None
    http_status: int = 400

    def to_dict(self):
        d = asdict(self)
        d.pop("http_status", None)
        return d

def install_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def _handle_api_error(err: ApiError):
        return jsonify(err.to_dict()), err.http_status

    @app.errorhandler(404)
    def _404(_):
        return jsonify({"code": "not_found", "message": "Not found"}), 404

    @app.errorhandler(500)
    def _500(err):
        app.logger.exception("Unhandled error: %s", err)
        return jsonify({"code": "internal_error", "message": "Something went wrong"}), 500
