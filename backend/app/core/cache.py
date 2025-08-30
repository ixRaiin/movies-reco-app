from __future__ import annotations
import time
import json
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple
from flask import request, jsonify, Response
from werkzeug.wrappers.response import Response as WResp

# ---------------------------
# In-process caches
# ---------------------------
# For route responses (we store ONLY dict payloads)
_ROUTE_CACHE: Dict[str, Dict[str, Any]] = {}
# For pure function results (e.g., TMDb client helpers)
_FUNC_CACHE: Dict[str, Dict[str, Any]] = {}

def _now() -> float:
    return time.time()

def _extract_payload(obj: Any) -> Optional[dict]:
    """
    Try to extract a JSON dict payload from various return shapes.
    Returns None if not a dict JSON payload.
    """
    # Flask / Werkzeug Response
    if isinstance(obj, (Response, WResp)):
        try:
            js = obj.get_json(silent=True)  # type: ignore[attr-defined]
            return js if isinstance(js, dict) else None
        except Exception:
            return None
    # Already a dict
    if isinstance(obj, dict):
        return obj
    # Something with get_json (rare)
    get_json = getattr(obj, "get_json", None)
    if callable(get_json):
        try:
            js = get_json(silent=True)  # type: ignore[call-arg]
            return js if isinstance(js, dict) else None
        except Exception:
            return None
    return None

def _normalize_for_key(x: Any) -> Any:
    """
    Convert args/kwargs to a stable, hashable structure for cache keying.
    This is conservative and JSON-serializes unknowns.
    """
    if x is None or isinstance(x, (str, int, float, bool)):
        return x
    if isinstance(x, (tuple, list)):
        return tuple(_normalize_for_key(i) for i in x)
    if isinstance(x, dict):
        return tuple(sorted((str(k), _normalize_for_key(v)) for k, v in x.items()))
    try:
        # Last resort: JSON dump to a string
        return json.dumps(x, sort_keys=True, default=str)
    except Exception:
        return str(x)

# ---------------------------
# Route-level TTL cache
# ---------------------------
def ttl_cache(ttl_seconds: int, vary: List[str] | None = None):
    """
    Decorator that caches JSON responses for ttl_seconds.
    IMPORTANT: We only cache the *payload dict*, never the Flask Response.
    We also avoid caching error statuses (>= 400).
    """
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Build cache key from function + selected args/query
            parts = [fn.__name__]
            if vary:
                va = request.view_args or {}
                for v in vary:
                    parts.append(str(
                        va.get(v) if v in va else request.args.get(v) or kwargs.get(v) or ""
                    ))
            key = "|".join(parts)

            # Try cache hit
            ent = _ROUTE_CACHE.get(key)
            if ent and (_now() - ent["ts"] < ttl_seconds):
                payload = ent["payload"]
                resp = jsonify(payload)  # payload is dict
                resp.headers["X-Cache"] = "hit"
                return resp

            # Miss: call the function
            rv = fn(*args, **kwargs)

            # Normalize common Flask return shapes
            body: Any = rv
            status: Optional[int] = None
            headers: Optional[dict] = None
            if isinstance(rv, tuple):
                if len(rv) == 2:
                    body, status = rv
                elif len(rv) == 3:
                    body, status, headers = rv

            # If it's a Response, don’t cache error statuses
            if isinstance(body, (Response, WResp)):
                code = getattr(body, "status_code", None)
                if isinstance(code, int) and code >= 400:
                    try:
                        body.headers["X-Cache"] = "miss"
                    except Exception:
                        pass
                    return body if status is None else (body, status) if headers is None else (body, status, headers)

                payload = _extract_payload(body)
                if isinstance(payload, dict):
                    _ROUTE_CACHE[key] = {"ts": _now(), "payload": payload}
                    out = jsonify(payload)
                    out.headers["X-Cache"] = "miss"
                    return out
                # passthrough if not JSON
                try:
                    body.headers["X-Cache"] = "miss"
                except Exception:
                    pass
                return body if status is None else (body, status) if headers is None else (body, status, headers)

            # Non-Response shapes: try extract dict & cache
            payload = _extract_payload(body)
            if isinstance(payload, dict):
                if status is None or status < 400:
                    _ROUTE_CACHE[key] = {"ts": _now(), "payload": payload}
                out = jsonify(payload)
                out.headers["X-Cache"] = "miss"
                return out if status is None else (out, status) if headers is None else (out, status, headers)

            # Fallback: jsonify dicts, passthrough others; don’t cache
            if isinstance(body, dict):
                out = jsonify(body)
                out.headers["X-Cache"] = "miss"
                return out if status is None else (out, status) if headers is None else (out, status, headers)

            return body if status is None else (body, status) if headers is None else (body, status, headers)
        return wrapper
    return deco

# ---------------------------
# Function-level TTL cache (for clients/helpers)
# ---------------------------
def cached(name: str, ttl: int):
    """
    Cache decorator for *pure* functions (e.g., TMDbClient helpers).
    Key includes: name + function name + normalized args/kwargs.
    Stores the returned value verbatim (must be JSON-serializable or simple types).
    """
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key_parts = [f"func:{name}", fn.__name__, repr(_normalize_for_key(args)), repr(_normalize_for_key(kwargs))]
            key = "|".join(key_parts)

            ent = _FUNC_CACHE.get(key)
            if ent and (_now() - ent["ts"] < ttl):
                return ent["value"]

            value = fn(*args, **kwargs)

            # Only cache values that are JSON-serializable or simple types.
            try:
                json.dumps(value, default=str)
                _FUNC_CACHE[key] = {"ts": _now(), "value": value}
            except Exception:
                # Skip caching un-serializable values to avoid surprises.
                pass

            return value
        return wrapper
    return deco

# ---------------------------
# Dev helpers
# ---------------------------
def _cache_clear():
    """Clear all in-memory caches (useful for tests or after refactors)."""
    _ROUTE_CACHE.clear()
    _FUNC_CACHE.clear()
