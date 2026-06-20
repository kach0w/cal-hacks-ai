"""Browserbase session helper for the scraping agents.

Note: Stagehand is TypeScript-first. This wrapper uses the Browserbase Python SDK; if
you want Stagehand's extract()/act() specifically, run a small Node sidecar and call it
from the agents (the agent interfaces don't change either way).
"""
from __future__ import annotations

from functools import lru_cache

from safestreets.config import get_settings


@lru_cache
def get_browserbase():
    from browserbase import Browserbase  # imported lazily so the app boots without it

    s = get_settings()
    return Browserbase(api_key=s.browserbase_api_key)


async def new_session():
    """TODO: create and return a Browserbase session / connect URL for the agent."""
    raise NotImplementedError("Create a Browserbase session for the scraping agent.")
