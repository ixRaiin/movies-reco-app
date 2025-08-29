from flask import Blueprint, jsonify, request
from ..core.errors import ApiError
from ..services.search_service import search_movies_service
from ..services.details_service import get_movie_details_service
from ..services.recommend_service import get_recommendations_service
from ..services.providers_service import get_watch_providers_service
from ..services.mood_service import mood_recommendations_service
from ..services.trending_service import get_trending_service, get_popular_service

bp = Blueprint("api", __name__)

@bp.get("/health")
def health():
    return jsonify({"status": "up"}), 200

@bp.get("/search")
def search():
    q = (request.args.get("q") or "").strip()
    if not q:
        raise ApiError(code="invalid_request", message="Missing 'q' query parameter", hint="Add ?q=term", http_status=400)
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        raise ApiError(code="invalid_request", message="'page' must be an integer", http_status=400)
    try:
        data = search_movies_service(q=q, page=page)
    except RuntimeError as e:
        raise ApiError(code="upstream_config_error", message=str(e), hint="Set TMDB_API_KEY in backend/.env", http_status=500)
    return jsonify(data), 200

@bp.get("/details/<int:movie_id>")
def details(movie_id: int):
    data = get_movie_details_service(movie_id)
    return jsonify(data), 200

@bp.get("/recommend/<int:movie_id>")
def recommend(movie_id: int):
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        raise ApiError(code="invalid_request", message="'page' must be an integer", http_status=400)
    data = get_recommendations_service(movie_id=movie_id, page=page, require_poster=True)
    return jsonify(data), 200

@bp.get("/providers/<int:movie_id>")
def providers(movie_id: int):
    region = request.args.get("region")
    data = get_watch_providers_service(movie_id, region=region)
    return jsonify(data), 200

@bp.get("/recommend/mood")
def recommend_mood():
    mood = (request.args.get("mood") or "").strip()
    if not mood:
        raise ApiError(code="invalid_request", message="Missing 'mood' query parameter", hint="Add ?mood=happy", http_status=400)
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        raise ApiError(code="invalid_request", message="'page' must be an integer", http_status=400)
    region = request.args.get("region")
    data = mood_recommendations_service(mood=mood, page=page, require_poster=True, region=region)
    return jsonify(data), 200

@bp.get("/trending")
def trending():
    window = (request.args.get("window") or "day").lower()
    if window not in ("day", "week"):
        window = "day"
    data = get_trending_service(window=window, limit=10, require_poster=True)
    return jsonify(data), 200

@bp.get("/popular")
def popular():
    data = get_popular_service(limit=20, require_poster=True)
    return jsonify(data), 200


def register_routes(app):
    app.register_blueprint(bp, url_prefix="/")
