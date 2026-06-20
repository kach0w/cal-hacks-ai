"""NHTSA FARS (fatal crash) API client. Intersection-level precision."""
from __future__ import annotations

import httpx

_BASE = "https://crashviewer.nhtsa.dot.gov/CrashAPI"


async def get_case_list(state: int, from_year: int, to_year: int) -> list[dict]:
    """TODO: filter to the target intersection by lat/lng proximity after fetching."""
    url = f"{_BASE}/crashes/GetCaseList"
    params = {"states": state, "fromYear": from_year, "toYear": to_year, "format": "json"}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json().get("Results", [])
