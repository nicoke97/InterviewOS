"""Application settings from environment variables.

Solo mode today (single SQLite database). For multi-user later:
- set DATABASE_URL to Postgres
- add auth using APP_SECRET
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATIC_DIR = ROOT / "frontend" / "dist"


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _env_bool(key: str, default: bool = False) -> bool:
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


ENVIRONMENT = _env("ENVIRONMENT", "development").lower()
IS_PRODUCTION = ENVIRONMENT == "production"

DATA_DIR = Path(_env("DATA_DIR", str(ROOT / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

_default_sqlite = f"sqlite:///{(DATA_DIR / 'progress.db').as_posix()}"
DATABASE_URL = _env("DATABASE_URL", _default_sqlite)

STATIC_DIR = Path(_env("STATIC_DIR", str(DEFAULT_STATIC_DIR)))

_default_origins = "http://localhost:5174,http://127.0.0.1:5174"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in _env("ALLOWED_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

HOST = _env("HOST", "0.0.0.0")
PORT = int(_env("PORT", "8001"))

# Reserved for future JWT/session auth when selling multi-user access.
APP_SECRET = _env("APP_SECRET", "")

_serve_static_default = DEFAULT_STATIC_DIR.joinpath("index.html").is_file()
SERVE_STATIC = _env_bool("SERVE_STATIC", _serve_static_default)


def engine_connect_args() -> dict:
    if DATABASE_URL.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}
