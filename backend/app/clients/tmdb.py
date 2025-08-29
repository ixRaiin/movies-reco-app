from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, List
import requests
from ..core.cache import cached

DEFAULT_TIMEOUT = 8  # seconds

# Read base URL at call-time (after load_dotenv has run)
def _tmdb_base() -> str:
    return os.getenv("TMDB_API_BASE", "https://api.themoviedb.org/3")

# One shared session
_session = requests.Session()
_session.headers.update({"Accept": "application/json"})


@dataclass
class TMDbCast:
    id: int
    name: str
    character: Optional[str] = None
    profile_path: Optional[str] = None


@dataclass
class TMDbMovie:
    id: int
    title: str
    year: Optional[int] = None
    overview: Optional[str] = None
    poster_path: Optional[str] = None


class TMDbClient:
    def __init__(self, api_key: Optional[str] = None):
        # Read API key at init-time, not import-time
        self.api_key = api_key or os.getenv("TMDB_API_KEY")
        if not self.api_key:
            raise RuntimeError("TMDB_API_KEY is required")

    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{_tmdb_base()}{path}"
        query = {"api_key": self.api_key, **params}
        r = _session.get(url, params=query, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return r.json()

    def search_movies(self, q: str, page: int = 1) -> Dict[str, Any]:
        return self._get(
            "/search/movie",
            {"query": q, "page": page, "include_adult": False},
        )
    
    def trending_movies(self, window: str = "day", page: int = 1) -> Dict[str, Any]:
        return self._get(f"/trending/movie/{window}", {"page": page})

    def popular_movies(self, page: int = 1) -> Dict[str, Any]:
        return self._get("/movie/popular", {"page": page})
    
    def movie_recommendations(self, movie_id: int, page: int = 1) -> Dict[str, Any]:
        return self._get(f"/movie/{movie_id}/recommendations", {"page": page})

    def movie_similar(self, movie_id: int, page: int = 1) -> Dict[str, Any]:
        return self._get(f"/movie/{movie_id}/similar", {"page": page})
    
    def movie_watch_providers(self, movie_id: int) -> Dict[str, Any]:
        return self._get(f"/movie/{movie_id}/watch/providers", {})
    
    def discover_movies(self, *, with_genres: str, page: int = 1, region: str | None = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "with_genres": with_genres,
            "sort_by": "popularity.desc",
            "include_adult": False,
            "page": page,
        }
        if region:
            params["region"] = region
        return self._get("/discover/movie", params)

    @staticmethod
    def normalize_movie(raw: Dict[str, Any]) -> TMDbMovie:
        # TMDb uses 'release_date' like '1999-10-15'
        year: Optional[int] = None
        rd = raw.get("release_date")
        if rd and len(rd) >= 4:
            try:
                year = int(rd[:4])
            except ValueError:
                year = None
        return TMDbMovie(
            id=raw["id"],
            title=raw.get("title") or raw.get("name") or "Untitled",
            year=year,
            overview=raw.get("overview"),
            poster_path=raw.get("poster_path"),
        )

    def movie_details(self, movie_id: int) -> Dict[str, Any]:
        # Append credits to avoid multiple roundtrips
        return self._get(f"/movie/{movie_id}", {"append_to_response": "credits"})

    @staticmethod
    def normalize_details(raw: Dict[str, Any]) -> Tuple[TMDbMovie, List[TMDbCast]]:
        movie = TMDbClient.normalize_movie(raw)
        cast_raw = (raw.get("credits") or {}).get("cast", []) or []
        cast: List[TMDbCast] = []
        for c in cast_raw:
            cast.append(
                TMDbCast(
                    id=c["id"],
                    name=c.get("name") or "",
                    character=c.get("character"),
                    profile_path=c.get("profile_path"),
                )
            )
        return movie, cast

    @cached("tmdb_search", ttl=600)   # cache for 10 minutes
    def search_movies(self, q: str, page: int = 1) -> Dict[str, Any]:
        return self._get(
            "/search/movie",
            {"query": q, "page": page, "include_adult": False},
        )

    @cached("tmdb_details", ttl=3600)   # cache for 1 hour
    def movie_details(self, movie_id: int) -> Dict[str, Any]:
        return self._get(f"/movie/{movie_id}", {"append_to_response": "credits"})

    @cached("tmdb_recommend", ttl=1800)   # cache for 30 minutes
    def movie_recommendations(self, movie_id: int, page: int = 1) -> Dict[str, Any]:
        return self._get(f"/movie/{movie_id}/recommendations", {"page": page})

    @cached("tmdb_similar", ttl=1800)   # cache for 30 minutes
    def movie_similar(self, movie_id: int, page: int = 1) -> Dict[str, Any]:
        return self._get(f"/movie/{movie_id}/similar", {"page": page})

    @cached("tmdb_providers", ttl=21600)   # cache for 6 hours
    def movie_watch_providers(self, movie_id: int) -> Dict[str, Any]:
        return self._get(f"/movie/{movie_id}/watch/providers", {})

    @cached("tmdb_discover", ttl=900)   # cache for 15 minutes
    def discover_movies(self, *, with_genres: str, page: int = 1, region: str | None = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "with_genres": with_genres,
            "sort_by": "popularity.desc",
            "include_adult": False,
            "page": page,
        }
        if region:
            params["region"] = region
        return self._get("/discover/movie", params)
