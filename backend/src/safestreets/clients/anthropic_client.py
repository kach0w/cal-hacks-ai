"""Configured Anthropic async client."""
from __future__ import annotations

from functools import lru_cache

from anthropic import AsyncAnthropic

from safestreets.config import get_settings


@lru_cache
def get_anthropic() -> AsyncAnthropic:
    return AsyncAnthropic(api_key=get_settings().anthropic_api_key)
