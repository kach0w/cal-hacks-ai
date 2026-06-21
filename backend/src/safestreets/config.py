"""Central settings, loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env from the repo root regardless of the process CWD. config.py lives at
# backend/src/safestreets/config.py, so the repo root is 3 parents up (and backend/ is 2).
# Without this, running `cd backend && uvicorn ...` would miss the root .env and every
# API key would silently load empty.
_HERE = Path(__file__).resolve()
_ENV_CANDIDATES = (
    str(_HERE.parents[3] / ".env"),   # <repo>/.env
    str(_HERE.parents[2] / ".env"),   # <repo>/backend/.env
    ".env",                            # CWD fallback
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_CANDIDATES, extra="ignore")

    # anthropic
    anthropic_api_key: str = ""
    claude_vision_model: str = "claude-opus-4-8"
    claude_text_model: str = "claude-sonnet-4-6"

    # browserbase
    browserbase_api_key: str = ""
    browserbase_project_id: str = ""

    # google maps
    google_maps_api_key: str = ""

    # socrata
    socrata_app_token: str = ""

    # midjourney (optional)
    midjourney_api_key: str = ""

    # redis
    redis_url: str = "redis://localhost:6379/0"

    # fetch.ai
    orchestrator_seed: str = "safestreets-orchestrator-dev-seed-change-me"

    # demo scope — the one knob that pins data collection to a city. Override via
    # DEMO_CITY in .env to retarget; nothing else hardcodes the city.
    demo_city: str = "Berkeley"

    # app
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_origin: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
