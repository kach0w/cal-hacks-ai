"""News agent: Browserbase scrape of local news for crash articles by location + date.
Witness accounts and physical scene descriptions that official databases miss."""
from __future__ import annotations

from typing import Any


async def fetch_news(lat: float, lng: float, city: str | None) -> list[dict[str, Any]]:
    """TODO: Browserbase (or Stagehand sidecar) extract() crash-related articles near
    the intersection in the last ~2 years. Return [{title, date, url, excerpt}]."""
    raise NotImplementedError("Scrape local news via Browserbase for the demo city.")
