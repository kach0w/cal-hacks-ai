"""Central settings, loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

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

    # app
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_origin: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
