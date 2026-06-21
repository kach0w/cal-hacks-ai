"""Generic Socrata (SODA) client for city open-data portals (Chicago, SF, NYC, ...)."""
from __future__ import annotations

import httpx

from safestreets.config import get_settings


async def query(
    domain: str, dataset_id: str, where: str, limit: int = 1000, offset: int = 0
) -> list[dict]:
    url = f"https://{domain}/resource/{dataset_id}.json"
    headers = {}
    token = get_settings().socrata_app_token
    if token:
        headers["X-App-Token"] = token
    params = {"$where": where, "$limit": limit, "$offset": offset}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def query_all(
    domain: str, dataset_id: str, where: str, page: int = 5000, hard_cap: int = 50000
) -> list[dict]:
    """Paginate through every matching row (no artificial cap).

    hard_cap is only a runaway guard; for an intersection bounding box the real
    count is in the hundreds, so this returns everything.
    """
    rows: list[dict] = []
    offset = 0
    while offset < hard_cap:
        batch = await query(domain, dataset_id, where, limit=page, offset=offset)
        rows.extend(batch)
        if len(batch) < page:
            break
        offset += page
    return rows
