from __future__ import annotations
import functools
import hashlib
import json
import threading
from typing import Any, Callable, TypeVar
from cachetools import TTLCache

F = TypeVar("F", bound=Callable[..., Any])

# Global cache store (thread-safe)
_caches: dict[str, TTLCache] = {}
_lock = threading.Lock()


def get_cache(name: str, maxsize: int = 512, ttl: int = 300) -> TTLCache:
    """Return (or create) a named TTLCache."""
    with _lock:
        if name not in _caches:
            _caches[name] = TTLCache(maxsize=maxsize, ttl=ttl)
        return _caches[name]


def make_key(args: tuple[Any], kwargs: dict[str, Any]) -> str:
    """Generate a stable hash key from args/kwargs."""
    raw = json.dumps([args, kwargs], sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def cached(name: str, maxsize: int = 512, ttl: int = 300) -> Callable[[F], F]:
    """Decorator to cache function results in a named TTLCache."""
    def decorator(func: F) -> F:
        cache = get_cache(name, maxsize, ttl)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = make_key(args, kwargs)
            if key in cache:
                return cache[key]
            result = func(*args, **kwargs)
            cache[key] = result
            return result

        return wrapper  # type: ignore
    return decorator
