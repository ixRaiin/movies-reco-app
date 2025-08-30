from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, List
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from ..core.cache import cached

DEFAULT_TIMEOUT = int(os.getenv("TMDB_TIMEOUT", "8"))  # seconds
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en-US")

def _tmdb_base() -> str:
    # Read at call-time (after dotenv), allow override for tests
    return os.getenv("TMDB_API_BASE", "https://api.themoviedb.org/3")

def tmdb_url(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return f"{_tmdb_base()}{path}"

def build_tmdb_session() -> Session:
    s = Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
        raise_on_status=False,
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    bearer = os.getenv("TMDB_BEARER")
    if bearer:
        s.headers.update({"Authorization": f"Bearer {bearer}"})
    s.headers.update({"Accept": "application/json"})
    return s

# Single shared session w/ retries & (optional) Bearer
session: Session = build_tmdb_session()

def refresh_tmdb_auth_from_env() -> None:
    bearer = os.getenv("TMDB_BEARER")
    if bearer:
        session.headers.update({"Authorization": f"Bearer {bearer}"})

# --- Models -----------------------------------------------------------------
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

# --- Client -----------------------------------------------------------------

class TMDbClient:
    """
    TMDb client with retrying session. Prefers Bearer auth via TMDB_BEARER.
    Falls back to API key (?api_key=) if present in env or constructor.
    """

    def __init__(self, api_key: Optional[str] = None):
        # Read API key at init-time (fallback if bearer not set)
        self.api_key = api_key or os.getenv("TMDB_API_KEY")

    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{_tmdb_base()}{path}"
        query = dict(params or {})
        # If no bearer configured, use legacy api_key
        if "Authorization" not in session.headers:
            if not self.api_key:
                raise RuntimeError("TMDb credentials missing: set TMDB_BEARER or TMDB_API_KEY")
            query["api_key"] = self.api_key
        r = session.get(url, params=query, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return r.json()

    # ---------- Normalizers
    @staticmethod
    def normalize_movie(raw: Dict[str, Any]) -> TMDbMovie:
        rd = raw.get("release_date") or ""
        try:
            year: Optional[int] = int(rd[:4]) if len(rd) >= 4 else None
        except ValueError:
            year = None
        return TMDbMovie(
            id=raw["id"],
            title=raw.get("title") or raw.get("name") or "Untitled",
            year=year,
            overview=raw.get("overview"),
            poster_path=raw.get("poster_path"),
        )

    @staticmethod
    def normalize_details(raw: Dict[str, Any]) -> Tuple[TMDbMovie, List[TMDbCast]]:
        movie = TMDbClient.normalize_movie(raw)
        cast_raw = (raw.get("credits") or {}).get("cast") or []
        cast = [
            TMDbCast(
                id=c["id"],
                name=c.get("name") or "",
                character=c.get("character"),
                profile_path=c.get("profile_path"),
            )
            for c in cast_raw
        ]
        return movie, cast

    # ---------- Read APIs (cached)
    @cached("tmdb_search", ttl=600)  # 10m; key varies by args (q, page, language)
    def search_movies(self, q: str, page: int = 1, *, language: str = DEFAULT_LANGUAGE) -> Dict[str, Any]:
        return self._get(
            "/search/movie",
            {"query": q, "page": page, "include_adult": False, "language": language},
        )

    @cached("tmdb_trending", ttl=600)  # 10m
    def trending_movies(self, window: str = "day", page: int = 1, *, language: str = DEFAULT_LANGUAGE) -> Dict[str, Any]:
        return self._get(f"/trending/movie/{window}", {"page": page, "language": language})

    @cached("tmdb_popular", ttl=900)  # 15m
    def popular_movies(self, page: int = 1, *, language: str = DEFAULT_LANGUAGE) -> Dict[str, Any]:
        return self._get("/movie/popular", {"page": page, "language": language})

    @cached("tmdb_recommend", ttl=1800)  # 30m
    def movie_recommendations(self, movie_id: int, page: int = 1, *, language: str = DEFAULT_LANGUAGE) -> Dict[str, Any]:
        return self._get(f"/movie/{movie_id}/recommendations", {"page": page, "language": language})

    @cached("tmdb_similar", ttl=1800)  # 30m
    def movie_similar(self, movie_id: int, page: int = 1, *, language: str = DEFAULT_LANGUAGE) -> Dict[str, Any]:
        return self._get(f"/movie/{movie_id}/similar", {"page": page, "language": language})

    @cached("tmdb_providers", ttl=21600)  # 6h (B2 spec)
    def movie_watch_providers(self, movie_id: int) -> Dict[str, Any]:
        # Providers API is region-agnostic at fetch; region is applied in normalization layer
        return self._get(f"/movie/{movie_id}/watch/providers", {})

    @cached("tmdb_discover", ttl=900)  # 15m (B2 spec)
    def discover_movies(
        self,
        *,
        with_genres: str,
        page: int = 1,
        region: Optional[str] = None,
        language: str = DEFAULT_LANGUAGE,
        watch_region: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "with_genres": with_genres,
            "sort_by": "popularity.desc",
            "include_adult": False,
            "page": page,
            "language": language,
        }
        # Region signals for TMDb recommendability & availability
        if region:
            params["region"] = region
        if watch_region:
            params["watch_region"] = watch_region
        return self._get("/discover/movie", params)

    @cached("tmdb_details", ttl=3600)  # 1h (B2 spec)
    def movie_details(self, movie_id: int, *, language: str = DEFAULT_LANGUAGE) -> Dict[str, Any]:
        # Append credits to avoid multiple roundtrips
        return self._get(f"/movie/{movie_id}", {"append_to_response": "credits", "language": language})
