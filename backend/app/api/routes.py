# backend/app/api/routes.py
from __future__ import annotations
import os
import json
import re
import traceback
import time
import math
import random
import collections
from uuid import uuid4
from typing import Optional, Dict, Any, List, Tuple

from flask import Blueprint, request, jsonify

from ..clients.tmdb import session, tmdb_url
from ..core.cache import ttl_cache
from ..core.errors import err
from ..services.providers_service import normalize_providers, validate_region
from ..services.mood_service import map_mood, supported_moods
from ..clients.llama import LlamaClient


bp = Blueprint("api", __name__)
mood_bp = Blueprint("mood", __name__)

LANG_DEFAULT = os.getenv("DEFAULT_LANGUAGE", "en-US")
REGION_DEFAULT = os.getenv("DEFAULT_REGION", "US")


# =============================================================================
# PATCHED HELPERS (place above /mood/analyze)
# =============================================================================

@ttl_cache(ttl_seconds=6 * 3600)
def _tmdb_genres_map() -> Dict[int, str]:
    """
    Return {genre_id: name}. Never return a Response/None.
    """
    try:
        r = session.get(tmdb_url("/genre/movie/list"), params={"language": LANG_DEFAULT}, timeout=10)
        if getattr(r, "ok", False):
            data = r.json() or {}
            out: Dict[int, str] = {}
            for g in (data.get("genres") or []):
                if isinstance(g, dict) and isinstance(g.get("id"), int) and isinstance(g.get("name"), str):
                    out[g["id"]] = g["name"]
            return out
    except Exception as e:
        print(f"[_tmdb_genres_map] EXCEPTION: {e}")
    return {}

def _best_search_match(results, want_year=None):
    if not results:
        return None
    filtered = [r for r in results if r.get("poster_path")]
    if not filtered:
        return None
    def score(s):
        base = float(s.get("popularity") or 0.0)
        bonus = 0.0
        if want_year and (s.get("release_date") or "")[:4] == str(want_year):
            bonus += 50.0
        return base + bonus
    return sorted(filtered, key=score, reverse=True)[0]

def _tmdb_search_movie_single(title: str, year: Optional[int] = None, *, language: str = LANG_DEFAULT) -> Optional[Dict[str, Any]]:
    """
    Return a SINGLE movie dict with poster_path, or None. Never returns requests.Response or a list.
    """
    try:
        params = {"query": title, "include_adult": "false", "language": language}
        if year:
            params["year"] = year
        r = session.get(tmdb_url("/search/movie"), params=params, timeout=10)
        if not getattr(r, "ok", False):
            return None
        data = r.json() or {}
        results = data.get("results") or []
        best = _best_search_match(results, want_year=year)
        return best if isinstance(best, dict) else None
    except Exception as e:
        print(f"[_tmdb_search_movie_single] EXCEPTION for {title!r}: {e}")
        return None

def _tmdb_search_movie_strict(title: str, year: Optional[int] = None, *, language: str = LANG_DEFAULT) -> Optional[Dict[str, Any]]:
    """
    STRICT single-movie search that returns a dict movie (with poster) or None.
    Never returns requests.Response or a list.
    """
    try:
        params = {"query": title, "include_adult": "false", "language": language}
        if year:
            params["year"] = year
        r = session.get(tmdb_url("/search/movie"), params=params, timeout=10)
        if not getattr(r, "ok", False):
            return None
        data = r.json() or {}
        results = (data.get("results") or [])
        best = _best_search_match(results, want_year=year)
        if isinstance(best, dict) and best.get("poster_path"):
            return best
        return None
    except Exception as e:
        print(f"[_tmdb_search_movie_strict] EXCEPTION for {title!r}: {e}")
        return None

@ttl_cache(ttl_seconds=3600, vary=["mid", "language"])
def _tmdb_movie_details(mid: int, language: str = LANG_DEFAULT) -> Dict[str, Any]:
    """
    Cached /movie/{id} details; {} on failure.
    """
    try:
        r = session.get(tmdb_url(f"/movie/{mid}"), params={"language": language}, timeout=10)
        if getattr(r, "ok", False):
            return r.json() or {}
    except Exception as e:
        print(f"[_tmdb_movie_details] EXCEPTION mid={mid}: {e}")
    return {}

def enrich_genres_if_missing(m: Dict[str, Any], language: str = LANG_DEFAULT) -> Dict[str, Any]:
    """
    If genre_ids missing/empty, fetch details once and backfill ids from 'genres'.
    Returns the same dict (mutated) for convenience.
    """
    try:
        gids = m.get("genre_ids") or []
        if gids:
            return m
        mid = m.get("id")
        if not isinstance(mid, int):
            return m
        d = _tmdb_movie_details(mid, language=language)
        if d:
            ids = [g.get("id") for g in (d.get("genres") or []) if isinstance(g, dict) and isinstance(g.get("id"), int)]
            if ids:
                m["genre_ids"] = ids
    except Exception as e:
        print(f"[enrich_genres_if_missing] EXCEPTION id={m.get('id')}: {e}")
    return m

def to_movie_obj(tmdb_movie: Dict[str, Any]) -> Dict[str, Any]:
    gmap = _tmdb_genres_map()
    if not isinstance(gmap, dict):
        gmap = {}
    year_str = (tmdb_movie.get("release_date") or "")[:4]
    year = int(year_str) if year_str.isdigit() else None
    return {
        "id": tmdb_movie.get("id"),
        "title": tmdb_movie.get("title") or tmdb_movie.get("name"),
        "poster_path": tmdb_movie.get("poster_path"),
        "overview": tmdb_movie.get("overview"),
        "genres": [gmap.get(gid) for gid in (tmdb_movie.get("genre_ids") or []) if gmap.get(gid)],
        "release_date": tmdb_movie.get("release_date"),
        "year": year,
    }

def _find_json_blob(t: str) -> Optional[str]:
    """
    Extract a JSON object/array from arbitrary model text. Tolerates common invalid escapes like \\'.
    """
    if not t:
        return None
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t).strip()
    s = t.lstrip()
    openers = {"{": "}", "[": "]"}
    idxs = [i for i, ch in enumerate(t) if ch in openers]
    for start in ([0] if (s.startswith("{") or s.startswith("[")) else []) + idxs:
        opener = t[start]; closer = openers.get(opener)
        if closer is None:
            continue
        depth, i = 0, start
        while i < len(t):
            ch = t[i]
            if ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    candidate = t[start:i+1]
                    try:
                        json.loads(candidate)
                        return candidate
                    except Exception:
                        try:
                            sanitized = re.sub(r"\\'", "'", candidate)
                            json.loads(sanitized)
                            return sanitized
                        except Exception:
                            break
            i += 1
    return None

def parse_llm_movies(raw_text: str):
    """
    JSON accepted:
      {"reply":"...","picks":[{"title":"...", "year":1999, "reason":"..."}]}
      {"reply":"...","movies":[{"title":"..."}]}
      [{"title":"..."}]   # top-level array, no reply
    Also supports noisy outputs with preface/suffix (via _find_json_blob),
    then falls back to parsing bullet lines.
    """
    t = (raw_text or "").strip()
    blob = _find_json_blob(t)
    if blob:
        try:
            sanitized = re.sub(r"\\'", "'", blob)
            data = json.loads(sanitized)
            reply = ""
            picks = []

            if isinstance(data, dict):
                reply = (data.get("reply") or "").strip()
                picks = data.get("picks") or data.get("movies") or []
            elif isinstance(data, list):
                picks = data
            out = []
            for p in picks:
                if not isinstance(p, dict):
                    continue
                title = (p.get("title") or "").strip()
                if not title:
                    continue
                year = p.get("year")
                if isinstance(year, str) and year.isdigit():
                    year = int(year)
                out.append({"title": title, "year": year, "reason": p.get("reason")})
            if out:
                return reply, out
        except Exception:
            pass
    # Bullet-list fallback
    lines = [l.strip() for l in t.splitlines() if l.strip()]
    out = []
    for l in lines:
        m = re.search(
            r"^(?:\d+[\).\s-]+)?(?P<title>.+?)(?:\s*\((?P<year>\d{4})\))?(?:\s*[-–—:].*)?$",
            l
        )
        if not m:
            continue
        title = (m.group("title") or "").strip()
        if not title:
            continue
        year = m.group("year")
        year = int(year) if year and year.isdigit() else None
        out.append({"title": title, "year": year, "reason": None})
    return "", out

def safe_to_movie_obj(x):
    if not isinstance(x, dict):
        return None
    try:
        return to_movie_obj(x)
    except Exception as e:
        print(f"[safe_to_movie_obj] drop invalid item type={type(x).__name__}: {e}")
        return None

def is_plausible_title(title: str) -> bool:
    if not title or len(title) > 80:
        return False
    t = title.strip()
    bad_substrings = ("placeholder", "not a real movie", "example", "e.g.", "for instance")
    if any(b in t.lower() for b in bad_substrings):
        return False
    if not re.match(r"^[\w\s\-\':&.,!/?()]+$", t):
        return False
    if not re.search(r"[A-Za-z]", t):
        return False
    return True

def _extract_llm_text(llm_raw) -> str:
    if isinstance(llm_raw, dict):
        v = llm_raw.get("content")
        if isinstance(v, str): return v
        if isinstance(v, list) and v and isinstance(v[0], dict):
            txt = "".join([b.get("text","") for b in v if isinstance(b, dict) and b.get("type") in (None,"text")])
            if txt.strip(): return txt
        choices = llm_raw.get("choices")
        if isinstance(choices, list) and choices:
            c0 = choices[0] or {}
            msg = c0.get("message")
            if isinstance(msg, dict) and isinstance(msg.get("content"), str):
                return msg["content"]
            t = c0.get("text")
            if isinstance(t, str): return t
            cc = c0.get("content")
            if isinstance(cc, str): return cc
        for k in ("output", "result", "text"):
            vv = llm_raw.get(k)
            if isinstance(vv, str) and vv.strip():
                return vv
    return str(llm_raw or "")

# =========================
# Discover helpers & utils
# =========================
def _as_bool(v, default=False):
    if isinstance(v, bool):
        return v
    if v is None:
        return default
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "y", "on"):
        return True
    if s in ("0", "false", "no", "n", "off"):
        return False
    return default

def _csv(s: Optional[str]) -> list[str]:
    if not s:
        return []
    return [p.strip() for p in str(s).split(",") if p.strip()]

def _int_or_none(v, lo=None, hi=None):
    try:
        x = int(str(v).strip())
        if lo is not None and x < lo: x = lo
        if hi is not None and x > hi: x = hi
        return x
    except Exception:
        return None

def _float_or_none(v, lo=None, hi=None):
    try:
        x = float(str(v).strip())
        if lo is not None and x < lo: x = lo
        if hi is not None and x > hi: x = hi
        return x
    except Exception:
        return None

def _genres_to_ids(genres_csv: Optional[str]) -> list[int]:
    """
    Accepts CSV of ids or names. Maps names -> ids using TMDB genre map.
    """
    raw = _csv(genres_csv)
    if not raw:
        return []
    gmap = _tmdb_genres_map() if "_tmdb_genres_map" in globals() else _genre_map()
    inv = { (name or "").strip().lower(): gid for gid, name in (gmap or {}).items() }
    out: list[int] = []
    for token in raw:
        if token.isdigit():
            out.append(int(token))
        else:
            gid = inv.get(token.lower())
            if isinstance(gid, int):
                out.append(gid)
    # de-dupe
    out2 = []
    seen = set()
    for gid in out:
        if gid not in seen:
            seen.add(gid); out2.append(gid)
    return out2

_DISCOVER_SORT_OK = {
    "popularity.desc",
    "vote_average.desc",
    "primary_release_date.desc",
    "revenue.desc",
    "original_title.asc",
}

def _clamp_page(v) -> int:
    x = _int_or_none(v, lo=1, hi=500)
    return x or 1

# =============================================================================
# Variety / Serendipity helpers (LRU, similar/recs)
# =============================================================================

# Keep the last ~200 ids we served (per-process memory)
_RECENT_IDS: "collections.deque[Tuple[int, float]]" = collections.deque(maxlen=200)

def _recent_seen(mid: int, window_sec: int = 6 * 3600) -> bool:
    """Return True if movie id was served in the last window."""
    now = time.time()
    # Prune old items opportunistically
    while _RECENT_IDS and (now - _RECENT_IDS[0][1]) > window_sec:
        _RECENT_IDS.popleft()
    return any(m == mid and (now - ts) <= window_sec for (m, ts) in _RECENT_IDS)

def _recent_mark(mids: List[int]) -> None:
    ts = time.time()
    for mid in mids:
        _RECENT_IDS.append((mid, ts))

def _fetch_similar_pool(seed_mid: int, *, language: str) -> List[Dict[str, Any]]:
    """
    Pull a small pool from /recommendations then /similar for a given seed movie.
    Returns a list of result dicts (TMDB shape) filtered to those with poster_path.
    """
    out: List[Dict[str, Any]] = []

    # Try recommendations first
    rec = session.get(tmdb_url(f"/movie/{seed_mid}/recommendations"),
                      params={"page": 1, "language": language}, timeout=10)
    if getattr(rec, "ok", False):
        items = (rec.json() or {}).get("results") or []
        out.extend([i for i in items if i.get("poster_path")])

    # Fallback/augment with similar
    if len(out) < 12:
        sim = session.get(tmdb_url(f"/movie/{seed_mid}/similar"),
                          params={"page": 1, "language": language}, timeout=10)
        if getattr(sim, "ok", False):
            items = (sim.json() or {}).get("results") or []
            out.extend([i for i in items if i.get("poster_path")])

    return out[:20]  # cap the pool


# =============================================================================
# Domain / Topic helpers (Music profile; extendable)
# =============================================================================

_MUSIC_GENRE_ID = 10402  # TMDB "Music"

def _detect_music_profile(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    keys = ("hip hop", "hip-hop", "rapper", "rap ", " rap", "mixtape", "dj ", "music", "compton", "detroit")
    return any(k in t for k in keys)

def _looks_musicy(item: Dict[str, Any]) -> bool:
    """
    Soft filter: keep if TMDB says it's music OR the title/overview "smells" like music/hip-hop.
    """
    try:
        # genre gate
        gids = item.get("genre_ids") or []
        if _MUSIC_GENRE_ID in gids:
            return True

        title = (item.get("title") or item.get("name") or "").lower()
        overview = (item.get("overview") or "").lower()
        bag = title + " " + overview
        hints = (
            "hip hop", "hip-hop", "rapper", "rap ", " rap", "mixtape", "dj ", "eminem",
            "n.w.a", "tupac", "2pac", "biggie", "notorious", "compton", "detroit",
            "beats", "studio", "producer", "record label"
        )
        return any(h in bag for h in hints)
    except Exception:
        return False


# =============================================================================
# Health
# =============================================================================

@bp.get("/health")
def health():
    return jsonify({"status": "up"}), 200


# =============================================================================
# Search (quality-filtered: vote_count >= 500, highest-rated first)
# =============================================================================

@bp.get("/search")
@ttl_cache(ttl_seconds=10 * 60, vary=["q", "page", "language"])
def search():
    q = (request.args.get("q") or "").strip()
    if not q:
        return err("bad_request", "Missing 'q' query parameter", hint="Add ?q=term")
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        return err("bad_request", "'page' must be an integer")
    language = request.args.get("language", LANG_DEFAULT)

    # Call TMDB search (page here is only to keep parity with their API;
    # we’ll do an extra client-side sort/filter below).
    r = session.get(
        tmdb_url("/search/movie"),
        params={"query": q, "page": page, "include_adult": "false", "language": language},
        timeout=12,
    )
    if r.status_code >= 500:
        return err("bad_gateway", "TMDb error", dependency="tmdb", status=502)
    if not r.ok:
        return err(
            "bad_gateway",
            f"TMDb request failed ({r.status_code})",
            hint=r.text[:200],
            dependency="tmdb",
            status=502,
        )

    raw = r.json() or {}
    items = (raw.get("results") or [])

    # ---- Quality filter & sort ----
    MIN_VOTES = 500
    REQUIRE_POSTER = True  # flip to False if you want to return items without posters

    filtered = [
        it for it in items
        if (it.get("vote_count") or 0) >= MIN_VOTES and (it.get("id")) and (it.get("title") or it.get("name"))
           and (it.get("poster_path") if REQUIRE_POSTER else True)
    ]

    # Sort by vote_average desc, then popularity desc
    def _score_key(it):
        va = float(it.get("vote_average") or 0.0)
        pop = float(it.get("popularity") or 0.0)
        return (-va, -pop)

    filtered.sort(key=_score_key)

    # Re-shape results for frontend grid
    results = [
        {
            "id": it.get("id"),
            "title": it.get("title") or it.get("name") or "Untitled",
            "year": (it.get("release_date") or "")[:4] or None,
            "poster_path": it.get("poster_path"),
            "overview": it.get("overview"),
        }
        for it in filtered
    ]

    # Recompute counts for the filtered set (based on TMDB's default page size=20)
    # We keep the current 'page' so clients can paginate deterministically if they want to.
    PAGE_SIZE = 20
    total_results = len(results)
    total_pages = math.ceil(total_results / PAGE_SIZE) if total_results else 0

    # Slice to the requested page window (so clients can page through our filtered set)
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    paged_results = results[start:end]

    return jsonify({
        "page": page,
        "total_pages": total_pages,
        "total_results": total_results,
        "results": paged_results,
    })


# =============================================================================
# Discover (filtered search)
# =============================================================================
@bp.get("/discover")
@ttl_cache(ttl_seconds=10 * 60, vary=[
    "language","page","genres","year","year_gte","year_lte","runtime_gte","runtime_lte",
    "vote_avg_gte","vote_count_gte","with_original_language","region","watch_region",
    "with_watch_providers","with_watch_monetization_types","include_adult","sort_by"
])
def discover():
    language = request.args.get("language", LANG_DEFAULT)
    page = _clamp_page(request.args.get("page", 1))

    # Normalize filters
    genre_ids = _genres_to_ids(request.args.get("genres"))
    year = _int_or_none(request.args.get("year"), lo=1870, hi=2100)
    year_gte = _int_or_none(request.args.get("year_gte"), lo=1870, hi=2100)
    year_lte = _int_or_none(request.args.get("year_lte"), lo=1870, hi=2100)
    runtime_gte = _int_or_none(request.args.get("runtime_gte"), lo=0, hi=600)
    runtime_lte = _int_or_none(request.args.get("runtime_lte"), lo=0, hi=600)
    vote_avg_gte = _float_or_none(request.args.get("vote_avg_gte"), lo=0.0, hi=10.0)
    vote_count_gte = _int_or_none(request.args.get("vote_count_gte"), lo=0, hi=1_000_000) or 50
    wol = request.args.get("with_original_language")
    region = request.args.get("region", REGION_DEFAULT)
    watch_region = request.args.get("watch_region", region)
    wwp = _csv(request.args.get("with_watch_providers"))
    wmt = _csv(request.args.get("with_watch_monetization_types"))
    include_adult = _as_bool(request.args.get("include_adult"), default=False)
    sort_by = request.args.get("sort_by", "popularity.desc")
    if sort_by not in _DISCOVER_SORT_OK:
        sort_by = "popularity.desc"

    # Build TMDB params
    params = {
        "language": language,
        "include_adult": "true" if include_adult else "false",
        "page": page,
        "sort_by": sort_by,
        "vote_count.gte": vote_count_gte,
    }

    if genre_ids:
        params["with_genres"] = ",".join(str(g) for g in genre_ids)

    # Year / date handling: prefer exact 'primary_release_year' if provided
    if year:
        params["primary_release_year"] = year
    else:
        # Use a loose date filter if gte/lte present
        if year_gte:
            params["primary_release_date.gte"] = f"{year_gte}-01-01"
        if year_lte:
            params["primary_release_date.lte"] = f"{year_lte}-12-31"

    if runtime_gte is not None:
        params["with_runtime.gte"] = runtime_gte
    if runtime_lte is not None:
        params["with_runtime.lte"] = runtime_lte
    if vote_avg_gte is not None:
        params["vote_average.gte"] = vote_avg_gte
    if wol:
        params["with_original_language"] = wol

    # Watch-region/provider filters
    if watch_region:
        params["watch_region"] = watch_region
        params["region"] = watch_region
    if wwp:
        params["with_watch_providers"] = ",".join(wwp)
    if wmt:
        params["with_watch_monetization_types"] = ",".join(wmt)

    r = session.get(tmdb_url("/discover/movie"), params=params, timeout=12)
    if r.status_code >= 500:
        return err("bad_gateway", "TMDb error", dependency="tmdb", status=502)
    if not r.ok:
        return err("bad_gateway", f"TMDb request failed ({r.status_code})", hint=r.text[:240], dependency="tmdb", status=502)

    data = r.json() or {}
    items = (data.get("results") or [])
    # Keep items with posters; shape for frontend reuse
    results = [
        {
            "id": i.get("id"),
            "title": i.get("title") or i.get("name") or "Untitled",
            "year": (i.get("release_date") or "")[:4] or None,
            "poster_path": i.get("poster_path"),
            "overview": i.get("overview"),
            "genre_ids": i.get("genre_ids") or [],
            "release_date": i.get("release_date")
        }
        for i in items
        if i.get("poster_path") and i.get("id")
    ]

    return jsonify({
        "page": data.get("page", page),
        "total_pages": data.get("total_pages", 0),
        "total_results": data.get("total_results", len(results)),
        "results": results,
        "params_used": params  # handy for debugging; strip later if you like
    })

# =============================================================================
# Details
# =============================================================================

@bp.get("/details/<int:mid>")
@ttl_cache(ttl_seconds=3600, vary=["mid", "language"])
def details(mid: int):
    language = request.args.get("language", LANG_DEFAULT)
    r = session.get(tmdb_url(f"/movie/{mid}"), params={"language": language})
    if r.status_code >= 500:
        return err("bad_gateway", "TMDb error", dependency="tmdb", status=502)
    if r.status_code == 404:
        return err("not_found", "Movie not found", hint="Check the id", status=404)
    if not r.ok:
        return err("bad_gateway", "TMDb request failed", dependency="tmdb", status=502)

    data = r.json() or {}
    movie = {
        "id": data.get("id"),
        "title": data.get("title"),
        "year": (data.get("release_date") or "")[:4] or None,
        "release_date": data.get("release_date"),
        "runtime": data.get("runtime"),
        "vote_average": data.get("vote_average"),
        "genres": data.get("genres") or [],
        "poster_path": data.get("poster_path"),
        "backdrop_path": data.get("backdrop_path"),
        "spoken_languages": data.get("spoken_languages") or [],
        "production_countries": data.get("production_countries") or [],
        "overview": data.get("overview"),
    }

    cr = session.get(tmdb_url(f"/movie/{mid}/credits"), params={"language": language})
    cast = []
    if r.ok and cr.ok:
        cast = [
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "character": c.get("character"),
                "profile_path": c.get("profile_path"),
            }
            for c in (cr.json().get("cast") or [])[:12]
        ]

    return jsonify({"movie": movie, "cast": cast})


# =============================================================================
# Recommendations by seed movie
# =============================================================================

@bp.get("/recommend/<int:mid>")
@ttl_cache(ttl_seconds=30 * 60, vary=["mid", "page", "language"])
def recommend(mid: int):
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        return err("bad_request", "'page' must be an integer")
    language = request.args.get("language", LANG_DEFAULT)

    rec = session.get(
        tmdb_url(f"/movie/{mid}/recommendations"),
        params={"page": page, "language": language},
    )
    src = "recommendations"
    if not rec.ok or (rec.json() or {}).get("total_results", 0) == 0:
        rec = session.get(
            tmdb_url(f"/movie/{mid}/similar"),
            params={"page": page, "language": language},
        )
        src = "similar"

    if rec.status_code >= 500:
        return err("bad_gateway", "TMDb error", dependency="tmdb", status=502)
    if not rec.ok:
        return err(
            "bad_gateway",
            f"TMDb request failed ({rec.status_code})",
            hint=rec.text[:200],
            dependency="tmdb",
            status=502,
        )

    data = rec.json() or {}
    items = data.get("results") or []
    results = [
        {
            "id": i.get("id"),
            "title": i.get("title") or i.get("name") or "Untitled",
            "year": (i.get("release_date") or "")[:4] or None,
            "poster_path": i.get("poster_path"),
        }
        for i in items
        if i.get("poster_path")
    ]

    return jsonify(
        {
            "source": src,
            "page": data.get("page", page),
            "total_pages": data.get("total_pages", 0),
            "total_results": data.get("total_results", len(results)),
            "results": results,
        }
    )

# =============================================================================
# Trending & Popular
# =============================================================================

@bp.get("/trending")
@ttl_cache(ttl_seconds=10 * 60, vary=["window", "page", "language"])
def trending():
    window = (request.args.get("window") or "day").lower()
    if window not in ("day", "week"):
        return err("bad_request", "window must be 'day' or 'week'", hint="Use ?window=day or ?window=week"), 400

    page = request.args.get("page", "1")
    language = request.args.get("language", LANG_DEFAULT)

    r = session.get(
        tmdb_url(f"/trending/movie/{window}"),
        params={"page": page, "language": language},
        timeout=10,
    )
    if r.status_code >= 500:
        return err("bad_gateway", "TMDb error", dependency="tmdb", status=502)
    if not r.ok:
        return err("bad_gateway", f"TMDb request failed ({r.status_code})",
                   hint=r.text[:200], dependency="tmdb", status=502)

    data = r.json() or {}
    return jsonify({
        "page": data.get("page"),
        "results": data.get("results") or [],
        "total_pages": data.get("total_pages"),
        "total_results": data.get("total_results"),
    })


@bp.get("/popular")
@ttl_cache(ttl_seconds=10 * 60, vary=["page", "language"])
def popular():
    page = request.args.get("page", "1")
    language = request.args.get("language", LANG_DEFAULT)

    r = session.get(
        tmdb_url("/movie/popular"),
        params={"page": page, "language": language},
        timeout=10,
    )
    if r.status_code >= 500:
        return err("bad_gateway", "TMDb error", dependency="tmdb", status=502)
    if not r.ok:
        return err("bad_gateway", f"TMDb request failed ({r.status_code})",
                   hint=r.text[:200], dependency="tmdb", status=502)

    data = r.json() or {}
    return jsonify({
        "page": data.get("page"),
        "results": data.get("results") or [],
        "total_pages": data.get("total_pages"),
        "total_results": data.get("total_results"),
    })


# =============================================================================
# Providers
# =============================================================================

@bp.get("/providers/<int:mid>")
@ttl_cache(ttl_seconds=6 * 3600, vary=["mid", "region"])
def providers(mid: int):
    try:
        region = validate_region(request.args.get("region"), REGION_DEFAULT)
    except ValueError as e:
        return err(
            "bad_request",
            str(e),
            hint="Try: US, GB, DE, FR, IN, JP, BR, CA, AU, ES, IT, MX, NL, SE",
        )

    r = session.get(tmdb_url(f"/movie/{mid}/watch/providers"))
    if r.status_code >= 500:
        return err("bad_gateway", "TMDb error", dependency="tmdb", status=502)
    if not r.ok:
        return err("bad_gateway", "TMDb request failed", dependency="tmdb", status=502)

    norm = normalize_providers(r.json(), region)
    raw_loc = (r.json() or {}).get("results", {}).get(region) or {}
    link = raw_loc.get("link")
    return jsonify({"id": mid, "region": region, "link": link, **norm})


# =============================================================================
# Mood discover
# =============================================================================

@bp.get("/recommend/mood")
@ttl_cache(ttl_seconds=15 * 60, vary=["mood", "page", "region", "language"])
def recommend_mood():
    mood = request.args.get("mood")
    language = request.args.get("language", LANG_DEFAULT)
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        return err("bad_request", "'page' must be an integer")
    try:
        region = validate_region(request.args.get("region"), REGION_DEFAULT)
        rule = map_mood(mood)   # only the 10 canonical moods
        canon = rule.get("__canon__", mood or "")
    except KeyError:
        return err(
            "bad_request",
            f"Unknown mood: '{mood}'",
            hint="Try: " + ", ".join(supported_moods()),
        )
    except ValueError as e:
        return err("bad_request", str(e), hint="Pass a valid ISO-3166-1 alpha-2 region")

    boost = rule.get("boostGenres", []) or []
    with_genres = ",".join(map(str, boost)) if boost else None
    strategies = []
    p1 = {
        "language": language,
        "include_adult": "false",
        "page": page,
        "sort_by": "popularity.desc",
        "vote_count.gte": 50,
        "region": region,
        "watch_region": region,
    }
    if with_genres:
        p1["with_genres"] = with_genres
    strategies.append(p1)
    p2 = {
        "language": language,
        "include_adult": "false",
        "page": page,
        "sort_by": "popularity.desc",
        "vote_count.gte": 50,
    }
    if with_genres:
        p2["with_genres"] = with_genres
    strategies.append(p2)
    p3 = {
        "language": language,
        "include_adult": "false",
        "page": page,
        "sort_by": "popularity.desc",
    }
    if with_genres:
        p3["with_genres"] = with_genres
    strategies.append(p3)

    data = None
    used_params = None
    for params in strategies:
        r = session.get(tmdb_url("/discover/movie"), params=params)
        if r.status_code >= 500:
            return err("bad_gateway", "TMDb error", dependency="tmdb", status=502)
        if not r.ok:
            continue
        candidate = r.json() or {}
        items = candidate.get("results") or []
        items = [it for it in items if it.get("poster_path")]
        if items:
            data = candidate
            used_params = params
            break
    if data is None:
        r = session.get(tmdb_url("/discover/movie"), params=strategies[0])
        if r.status_code >= 500:
            return err("bad_gateway", "TMDb error", dependency="tmdb", status=502)
        if not r.ok:
            return err(
                "bad_gateway",
                f"TMDb request failed ({r.status_code})",
                hint=r.text[:200],
                dependency="tmdb",
                status=502,
            )
        data = r.json() or {}

    raw = data.get("results") or []
    results = [
        {
            "id": it.get("id"),
            "title": it.get("title") or it.get("name") or "Untitled",
            "year": (it.get("release_date") or "")[:4] or None,
            "poster_path": it.get("poster_path"),
            "genre_ids": it.get("genre_ids") or [],
        }
        for it in raw
        if it.get("poster_path")
    ]

    return jsonify({
        "mood": canon,
        "region": region,
        "page": data.get("page", page),
        "total_pages": data.get("total_pages", 0),
        "total_results": data.get("total_results", len(results)),
        "results": results,
        # "debug_used_params": used_params,  # optional for dev
    })


# =============================================================================
# Mood analyze (LLM → TMDB enrichment + variety + domain filtering)
# =============================================================================

@bp.route("/mood/analyze", methods=["POST"])
def analyze_mood():
    trace_id = str(uuid4())[:8]
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    language = data.get("language", LANG_DEFAULT)
    if not text:
        return err(
            "bad_request",
            "Text is required for mood analysis",
            hint="Provide a 'text' field with your input",
            status=400
        )
    llama_client = LlamaClient()
    system_prompt = (
        "You are a movie recommendation assistant. Reply ONLY with JSON, no preface:\n"
        '{\n'
        '  "reply": "one-sentence friendly summary",\n'
        '  "picks": [ {"title": "Movie", "year": 2016, "reason": "why"} ]\n'
        '}\n'
        'If you must choose a different key, use "movies" instead of "picks". '
        "No markdown fences, no extra text. 5–10 films (not TV)."
    )
    try:
        # 1) Call LLM and normalize content
        llm_raw = llama_client.analyze_mood_with_system_prompt(system_prompt, text)
        if isinstance(llm_raw, dict):
            try:
                print(f"[mood.analyze][trace={trace_id}] llm_raw_shape=dict keys={list(llm_raw.keys())[:6]}")
            except Exception:
                pass
        llm_text = _extract_llm_text(llm_raw)
        print(f"[mood.analyze][trace={trace_id}] llm_text[0:300]={llm_text[:300]!r}")
        # 2) Parse candidates
        reply, candidates = parse_llm_movies(llm_text)
        if not candidates:
            # If LLM gave nothing useful, we continue (domain fallback later will still try to fill)
            candidates = []
        # ---- 3) Enrich with TMDB; require poster; dedupe; add serendipity + domain filter ----
        want_music = _detect_music_profile(text)
        base_matches: List[Dict[str, Any]] = []
        seen_ids = set()
        # 3a) Exact title matches (up to ~6)
        for c in candidates:
            title = (c.get("title") or "").strip()
            if not title or not is_plausible_title(title):
                continue
            m = _tmdb_search_movie_single(title, c.get("year"), language=language)
            if not isinstance(m, dict):
                continue
            mid = m.get("id"); poster = m.get("poster_path")
            if not mid or not poster:
                continue
            # optional: backfill genres for better domain checks
            if want_music and not (m.get("genre_ids") or []):
                m = enrich_genres_if_missing(m, language=language)
            if want_music and not _looks_musicy(m):
                continue
            if mid in seen_ids:
                continue
            seen_ids.add(mid)
            base_matches.append(m)
            if len(base_matches) >= 6:
                break

        # 3b) Expand with recommendations/similar from a few seeds
        pool: List[Dict[str, Any]] = list(base_matches)
        for seed in base_matches[:3]:  # expand around up to 3 seeds
            sid = seed.get("id")
            if not sid:
                continue
            try:
                recs = _fetch_similar_pool(sid, language=language)
                for r in recs:
                    rid = r.get("id")
                    if not rid or not r.get("poster_path"):
                        continue
                    # domain filter early to keep pool clean
                    if want_music and not _looks_musicy(r):
                        continue
                    if rid in seen_ids:
                        continue
                    seen_ids.add(rid)
                    pool.append(r)
            except Exception:
                pass

        # 3c) Filter out things we served very recently; keep reserve if emptying
        def _id_of(x):
            try:
                return int(x.get("id"))
            except Exception:
                return None
        fresh_pool = [p for p in pool if (_id_of(p) is not None and not _recent_seen(_id_of(p)))]
        if len(fresh_pool) < 10:
            fresh_pool = pool  # fallback if filtering was too strict

        # 3d) Shuffle per-request for variety
        rng = random.Random(time.time_ns())
        rng.shuffle(fresh_pool)

        # 3e) Keep the first 10, convert to frontend shape, final de-dup by id
        chosen: List[Dict[str, Any]] = []
        chosen_ids = set()
        for item in fresh_pool:
            obj = safe_to_movie_obj(item)
            if not obj:
                continue
            oid = obj.get("id")
            if not isinstance(oid, int) or oid in chosen_ids:
                continue
            chosen_ids.add(oid)
            chosen.append(obj)
            if len(chosen) >= 10:
                break

        # 3f) Guaranteed fallback if we have too few (Discover tuned for music profile)
        if len(chosen) < 5:
            try:
                discover_params = {
                    "language": language,
                    "include_adult": "false",
                    "sort_by": "popularity.desc",
                    "vote_count.gte": 50,
                    "page": 1,
                }
                if want_music:
                    discover_params["with_genres"] = str(_MUSIC_GENRE_ID)
                r = session.get(tmdb_url("/discover/movie"), params=discover_params, timeout=10)
                if getattr(r, "ok", False):
                    items = (r.json() or {}).get("results") or []
                    # Prefer explicitly musicy items
                    items = [it for it in items if it.get("poster_path")]
                    if want_music:
                        items = [it for it in items if (_MUSIC_GENRE_ID in (it.get("genre_ids") or [])) or _looks_musicy(it)]
                    rng.shuffle(items)
                    for it in items:
                        obj = safe_to_movie_obj(it)
                        if not obj:
                            continue
                        oid = obj.get("id")
                        if not isinstance(oid, int) or oid in chosen_ids:
                            continue
                        chosen_ids.add(oid)
                        chosen.append(obj)
                        if len(chosen) >= 10:
                            break
            except Exception:
                pass

        # 3g) Static, on-topic last resort for music-only case
        if not chosen and want_music:
            static_titles = [
                ("8 Mile", 2002),
                ("Straight Outta Compton", 2015),
                ("All Eyez on Me", 2017),
                ("Notorious", 2009),
                ("Get Rich or Die Tryin'", 2005),
            ]
            for (t, y) in static_titles:
                m = _tmdb_search_movie_strict(t, y, language=language)
                if isinstance(m, dict) and m.get("poster_path"):
                    obj = safe_to_movie_obj(m)
                    if obj and isinstance(obj.get("id"), int) and obj["id"] not in chosen_ids:
                        chosen_ids.add(obj["id"])
                        chosen.append(obj)
                        if len(chosen) >= 5:
                            break
        if not chosen:
            return err(
                "tmdb_no_match",
                "Could not match movie candidates in TMDB",
                hint="Rephrase mood or include a genre/decade",
                dependency="tmdb",
                status=502
            )
        # Remember what we just served to avoid repeats next time
        _recent_mark([m_id for m_id in chosen_ids])
        return jsonify({
            "reply": reply or "Here are some picks that match your vibe.",
            "language": language,
            "movies": chosen
        })
    except Exception as e:
        try:
            print(f"[mood.analyze][trace={trace_id}] EXCEPTION: {e}")
            traceback.print_exc()
        except Exception:
            pass
        fallback_movies = [
            {"id": None, "title": "The Pursuit of Happyness", "poster_path": None, "overview": "A heart-wrenching drama about perseverance.", "genres": ["Drama","Biography"], "release_date": None, "year": None},
            {"id": None, "title": "Crazy, Stupid, Love", "poster_path": None, "overview": "A warm rom-com about relationships.", "genres": ["Comedy","Romance"], "release_date": None, "year": None},
            {"id": None, "title": "Inside Out", "poster_path": None, "overview": "An animated journey through emotions.", "genres": ["Animation","Adventure","Comedy"], "release_date": None, "year": None},
        ]
        return jsonify({
            "code": "fallback",
            "message": "Unexpected error — returning generic suggestions.",
            "hint": "Check Llama/TMDB credentials and logs",
            "dependency": "llama/tmdb",
            "trace_id": trace_id,
            "movies": fallback_movies
        }), 500
