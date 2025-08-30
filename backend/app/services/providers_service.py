from __future__ import annotations
from typing import Any, Dict, List
from ..clients.tmdb import TMDbClient
import os

# Choose a sane default region (overridable via env)
DEFAULT_REGION = os.getenv("DEFAULT_REGION", "US")
ALLOWED_REGIONS = {"US","GB","DE","FR","IN","JP","BR","CA","AU","ES","IT","MX","NL","SE"}

def validate_region(region: str | None, default_region: str | None) -> str:
    region = (region or default_region or "US").upper()
    if region not in ALLOWED_REGIONS:
        raise ValueError(f"Invalid region: {region}")
    return region

def normalize_providers(raw: dict, region: str) -> dict:
    """
    Normalize TMDb providers into three groups we show in the modal:
      - stream  (TMDb 'flatrate')
      - rent    (TMDb 'rent')
      - buy     (TMDb 'buy')
    Each item includes: { id, name, logoPath, link }
    `link` points to TMDb's region watch page (TMDb does not provide deep links).
    """
    loc = (raw or {}).get("results", {}).get(region)
    if not loc:
        return {"stream": [], "rent": [], "buy": [], "link": None}

    def pick(items: List[Dict[str, Any]] | None):
        items = items or []
        # Sort by TMDb display_priority then name, and de-dupe by provider_id
        items.sort(key=lambda i: (i.get("display_priority", 9999), i.get("provider_name", "")))
        seen, out = set(), []
        for i in items:
            pid = i.get("provider_id")
            if pid in seen:
                continue
            seen.add(pid)
            out.append({
                "id": pid,
                "name": i.get("provider_name"),
                "logoPath": i.get("logo_path"),
                # TMDb only gives a region-level link; attach it so the chip can open something useful.
                "link": loc.get("link"),
            })
        return out

    return {
        "stream": pick(loc.get("flatrate")),
        "rent": pick(loc.get("rent")),
        "buy": pick(loc.get("buy")),
        "link": loc.get("link"),
    }
