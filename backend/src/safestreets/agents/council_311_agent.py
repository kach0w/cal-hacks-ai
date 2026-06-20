"""Council/311 agent: Browserbase scrape of council minutes (PDF) + 311 portals without
APIs. Council mentions also feed the accountability log."""
from __future__ import annotations

from typing import Any


async def fetch_council_and_311(lat: float, lng: float, city: str | None) -> dict[str, Any]:
    """TODO: returns {"complaints_311": [...], "council": [...]}.
    Council items should carry dates so accountability can compute 'no action since'."""
    raise NotImplementedError("Scrape council minutes + 311 portal via Browserbase.")
