import os
from flask import Flask
from dotenv import load_dotenv

REQUIRED = ["TMDB_API_KEY"]

class Settings:
    TMDB_API_KEY: str | None = os.getenv("TMDB_API_KEY")

def load_config(app: Flask) -> None:
    # Load .env first so os.getenv works locally
    load_dotenv()
    missing = [k for k in REQUIRED if not os.getenv(k)]
    if missing:
        app.logger.warning("Missing required env vars: %s", ", ".join(missing))
