from __future__ import annotations
from typing import Dict, Any, List
from ..clients.tmdb import TMDbClient

def get_trending_service(window: str = "day", limit: int = 10, require_poster: bool = True) -> Dict[str, Any]:
    client = TMDbClient()
    payload = client.trending_movies(window=window, page=1)
    results: List[dict] = payload.get("results", []) or []
    normalized = [client.normalize_movie(m).__dict__ for m in results]
    if require_poster:
        normalized = [m for m in normalized if m.get("poster_path")]
    return {
        "window": window,
        "results": normalized[:limit],
        "total": len(normalized[:limit]),
    }

def get_popular_service(limit: int = 20, require_poster: bool = True) -> Dict[str, Any]:
    client = TMDbClient()
    payload = client.popular_movies(page=1)
    results: List[dict] = payload.get("results", []) or []
    normalized = [client.normalize_movie(m).__dict__ for m in results]
    if require_poster:
        normalized = [m for m in normalized if m.get("poster_path")]
    return {
        "results": normalized[:limit],
        "total": len(normalized[:limit]),
    }
