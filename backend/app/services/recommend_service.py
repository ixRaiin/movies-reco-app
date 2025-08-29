from __future__ import annotations
from typing import Dict, Any, List
from ..clients.tmdb import TMDbClient

def get_recommendations_service(movie_id: int, page: int = 1, require_poster: bool = True) -> Dict[str, Any]:
    client = TMDbClient()

    payload = client.movie_recommendations(movie_id, page)
    source = "recommendations"
    results_raw: List[dict] = payload.get("results", []) or []

    if not results_raw:
        payload = client.movie_similar(movie_id, page)
        results_raw = payload.get("results", []) or []
        source = "similar"

    normalized = [client.normalize_movie(m).__dict__ for m in results_raw]
    if require_poster:
        normalized = [m for m in normalized if m.get("poster_path")]
    return {
        "source": source,
        "page": payload.get("page", page),
        "total_pages": payload.get("total_pages", 0),
        "total_results": len(normalized),
        "results": normalized,
    }
