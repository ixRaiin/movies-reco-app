from __future__ import annotations
from typing import Dict, Any, List
from ..clients.tmdb import TMDbClient

# Simple mood -> TMDb genre IDs (expand later / LLM-powered)
MOOD_TO_GENRES: Dict[str, List[int]] = {
    "happy": [35, 10751, 16],            # Comedy, Family, Animation
    "romantic": [10749, 35],             # Romance, Comedy
    "thrilling": [53, 28],               # Thriller, Action
    "adventurous": [12, 28, 14],         # Adventure, Action, Fantasy
    "scary": [27, 53],                   # Horror, Thriller
    "thoughtful": [18, 99],              # Drama, Documentary
    "mystery": [9648, 80],               # Mystery, Crime
    "sci-fi": [878, 12, 14],             # Sci-Fi, Adventure, Fantasy
    "feel-good": [35, 10751],            # Comedy, Family
    "epic": [12, 14, 28],                # Adventure, Fantasy, Action
}

def _genres_for_mood(mood: str) -> List[int]:
    key = (mood or "").strip().lower()
    return MOOD_TO_GENRES.get(key, [18])  # default Drama if unknown

def mood_recommendations_service(mood: str, page: int = 1, require_poster: bool = True, region: str | None = None) -> Dict[str, Any]:
    client = TMDbClient()
    genre_ids = _genres_for_mood(mood)
    with_genres = ",".join(str(g) for g in genre_ids)
    payload = client.discover_movies(with_genres=with_genres, page=page, region=region)

    normalized = [client.normalize_movie(m).__dict__ for m in payload.get("results", [])]
    if require_poster:
        normalized = [m for m in normalized if m.get("poster_path")]

    return {
        "mood": mood,
        "genres": genre_ids,
        "page": payload.get("page", page),
        "total_pages": payload.get("total_pages", 0),
        "total_results": len(normalized),
        "results": normalized,
    }
