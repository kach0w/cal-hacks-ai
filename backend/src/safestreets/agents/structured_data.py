"""Structured data agent: FARS + city open data. Returns crash records at the precision
the source supports (intersection-level for FARS)."""
from __future__ import annotations

from typing import Any

from safestreets.clients import nhtsa, socrata  # noqa: F401  (socrata used per-city)


async def fetch_crash_data(lat: float, lng: float, city: str | None) -> list[dict[str, Any]]:
    """TODO:
    1. FARS GetCaseList for the state, then filter by proximity to (lat,lng).
    2. If the city has a Socrata portal, query its crash dataset for the intersection.
    3. Normalize to a common shape; KEEP precision honest (no fabricated corner counts).
    """
    raise NotImplementedError("Wire FARS + the demo city's open-data crash dataset.")
