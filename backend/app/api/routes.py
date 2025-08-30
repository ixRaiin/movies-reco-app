# backend/app/api/routes.py
from __future__ import annotations
import os
from flask import Blueprint, request, jsonify
from ..clients.tmdb import session, tmdb_url
from ..core.cache import ttl_cache
from ..core.errors import err
from ..services.providers_service import normalize_providers, validate_region
from ..services.mood_service import map_mood, supported_moods

bp = Blueprint("api", __name__)

LANG_DEFAULT = os.getenv("DEFAULT_LANGUAGE", "en-US")
REGION_DEFAULT = os.getenv("DEFAULT_REGION", "US")

# --- Health -----------------------------------------------------------------

@bp.get("/health")
def health():
    return jsonify({"status": "up"}), 200

# --- Search -----------------------------------------------------------------

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

    r = session.get(
        tmdb_url("/search/movie"),
        params={"query": q, "page": page, "include_adult": "false", "language": language},
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
    # Keep raw shape (frontend can use it directly) or transform if you prefer.
    return jsonify(r.json())

# --- Details ----------------------------------------------------------------

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

    # Best-effort credits
    cr = session.get(tmdb_url(f"/movie/{mid}/credits"), params={"language": language})
    cast = []
    if cr.ok:
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

# --- Recommendations by seed movie ------------------------------------------

@bp.get("/recommend/<int:mid>")
@ttl_cache(ttl_seconds=30 * 60, vary=["mid", "page", "language"])
def recommend(mid: int):
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        return err("bad_request", "'page' must be an integer")
    language = request.args.get("language", LANG_DEFAULT)

    # Try /recommendations then fallback to /similar
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

# --- Providers (ONE definition) ---------------------------------------------

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

# --- Mood discover (ONE definition) -----------------------------------------

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
            return err("bad_gateway", f"TMDb request failed ({r.status_code})",
                       hint=r.text[:200], dependency="tmdb", status=502)
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
        # Optional debug for dev: which pass returned results
        # "debug_used_params": used_params,
    })


# --- Trending & Popular ------------------------------------------------------

@bp.get("/trending")
@ttl_cache(ttl_seconds=10 * 60, vary=["window", "page", "language"])
def trending():
    window = (request.args.get("window") or "day").lower()
    if window not in ("day", "week"):
        window = "day"
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        return err("bad_request", "'page' must be an integer")
    language = request.args.get("language", LANG_DEFAULT)

    r = session.get(
        tmdb_url(f"/trending/movie/{window}"),
        params={"page": page, "language": language},
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
    return jsonify(r.json())

@bp.get("/popular")
@ttl_cache(ttl_seconds=15 * 60, vary=["page", "language"])
def popular():
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        return err("bad_request", "'page' must be an integer")
    language = request.args.get("language", LANG_DEFAULT)

    r = session.get(
        tmdb_url("/movie/popular"),
        params={"page": page, "language": language},
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
    return jsonify(r.json())
