from __future__ import annotations
from typing import Any, Dict, List
from ..clients.tmdb import TMDbClient

# Choose a sane default region (overridable via env)
import os
DEFAULT_REGION = os.getenv("DEFAULT_REGION", "US")

def get_watch_providers_service(movie_id: int, region: str | None = None) -> Dict[str, Any]:
    region = (region or DEFAULT_REGION).upper()
    client = TMDbClient()
    payload = client.movie_watch_providers(movie_id)
    results = payload.get("results", {}) or {}
    region_block = results.get(region) or {}

    # Normalize into groups
    def _norm(lst: List[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
        lst = lst or []
        # keep only id, name, logo_path (avoid extra noise)
        out = []
        for p in lst:
            out.append({
                "provider_id": p.get("provider_id"),
                "provider_name": p.get("provider_name"),
                "logo_path": p.get("logo_path"),
            })
        return out

    return {
        "region": region,
        "link": region_block.get("link"),
        "flatrate": _norm(region_block.get("flatrate")),
        "rent": _norm(region_block.get("rent")),
        "buy": _norm(region_block.get("buy")),
        "ads": _norm(region_block.get("ads")),
        "free": _norm(region_block.get("free")),
    }
