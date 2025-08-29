from __future__ import annotations
from typing import Dict, Any
from ..clients.tmdb import TMDbClient

def get_movie_details_service(movie_id: int) -> Dict[str, Any]:
    client = TMDbClient()
    payload = client.movie_details(movie_id)
    movie, cast = client.normalize_details(payload)

    # Only include top-billed (e.g., first 8)
    top_cast = [
        {
            "id": c.id,
            "name": c.name,
            "character": c.character,
            "profile_path": c.profile_path,
        }
        for c in cast[:8]
        if c.name
    ]

    return {
        "movie": movie.__dict__,
        "cast": top_cast,
    }
