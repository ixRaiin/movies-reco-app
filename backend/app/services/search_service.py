from __future__ import annotations
from typing import Dict, Any
from ..clients.tmdb import TMDbClient

def search_movies_service(q: str, page: int = 1) -> Dict[str, Any]:
    client = TMDbClient()
    payload = client.search_movies(q, page)
    results = [client.normalize_movie(m).__dict__ for m in payload.get("results", [])]
    return {
        "page": payload.get("page", page),
        "total_pages": payload.get("total_pages", 0),
        "total_results": payload.get("total_results", 0),
        "results": results,
    }
