from __future__ import annotations
from typing import Dict, Any, List

# TMDb genre IDs
GENRE = {
    "Action": 28, "Adventure": 12, "Animation": 16, "Comedy": 35, "Crime": 80,
    "Documentary": 99, "Drama": 18, "Family": 10751, "Fantasy": 14, "History": 36,
    "Horror": 27, "Music": 10402, "Mystery": 9648, "Romance": 10749, "Sci-Fi": 878,
    "TV": 10770, "Thriller": 53, "War": 10752, "Western": 37,
}

# === Canonical moods (ONLY these 10) =========================================
# Happy, Family, Comedy, Action, Adventure, Drama, Thriller, Horror, Sci-Fi, Animated
RULES: Dict[str, Dict[str, Any]] = {
    "happy":     {"boostGenres": [GENRE["Comedy"], GENRE["Family"], GENRE["Romance"]], "suppressGenres": [GENRE["Horror"]]},
    "family":    {"boostGenres": [GENRE["Family"], GENRE["Animation"], GENRE["Comedy"]]},
    "comedy":    {"boostGenres": [GENRE["Comedy"]]},
    "action":    {"boostGenres": [GENRE["Action"], GENRE["Thriller"]]},
    "adventure": {"boostGenres": [GENRE["Adventure"], GENRE["Fantasy"], GENRE["Action"]]},
    "drama":     {"boostGenres": [GENRE["Drama"]]},
    "thriller":  {"boostGenres": [GENRE["Thriller"], GENRE["Mystery"]]},
    "horror":    {"boostGenres": [GENRE["Horror"], GENRE["Thriller"]]},
    "sci-fi":    {"boostGenres": [GENRE["Sci-Fi"], GENRE["Adventure"], GENRE["Action"]]},
    "animated":  {"boostGenres": [GENRE["Animation"], GENRE["Family"]]},
}

# Common aliases → canonical keys
ALIASES: Dict[str, str] = {
    "sci fi": "sci-fi",
    "scifi": "sci-fi",
    "animation": "animated",
    "kids": "family",
    "funny": "comedy",
    "exciting": "action",
    "spooky": "horror",
    # Allow exact canonical pass-through
    **{k: k for k in RULES.keys()},
}

def supported_moods() -> List[str]:
    # Return in a pleasant, consistent order for hints/UI
    return ["happy","family","comedy","action","adventure","drama","thriller","horror","sci-fi","animated"]

def map_mood(mood: str | None) -> Dict[str, Any]:
    m = (mood or "").strip().lower()
    if not m:
        raise KeyError("missing")
    canon = ALIASES.get(m, m)
    rule = RULES.get(canon)
    if not rule:
        raise KeyError(canon)
    return {"__canon__": canon, **rule}
